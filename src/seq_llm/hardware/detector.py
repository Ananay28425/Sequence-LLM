# src/seq_llm/hardware/detector.py
from __future__ import annotations

import json
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

import psutil


@dataclass
class GPUInfo:
    name: str
    memory_gb: Optional[float] = None
    vendor: Optional[str] = None


@dataclass
class HardwareProfile:
    os: str
    cpu_physical: int
    cpu_logical: int
    total_ram_gb: float
    gpus: List[GPUInfo]
    has_gpu: bool
    cuda_available: bool
    probe_raw: Dict

    def to_dict(self):
        d = asdict(self)
        d["probe_raw"] = json.dumps(self.probe_raw)
        return d


def _bytes_to_gb(b: int) -> float:
    return round(b / (1024 ** 3), 2)


def _probe_nvidia_smi() -> List[Dict]:
    """Return list of GPUs from nvidia-smi if available. Conservative: do not crash."""
    path = shutil.which("nvidia-smi")
    if not path:
        return []
    try:
        out = subprocess.check_output([path, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"], stderr=subprocess.DEVNULL, text=True)
        gpus = []
        for line in out.splitlines():
            parts = [p.strip() for p in line.split(",")]
            name = parts[0] if parts else "nvidia"
            mem = float(parts[1]) / 1024 if len(parts) > 1 and parts[1].isdigit() else None
            gpus.append({"name": name, "memory_gb": mem, "vendor": "nvidia"})
        return gpus
    except Exception:
        return []


def _probe_rocm_smi() -> List[Dict]:
    path = shutil.which("rocm-smi")
    if not path:
        return []
    try:
        out = subprocess.check_output([path, "--showproductname", "--showuse"], stderr=subprocess.DEVNULL, text=True)
        # Very conservative parsing fallback
        lines = out.splitlines()
        if not lines:
            return []
        return [{"name": "rocm_gpu", "memory_gb": None, "vendor": "amd"}]
    except Exception:
        return []


def detect_hardware() -> HardwareProfile:
    os_name = platform.system()
    cpu_logical = psutil.cpu_count(logical=True) or 1
    cpu_physical = psutil.cpu_count(logical=False) or cpu_logical
    total_ram = _bytes_to_gb(psutil.virtual_memory().total)

    # Probe GPUs
    gpus_raw = []
    gpus_raw.extend(_probe_nvidia_smi())
    gpus_raw.extend(_probe_rocm_smi())

    # If no vendor probe succeeded, do a lightweight lspci fallback on linux
    if not gpus_raw and os_name == "Linux" and shutil.which("lspci"):
        try:
            out = subprocess.check_output(["lspci"], stderr=subprocess.DEVNULL, text=True)
            if "VGA compatible controller" in out or "3D controller" in out:
                gpus_raw.append({"name": "unknown_gpu", "memory_gb": None, "vendor": None})
        except Exception:
            pass

    gpus = [GPUInfo(name=g.get("name", "gpu"), memory_gb=g.get("memory_gb"), vendor=g.get("vendor")) for g in gpus_raw]
    has_gpu = len(gpus) > 0
    cuda_available = bool(shutil.which("nvidia-smi"))  # conservative proxy

    return HardwareProfile(
        os=os_name,
        cpu_physical=cpu_physical,
        cpu_logical=cpu_logical,
        total_ram_gb=total_ram,
        gpus=gpus,
        has_gpu=has_gpu,
        cuda_available=cuda_available,
        probe_raw={"nvidia": len(_probe_nvidia_smi()) > 0, "rocm": len(_probe_rocm_smi()) > 0},
    )
