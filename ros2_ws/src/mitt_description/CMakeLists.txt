cmake_minimum_required(VERSION 3.8)
project(mitt_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  urdf
  config
  meshes
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  # Functional tests, not linters: the URDF, controller and Nav2 parameters
  # each vehicle gets carry its measured values. The `functional_` prefix is
  # what CI selects (.github/workflows/workspace.yml).
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(functional_vehicle_geometry test/test_vehicle_geometry.py
    TIMEOUT 120)
endif()

ament_package()
