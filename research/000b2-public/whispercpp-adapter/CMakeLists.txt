cmake_minimum_required(VERSION 3.16)
project(wispral_whispercpp_c0_adapter LANGUAGES C CXX)

if(NOT DEFINED WHISPER_SOURCE_DIR)
  message(FATAL_ERROR "WHISPER_SOURCE_DIR must point to the exact pinned whisper.cpp source tree")
endif()

get_filename_component(WHISPER_SOURCE_DIR "${WHISPER_SOURCE_DIR}" REALPATH)

set(WHISPER_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(WHISPER_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(WHISPER_BUILD_SERVER OFF CACHE BOOL "" FORCE)
set(GGML_CUDA OFF CACHE BOOL "" FORCE)
set(GGML_METAL OFF CACHE BOOL "" FORCE)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)

add_subdirectory("${WHISPER_SOURCE_DIR}" whispercpp EXCLUDE_FROM_ALL)

add_executable(wispral-whispercpp-c0 adapter.cpp)
target_compile_features(wispral-whispercpp-c0 PRIVATE cxx_std_17)
target_include_directories(wispral-whispercpp-c0 PRIVATE
  "${WHISPER_SOURCE_DIR}/include"
  "${WHISPER_SOURCE_DIR}/ggml/include"
)
target_link_libraries(wispral-whispercpp-c0 PRIVATE whisper)
