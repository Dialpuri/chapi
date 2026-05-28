project(ssm)

add_library(ssm STATIC
    ${WRK_DIR}/checkout/ssm/ssm/ssm_align.cpp
    ${WRK_DIR}/checkout/ssm/ssm/ssm_csia.cpp
    ${WRK_DIR}/checkout/ssm/ssm/ssm_graph.cpp
    ${WRK_DIR}/checkout/ssm/ssm/ssm_malign.cpp
    ${WRK_DIR}/checkout/ssm/ssm/ssm_superpose.cpp
    ${WRK_DIR}/checkout/ssm/ssm/ssm_vxedge.cpp
)

target_include_directories(ssm PRIVATE ${WRK_DIR}/checkout/mmdb2)

set(ssm_HEADERS
    ${WRK_DIR}/checkout/ssm/ssm/ssm_align.h
    ${WRK_DIR}/checkout/ssm/ssm/ssm_csia.h
    ${WRK_DIR}/checkout/ssm/ssm/ssm_defs.h
    ${WRK_DIR}/checkout/ssm/ssm/ssm_graph.h
    ${WRK_DIR}/checkout/ssm/ssm/ssm_malign.h
    ${WRK_DIR}/checkout/ssm/ssm/ssm_superpose.h
    ${WRK_DIR}/checkout/ssm/ssm/ssm_vxedge.h
)

set_target_properties(ssm PROPERTIES PUBLIC_HEADER "${ssm_HEADERS}")

install(TARGETS ssm
    LIBRARY DESTINATION lib
    PUBLIC_HEADER DESTINATION include/ssm
)
