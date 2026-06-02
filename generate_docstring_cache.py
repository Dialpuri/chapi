#!/usr/bin/env python3
"""Generate a C++ source file that pre-fills the nanobind docstring cache.

At runtime ``molecules-container-nanobind.cc`` used to read the Doxygen XML
(``classmolecules__container__t.xml``) and build ``docstring_cache`` on first
use. That means the XML had to be shipped/installed alongside the wheel.

This script parses the same XML at *build time* and emits a ``.cc`` file
defining ``fill_docstring_cache()``, which the nanobind module calls to
populate the cache directly. The XML no longer needs to be shipped.

The parsing logic here is a faithful port of ``get_docstring_from_xml()`` in
``molecules-container-nanobind.cc`` so that the generated docstrings are
identical to what the old runtime path produced.

Run with no arguments (paths are derived relative to this file), or pass
``--xml`` / ``--output`` to override.
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

# This script lives in the chapi repo root; the coot sources are in the
# `coot` submodule below it.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
COOT_API = os.path.join(REPO_ROOT, "coot", "api")
DEFAULT_XML = os.path.join(COOT_API, "doxy-sphinx", "xml",
                           "classmolecules__container__t.xml")
DEFAULT_OUTPUT = os.path.join(COOT_API, "molecules-container-docstrings-cache.cc")


def text_get(elem):
    """Mimic pugixml's ``xml_node::text().get()``.

    Returns the value of the first PCDATA/CDATA child of ``elem``. pugixml does
    not create nodes for whitespace-only PCDATA by default, so we skip
    whitespace-only fragments (but preserve the surrounding whitespace of the
    fragment we do return, matching pugixml).
    """
    if elem is None:
        return ""
    if elem.text is not None and elem.text.strip() != "":
        return elem.text
    for child in elem:
        if child.tail is not None and child.tail.strip() != "":
            return child.tail
    return ""


def convert_type(s_in):
    """Port of the ``convert_type`` lambda (sequential, non-exclusive ifs)."""
    s = s_in
    if s_in == "const std::string &":
        s = "str"
    if s_in == "std::string":
        s = "str"
    if s_in == "void":
        s = "None"
    if s_in == "std::vector<":
        s = "list"
    if s_in == "std::vector< std::pair< double, double > >":
        s = "list"
    if s_in == "std::vector< std::pair< std::string, std::string > >":
        s = "list"
    if "std::vector<" in s_in:
        s = "list"
    if s_in.startswith("std::pair<"):
        s = "tuple"
    return s


class ArgInfo:
    __slots__ = ("name", "type", "description")

    def __init__(self, name, type_):
        self.name = name
        self.type = type_
        self.description = ""


def update_arg_in_args(arg_name, descr, args):
    for arg in args:
        if arg.name == arg_name:
            arg.description = descr


def build_docstring(member):
    """Build the docstring for a single <memberdef>, mirroring the C++ code."""
    oss = []
    args = []

    # briefdescription paras
    brief = member.find("briefdescription")
    if brief is not None:
        for para in brief.findall("para"):
            para_text = text_get(para)
            if para_text:
                oss.append(para_text + "\n")

    type_elem = member.find("type")
    type_string = ""
    if type_elem is not None:
        type_string = convert_type(text_get(type_elem))

    # parameters
    for param in member.findall("param"):
        p_type = param.find("type")
        p_declname = param.find("declname")
        if p_type is not None and p_declname is not None:
            tt = convert_type(text_get(p_type))
            args.append(ArgInfo(text_get(p_declname), tt))

    return_type_docs = ""

    detailed = member.find("detaileddescription")
    if detailed is not None:
        n_para = 0
        for para in detailed.findall("para"):
            n_para += 1
            para_text = text_get(para)
            if para_text:
                if n_para > 1:
                    oss.append("\n    ")
                if para_text[0] == "\n":
                    para_text = para_text[1:]
                oss.append(para_text + "\n")

            for parameterlist in para.findall("parameterlist"):
                for parameteritem in parameterlist.findall("parameteritem"):
                    parameter_name_text = ""
                    for parameternamelist in parameteritem.findall("parameternamelist"):
                        for parametername in parameternamelist.findall("parametername"):
                            parameter_name_text = text_get(parametername)
                    for parameterdescription in parameteritem.findall("parameterdescription"):
                        for d_para in parameterdescription.findall("para"):
                            t = text_get(d_para)
                            if parameter_name_text and t:
                                update_arg_in_args(parameter_name_text, t, args)

            for simplesect in para.findall("simplesect"):
                if simplesect.get("kind") == "return":
                    for ss_para in simplesect.findall("para"):
                        return_type_docs += text_get(ss_para)

        if args:
            oss.append("\n")
            oss.append("    Args:\n")
            for arg in args:
                oss.append("        %s (%s): %s\n" % (arg.name, arg.type, arg.description))

        if type_string:
            oss.append("\n")
            oss.append("    Returns:\n")
            if not return_type_docs:
                oss.append("        %s\n" % type_string)
            else:
                oss.append("        %s: %s\n" % (type_string, return_type_docs))

    return "".join(oss)


def parse_docstrings(xml_path):
    """Return an ordered list of (name, docstring) pairs.

    Order is preserved so that, as in the C++ map assignment, the last entry
    for a duplicated name wins when emitted as a sequence of assignments.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    compounddef = root.find("compounddef")
    results = []
    if compounddef is None:
        return results
    for sectiondef in compounddef.findall("sectiondef"):
        for member in sectiondef.findall("memberdef"):
            name_elem = member.find("name")
            if name_elem is None:
                continue
            name = text_get(name_elem)
            results.append((name, build_docstring(member)))
    return results


def cpp_escape(s):
    out = []
    for ch in s:
        o = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif o < 0x20:
            out.append("\\%03o" % o)  # 3-digit octal is not greedy past 3 chars
        else:
            out.append(ch)  # UTF-8 bytes preserved by writing the file as utf-8
    return "".join(out)


def write_cc(pairs, output_path):
    lines = [
        "// Auto-generated by generate_docstring_cache.py - DO NOT EDIT.",
        "//",
        "// Pre-filled nanobind docstring cache parsed from the Doxygen XML at",
        "// build time, so the XML does not need to be shipped/installed.",
        "// Regenerated by the before-all step in pyproject.toml.",
        "",
        "#include <string>",
        "#include <unordered_map>",
        "",
        "void fill_docstring_cache(std::unordered_map<std::string, std::string> &cache) {",
    ]
    for name, doc in pairs:
        lines.append('   cache["%s"] = "%s";' % (cpp_escape(name), cpp_escape(doc)))
    lines.append("}")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", default=DEFAULT_XML,
                        help="Path to classmolecules__container__t.xml")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help="Path of the .cc file to generate")
    args = parser.parse_args(argv)

    if not os.path.exists(args.xml):
        sys.stderr.write(
            "WARNING: docstring XML not found at %s - generating empty cache.\n"
            % args.xml)
        write_cc([], args.output)
        return 0

    pairs = parse_docstrings(args.xml)
    write_cc(pairs, args.output)
    sys.stderr.write("Generated %s with %d docstrings.\n"
                     % (args.output, len(pairs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
