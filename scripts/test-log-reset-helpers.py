"""Sanity test cho services.log_reset helpers (không đụng DB)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from datetime import datetime
from services.log_reset import LOG_TABLES, _mysql_escape_value

print("LOG_TABLES          :", LOG_TABLES)
print("escape None         :", _mysql_escape_value(None))
print("escape int          :", _mysql_escape_value(42))
print("escape float        :", _mysql_escape_value(3.14))
print("escape bool True    :", _mysql_escape_value(True))
print("escape str simple   :", _mysql_escape_value("hello"))
print("escape str quote    :", _mysql_escape_value("O'Brien"))
print("escape str backslash:", _mysql_escape_value("a\\b"))
print("escape newline      :", _mysql_escape_value("a\nb"))
print("escape dict         :", _mysql_escape_value({"a": 1, "v": "x"}))
print("escape list         :", _mysql_escape_value([1, 2, 3]))
print("escape datetime     :", _mysql_escape_value(datetime(2026, 4, 19, 21, 55, 0)))
print("escape bytes        :", _mysql_escape_value(b"\x00\x01\xff"))
print("\nAll helpers OK.")
