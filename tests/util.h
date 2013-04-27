#ifndef TESTS_UTIL_H_
#define TESTS_UTIL_H_

#include <algorithm>
#include <string>

#include "solvers/util/format.h"

std::string ReadFile(const char *name);
void WriteFile(const char *name, const char *data);

inline std::string FixPath(fmt::StringRef s) {
#ifdef WIN32
  std::string fixed = s;
  std::replace(fixed.begin(), fixed.end(), '/', '\\');
  return fixed;
#else
  return s;
#endif
}

#endif  // TESTS_UTIL_H_
