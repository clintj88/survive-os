"""External Content Integration API routes."""

from pathlib import Path

from fastapi import APIRouter

from .config import load_config

router = APIRouter(prefix="/api/external", tags=["external"])


def _get_ext_config() -> dict:
    config = load_config()
    return config.get("external_content", {})


@router.get("/resources")
def list_resources() -> list[dict]:
    ext = _get_ext_config()
    resources = [
        {
            "name": "Kiwix (Offline Wikipedia)",
            "type": "kiwix",
            "path": ext.get("kiwix_zim_path", ""),
            "port": ext.get("kiwix_port", 8091),
            "available": bool(ext.get("kiwix_zim_path") and Path(ext["kiwix_zim_path"]).exists()),
        },
        {
            "name": "OpenStax Textbooks",
            "type": "openstax",
            "path": ext.get("openstax_path", ""),
            "available": bool(ext.get("openstax_path") and Path(ext["openstax_path"]).is_dir()),
        },
        {
            "name": "Project Gutenberg",
            "type": "gutenberg",
            "path": ext.get("gutenberg_path", ""),
            "available": bool(ext.get("gutenberg_path") and Path(ext["gutenberg_path"]).is_dir()),
        },
    ]
    return resources


@router.get("/kiwix")
def kiwix_status() -> dict:
    ext = _get_ext_config()
    zim_path = ext.get("kiwix_zim_path", "")
    available = bool(zim_path and Path(zim_path).exists())
    return {
        "available": available,
        "zim_path": zim_path,
        "port": ext.get("kiwix_port", 8091),
        "url": f"http://localhost:{ext.get('kiwix_port', 8091)}" if available else None,
    }


@router.get("/openstax")
def openstax_list() -> dict:
    ext = _get_ext_config()
    path = ext.get("openstax_path", "")
    if not path or not Path(path).is_dir():
        return {"available": False, "files": []}

    files = sorted([f.name for f in Path(path).glob("*.pdf")])
    return {"available": True, "path": path, "files": files}


@router.get("/gutenberg")
def gutenberg_list() -> dict:
    ext = _get_ext_config()
    path = ext.get("gutenberg_path", "")
    if not path or not Path(path).is_dir():
        return {"available": False, "files": []}

    extensions = ("*.txt", "*.epub", "*.pdf")
    files = []
    for ext_pattern in extensions:
        files.extend(f.name for f in Path(path).glob(ext_pattern))
    return {"available": True, "path": path, "files": sorted(files)}
