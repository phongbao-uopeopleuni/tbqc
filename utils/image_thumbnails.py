from __future__ import annotations

import logging
import os
from pathlib import Path

from utils.validation import validate_filename

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_IMAGE_PREFIX = "/static/images/"
THUMB_ROOT = "_thumbs"
THUMB_MAX_EDGE = 640
THUMB_QUALITY = 80
THUMB_SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def get_images_base_dir() -> Path:
    volume_mount_path = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    if volume_mount_path and os.path.exists(volume_mount_path):
        return Path(volume_mount_path)
    return BASE_DIR / "static" / "images"


def normalize_public_image_url(image_ref: str | None) -> str | None:
    if not image_ref:
        return None
    image_ref = str(image_ref).strip().replace("\\", "/")
    if not image_ref:
        return None
    if image_ref.startswith(("http://", "https://", "data:")):
        return image_ref
    if image_ref.startswith(STATIC_IMAGE_PREFIX):
        return image_ref
    if image_ref.startswith("static/images/"):
        return f"/{image_ref.lstrip('/')}"
    if image_ref.startswith("/"):
        return image_ref
    rel_path = _normalize_relative_path(image_ref)
    return f"{STATIC_IMAGE_PREFIX}{rel_path}" if rel_path else None


def get_thumbnail_url(
    image_ref: str | None,
    *,
    source_path: str | None = None,
    create_if_missing: bool = False,
    fallback_to_original: bool = True,
) -> str | None:
    rel_path = _normalize_relative_path(image_ref)
    if not rel_path:
        return normalize_public_image_url(image_ref) if fallback_to_original else None

    if rel_path.startswith(f"{THUMB_ROOT}/"):
        return f"{STATIC_IMAGE_PREFIX}{rel_path}"

    base_dir = _resolve_base_dir(source_path=source_path, relative_path=rel_path)
    thumb_rel_path = _thumbnail_relative_path(rel_path)
    thumb_path = base_dir / Path(thumb_rel_path)
    if thumb_path.exists():
        return f"{STATIC_IMAGE_PREFIX}{thumb_rel_path}"

    if create_if_missing:
        original_path = Path(source_path) if source_path else base_dir / Path(rel_path)
        if ensure_thumbnail_file(original_path, relative_path=rel_path):
            return f"{STATIC_IMAGE_PREFIX}{thumb_rel_path}"

    return normalize_public_image_url(image_ref) if fallback_to_original else None


def image_reference_exists(image_ref: str | None, *, source_path: str | None = None) -> bool:
    rel_path = _normalize_relative_path(image_ref)
    if not rel_path:
        return bool(image_ref and str(image_ref).startswith(("http://", "https://", "data:")))

    base_dir = _resolve_base_dir(source_path=source_path, relative_path=rel_path)
    return (base_dir / Path(rel_path)).exists()


def ensure_thumbnail_for_image(image_ref: str | None, *, source_path: str | None = None) -> tuple[str | None, str | None]:
    rel_path = _normalize_relative_path(image_ref)
    if not rel_path or rel_path.startswith(f"{THUMB_ROOT}/"):
        normalized_url = normalize_public_image_url(image_ref)
        return normalized_url, None

    base_dir = _resolve_base_dir(source_path=source_path, relative_path=rel_path)
    thumb_rel_path = _thumbnail_relative_path(rel_path)
    original_path = Path(source_path) if source_path else base_dir / Path(rel_path)
    if ensure_thumbnail_file(original_path, relative_path=rel_path):
        return f"{STATIC_IMAGE_PREFIX}{thumb_rel_path}", str(base_dir / Path(thumb_rel_path))
    return None, None


def ensure_thumbnail_file(original_path: str | Path, *, relative_path: str | None = None) -> bool:
    original_path = Path(original_path)
    if not original_path.exists() or not original_path.is_file():
        return False

    if original_path.suffix.lower() not in THUMB_SUPPORTED_EXTENSIONS:
        return False

    try:
        rel_path = relative_path or str(original_path.relative_to(get_images_base_dir())).replace("\\", "/")
        rel_path = _normalize_relative_path(rel_path)
        if not rel_path or rel_path.startswith(f"{THUMB_ROOT}/"):
            return False
        base_dir = _resolve_base_dir(source_path=str(original_path), relative_path=rel_path)
        thumb_path = base_dir / Path(_thumbnail_relative_path(rel_path))
        if thumb_path.exists():
            return True

        thumb_path.parent.mkdir(parents=True, exist_ok=True)

        from PIL import Image, ImageOps

        with Image.open(original_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            elif img.mode == "L":
                img = img.convert("RGB")
            img.thumbnail((THUMB_MAX_EDGE, THUMB_MAX_EDGE))
            img.save(thumb_path, format="WEBP", quality=THUMB_QUALITY, method=6)
        return True
    except Exception as exc:
        logger.warning("Could not generate thumbnail for %s: %s", original_path, exc)
        return False


def _thumbnail_relative_path(relative_path: str) -> str:
    path = Path(relative_path)
    return f"{THUMB_ROOT}/{path.with_suffix('.webp').as_posix()}"


def _resolve_base_dir(*, source_path: str | None, relative_path: str) -> Path:
    if source_path:
        source = Path(source_path).resolve()
        depth = len(Path(relative_path).parts)
        if depth <= len(source.parents):
            return source.parents[depth - 1]
    return get_images_base_dir()


def _normalize_relative_path(image_ref: str | None) -> str | None:
    if not image_ref:
        return None

    image_ref = str(image_ref).strip().replace("\\", "/")
    if not image_ref or image_ref.startswith(("http://", "https://", "data:")):
        return None

    image_ref = image_ref.split("?", 1)[0].split("#", 1)[0]
    if image_ref.startswith(STATIC_IMAGE_PREFIX):
        image_ref = image_ref[len(STATIC_IMAGE_PREFIX):]
    elif image_ref.startswith("static/images/"):
        image_ref = image_ref[len("static/images/"):]
    elif image_ref.startswith("/"):
        return None

    image_ref = image_ref.lstrip("/")
    if not image_ref:
        return None

    try:
        return validate_filename(image_ref)
    except ValueError:
        logger.warning("Invalid image reference for thumbnailing: %s", image_ref)
        return None
