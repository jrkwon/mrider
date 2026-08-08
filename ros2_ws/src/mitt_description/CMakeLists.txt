cmake_minimum_required(VERSION 3.8)
project(mitt_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  urdf
  config
  launch
  meshes
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  # MUST be set BEFORE find_package(ament_lint_auto) - the exclude list is
  # read at that point, not at find_test_dependencies() time.
  #
  # ament_copyright on Humble only recognises apache2/bsd/gpl/boost headers;
  # there is no MIT template, so it reports license=<unknown> for every file
  # regardless of content. Excluded rather than changing the project licence
  # to satisfy a linter.
  #
  # NOTE: the repository has no LICENSE file yet; package.xml says MIT as a
  # scaffolding default. Settle that before external release.
  list(APPEND AMENT_LINT_AUTO_EXCLUDE ament_cmake_copyright)

  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
