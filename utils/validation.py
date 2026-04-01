import re
import secrets
from typing import Any, Optional


def validate_filename(filename: str) -> str:
    """
    Validate filename để chống path traversal attacks.
    Cho phép subfolders nhưng vẫn đảm bảo an toàn.
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename không được để trống")
    from urllib.parse import unquote

    filename = unquote(filename)
    filename = filename.replace("\\", "/")
    filename = filename.strip("/")
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        raise ValueError("Invalid filename: path traversal detected")
    path_components = filename.split("/")
    for component in path_components:
        if not component or component == "." or component == "..":
            raise ValueError("Invalid filename: invalid path component")
        if not re.match(r"^[\w\s.-]+$", component, re.UNICODE):
            raise ValueError(
                f"Invalid filename: contains invalid characters in component '{component}'"
            )
        if len(component) > 255:
            raise ValueError(
                f"Filename component quá dài (max 255 characters): '{component}'"
            )
    if len(filename) > 1000:
        raise ValueError("Filename path quá dài (max 1000 characters)")
    return filename


def validate_person_id(person_id: str) -> str:
    """
    Validate person_id format (phải là P-X-X).
    """
    if not person_id or not isinstance(person_id, str):
        raise ValueError("person_id không được để trống")
    person_id = person_id.strip()
    if not re.match(r"^P-\d+-\d+$", person_id):
        raise ValueError(
            f"Invalid person_id format: {person_id}. Must be P-X-X format"
        )
    return person_id


def sanitize_string(
    input_str: Any, max_length: Optional[int] = None, allow_empty: bool = False
) -> Optional[str]:
    """
    Sanitize string input để chống injection attacks.
    """
    if input_str is None:
        return "" if allow_empty else None
    if not isinstance(input_str, str):
        input_str = str(input_str)
    sanitized = input_str.strip()
    if not sanitized and (not allow_empty):
        raise ValueError("Input không được để trống")
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def validate_integer(
    value: Any,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
    default: Optional[int] = None,
) -> int:
    """
    Validate và giới hạn integer values để chống DoS.
    """
    try:
        int_val = int(value)
        if min_val is not None and int_val < min_val:
            if default is not None:
                return default
            raise ValueError(f"Value {int_val} is below minimum {min_val}")
        if max_val is not None and int_val > max_val:
            if default is not None:
                return default
            raise ValueError(f"Value {int_val} exceeds maximum {max_val}")
        return int_val
    except (ValueError, TypeError):
        if default is not None:
            return default
        raise ValueError(f"Invalid integer value: {value}")


def secure_compare(a: str, b: str) -> bool:
    """
    So sánh password an toàn, chống timing attack.
    """
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))

