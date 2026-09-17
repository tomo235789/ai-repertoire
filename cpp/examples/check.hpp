// ai-repertoire の C++ examples 用の最小テストハーネス（外部依存なし）。
// 各 *_test.cpp は main() を持ち、CHECK(expr) で検証する。失敗があれば終了コード 1。
#pragma once
#include <cstdio>
#include <cstdlib>

namespace repertoire {
inline int failures = 0;
inline void check(bool ok, const char* expr, const char* file, int line) {
  if (!ok) {
    ++failures;
    std::fprintf(stderr, "CHECK failed: %s (%s:%d)\n", expr, file, line);
  }
}
inline int finish(const char* name) {
  if (failures == 0) std::printf("ok   %s\n", name);
  else std::printf("FAIL %s (%d failures)\n", name, failures);
  return failures == 0 ? 0 : 1;
}
}  // namespace repertoire

#define CHECK(expr) ::repertoire::check(static_cast<bool>(expr), #expr, __FILE__, __LINE__)
#define CHECK_THROWS(stmt, ExceptionType)                                              \
  do {                                                                                 \
    bool thrown = false;                                                               \
    try { stmt; } catch (const ExceptionType&) { thrown = true; } catch (...) {}       \
    ::repertoire::check(thrown, "throws " #ExceptionType ": " #stmt, __FILE__, __LINE__); \
  } while (0)
#define FINISH() return ::repertoire::finish(__FILE__)
