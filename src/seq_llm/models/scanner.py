# src/seq_llm/models/scanner.py
from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import psutil

CACHE_PATH = Path.home() / ".sequence-llm" / "models_cache.json"
CACHE_TTL_SECONDS = 60 * 60 * 6  # 6 hours


# extensions we consider model files (ordered by likelihood)
MODEL_EXTENSIONS = [".gguf", ".ggml", ".bin", ".pt", ".safetensors", ".ckpt"]


def _default_mount_points() -> List[str]:
    """
    Return sensible mount points / root paths to scan.
    - On Windows: all existing drive letters (C:\, D:\, ...)
    - On Unix: use psutil disk_partitions() mountpoints, plus / (as fallback)
    """
    system = platform.system()
    if system == "Windows":
        roots = []
        for drive in (f"{c}:\\" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            if os.path.exists(drive):
                roots.append(drive)
        # Always include current working drive as fallback
        cwd_drive = os.path.abspath(os.getcwd())[:3]
        if cwd_drive not in roots:
            roots.append(cwd_drive)
        return roots
    else:
        # Gather mount points but avoid pseudo filesystems
        mounts = []
        for part in psutil.disk_partitions(all=False):
            mp = part.mountpoint
            if mp and not mp.startswith("/proc") and not mp.startswith("/sys"):
                mounts.append(mp)
        if "/" not in mounts:
            mounts.append("/")
        return mounts


def _is_candidate_file(name: str, exts: Iterable[str]) -> bool:
    ln = name.lower()
    for e in exts:
        if ln.endswith(e):
            return True
    return False


def _file_info(path: Path) -> Dict:
    try:
        st = path.stat()
        return {
            "path": str(path),
            "size_bytes": st.st_size,
            "size_gb": round(st.st_size / (1024**3), 3),
            "modified_ns": st.st_mtime_ns,
        }
    except Exception:
        return {"path": str(path), "size_bytes": None, "size_gb": None, "modified_ns": None}


def _load_cache() -> Optional[Dict]:
    try:
        if not CACHE_PATH.exists():
            return None
        raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        ts = raw.get("_scanned_at", 0)
        if time.time() - ts > CACHE_TTL_SECONDS:
            return None
        return raw
    except Exception:
        return None


def _save_cache(payload: Dict):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload["_scanned_at"] = int(time.time())
        CACHE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def discover_models(
    roots: Optional[List[str]] = None,
    max_results: int = 200,
    timeout_seconds: int = 30,
    extensions: Optional[List[str]] = None,
    use_cache: bool = True,
) -> List[Dict]:
    """
    Discover candidate model files on the system.

    - roots: list of paths to scan (defaults to all mount points / drive letters)
    - max_results: stop after this many results
    - timeout_seconds: total scan timeout (approx)
    - extensions: list of filename extensions to treat as models
    - use_cache: allow returning cached results within TTL

    Returns list of dicts: {path, size_bytes, size_gb, modified_ns}
    """
    if extensions is None:
        extensions = MODEL_EXTENSIONS

    if use_cache:
        cached = _load_cache()
        if cached and "models" in cached:
            return cached["models"][:max_results]

    if roots is None:
        roots = _default_mount_points()

    start = time.time()
    found: List[Dict] = []
    scanned_roots = set()
    # Walk each root; keep searches conservative (timeout and max_results)
    for root in roots:
        if time.time() - start > timeout_seconds:
            break
        root = os.path.abspath(root)
        if root in scanned_roots:
            continue
        scanned_roots.add(root)
        # Use os.walk but guard against massive directory trees
        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=True):
                # Avoid scanning virtual/proc/sysfs and typical large media folders
                if time.time() - start > timeout_seconds:
                    break
                # Skip some heavy system paths (linux)
                if (
                    dirpath.startswith("/proc")
                    or dirpath.startswith("/sys")
                    or dirpath.startswith("/dev")
                ):
                    continue
                # Quick heuristic: skip node_modules and .git directories to save time
                dirnames[:] = [
                    d
                    for d in dirnames
                    if d not in ("node_modules", ".git", "venv", "env", "__pycache__")
                ]
                # Check files in this directory for candidate extensions or names
                for fn in filenames:
                    if time.time() - start > timeout_seconds:
                        break
                    if _is_candidate_file(fn, extensions):
                        p = Path(dirpath) / fn
                        found.append(_file_info(p))
                        if len(found) >= max_results:
                            break
                if len(found) >= max_results:
                    break
        except PermissionError:
            # skip unreadable roots
            continue
        except Exception:
            # best-effort: continue on errors
            continue

    # sort by size (largest first) then modified time latest
    found_sorted = sorted(
        found, key=lambda x: ((x.get("size_bytes") or 0), (x.get("modified_ns") or 0)), reverse=True
    )
    found_sorted = found_sorted[:max_results]

    # Save cache
    try:
        _save_cache({"models": found_sorted, "roots": roots})
    except Exception:
        pass

    return found_sorted
