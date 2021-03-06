# CMake initialization code that should be run before the project command.

function (find_setenv var)
  set(winsdk_key
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Microsoft SDKs\\Windows")
  find_program(setenv NAMES SetEnv.cmd
    PATHS "[${winsdk_key};CurrentInstallFolder]/bin")
  set(${var} ${setenv} PARENT_SCOPE)
endfunction ()

if (ARGS)
  # Run CMake in a Microsoft SDK build environment.
  find_setenv(WINSDK_SETENV)
  if (WINSDK_SETENV)
    if (NOT ARGS MATCHES Win64)
      set(setenv_arg "/x86")
    endif ()
    # If Microsoft SDK is installed create script run-msbuild.bat that
    # calls SetEnv.cmd to to set up build environment and runs msbuild.
    # It is useful when building Visual Studio projects with the SDK
    # toolchain rather than Visual Studio.
    # Set FrameworkPathOverride to get rid of MSB3644 warnings.
    file(WRITE "${CMAKE_BINARY_DIR}/run-msbuild.bat" "
      call \"${WINSDK_SETENV}\" ${setenv_arg}
      msbuild -p:FrameworkPathOverride=^\"C:\\Program Files^
\\Reference Assemblies\\Microsoft\\Framework\\.NETFramework\\v4.0^\" %*")
    execute_process(
      COMMAND ${CMAKE_COMMAND} -E echo "\"${WINSDK_SETENV}\" ${setenv_arg}")
  endif ()
  return ()
endif ()

include(CMakeParseArguments)

# Joins arguments and sets the result to <var>.
# Usage:
#   join(<var> [<arg>...])
function (join var)
  unset(result)
  foreach (arg ${ARGN})
    if (DEFINED result)
      set(result "${result} ${arg}")
    else ()
      set(result "${arg}")
    endif ()
  endforeach ()
  set(${var} "${result}" PARENT_SCOPE)
endfunction ()

# Sets cache variable <var> to the value <value>. The arguments
# following <type> are joined into a single docstring which allows
# breaking long documentation into smaller strings.
# Usage:
#   set_cache(<var> <value> <type> docstring... [FORCE])
function (set_cache var value type)
  cmake_parse_arguments(set_cache FORCE "" "" ${ARGN})
  unset(force)
  if (set_cache_FORCE)
    set(force FORCE)
  endif ()
  join(docstring ${set_cache_UNPARSED_ARGUMENTS})
  set(${var} ${value} CACHE ${type} "${docstring}" ${force})
endfunction ()

if (NOT CMAKE_BUILD_TYPE)
  # Set the default CMAKE_BUILD_TYPE to Release.
  # This should be done before the project command since the latter sets
  # CMAKE_BUILD_TYPE itself.
  set_cache(CMAKE_BUILD_TYPE Release STRING
    "Choose the type of build, options are: None(CMAKE_CXX_FLAGS or"
    "CMAKE_C_FLAGS used) Debug Release RelWithDebInfo MinSizeRel.")
endif ()

function (override var file)
  if (EXISTS "${file}")
    set(${var} ${file} PARENT_SCOPE)
  endif ()
endfunction ()

# Use static MSVC runtime.
# This should be done before the project command.
override(CMAKE_USER_MAKE_RULES_OVERRIDE
  ${CMAKE_CURRENT_LIST_DIR}/c_flag_overrides.cmake)
override(CMAKE_USER_MAKE_RULES_OVERRIDE_CXX
  ${CMAKE_CURRENT_LIST_DIR}/cxx_flag_overrides.cmake)
