"""Print the runtime Flask url_map in contract-test format."""

from __future__ import annotations

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    import app as app_module

    for rule in app_module.app.url_map.iter_rules():
        methods = sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"})
        methods_text = "|".join(methods) if methods else "GET"
        print(f"{methods_text} {rule.rule} -> {rule.endpoint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
