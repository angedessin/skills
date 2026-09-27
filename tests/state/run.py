#!/usr/bin/env python3
"""判定表テストのランナー — table-driven ケース + 構造検査を回す。

Usage: python3 tests/state/run.py
Exit 0 = all pass. Exit 1 = failure (prints details).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_pipeline_state import all_results  # noqa: E402


def main() -> int:
    results = all_results()
    passed = 0
    for check_id, label, details in results:
        if details:
            print(f"FAIL {check_id}: {label}")
            for line in details:
                print(f"  {line}")
        else:
            print(f"PASS {check_id}: {label}")
            passed += 1
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
