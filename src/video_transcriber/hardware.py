import logging
import platform
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HardwareInfo:
    os_name: str
    os_version: str
    cpu_count: int
    ram_gb: float
    has_cuda: bool
    vram_gb: float
    gpu_name: str
    recommended_model: str
    recommended_device: str
    recommended_compute: str


def _get_ram_gb() -> float:
    try:
        import psutil
        return psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        pass

    try:
        if platform.system() == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            mem = ctypes.c_ulonglong(0)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
            return mem.value / (1024 ** 3)
        else:
            result = subprocess.run(
                ["free", "-g", "-b"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                if line.startswith("Mem:"):
                    return int(line.split()[1]) / (1024 ** 3)
    except Exception:
        pass
    return 4.0


def _get_cuda_info() -> tuple[bool, float, str]:
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_mem / (1024 ** 3)
            return True, vram, name
    except ImportError:
        pass

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            line = result.stdout.strip().splitlines()[0]
            parts = line.split(",")
            name = parts[0].strip()
            vram_mb = float(parts[1].strip())
            return True, vram_mb / 1024, name
    except Exception:
        pass

    return False, 0.0, ""


def _recommend_model(has_cuda: bool, vram_gb: float, ram_gb: float) -> tuple[str, str, str]:
    if has_cuda and vram_gb >= 10:
        return "large-v2", "cuda", "float16"
    if has_cuda and vram_gb >= 5:
        return "medium", "cuda", "float16"
    if has_cuda and vram_gb >= 2.5:
        return "small", "cuda", "float16"
    if has_cuda and vram_gb >= 1.5:
        return "base", "cuda", "int8_float16"

    if ram_gb >= 16:
        return "medium", "cpu", "int8"
    if ram_gb >= 8:
        return "small", "cpu", "int8"
    if ram_gb >= 4:
        return "base", "cpu", "int8"

    return "tiny", "cpu", "int8"


MODEL_SPECS = {
    "tiny":     {"vram": "~1 GB",  "ram": "~1 GB",  "speed": "fastest",     "quality": "basic"},
    "base":     {"vram": "~1 GB",  "ram": "~1 GB",  "speed": "fast",        "quality": "good"},
    "small":    {"vram": "~2 GB",  "ram": "~2 GB",  "speed": "moderate",    "quality": "great"},
    "medium":   {"vram": "~5 GB",  "ram": "~5 GB",  "speed": "slow",        "quality": "excellent"},
    "large-v2": {"vram": "~10 GB", "ram": "~10 GB", "speed": "very slow",   "quality": "best"},
}


def detect_hardware() -> HardwareInfo:
    os_name = platform.system()
    os_version = platform.version()
    cpu_count = platform.processor() or f"{_cpu_count()} cores"

    import os
    cpu_cores = os.cpu_count() or 2

    ram_gb = _get_ram_gb()
    has_cuda, vram_gb, gpu_name = _get_cuda_info()

    model, device, compute = _recommend_model(has_cuda, vram_gb, ram_gb)

    info = HardwareInfo(
        os_name=os_name,
        os_version=os_version,
        cpu_count=cpu_cores,
        ram_gb=ram_gb,
        has_cuda=has_cuda,
        vram_gb=vram_gb,
        gpu_name=gpu_name,
        recommended_model=model,
        recommended_device=device,
        recommended_compute=compute,
    )
    return info


def _cpu_count() -> int:
    import os
    return os.cpu_count() or 2


def print_hardware_report(info: HardwareInfo) -> None:
    print("\n" + "=" * 50)
    print("  Hardware Detection Report")
    print("=" * 50)
    print(f"  OS:           {info.os_name} ({info.os_version})")
    print(f"  CPU cores:    {info.cpu_count}")
    print(f"  RAM:          {info.ram_gb:.1f} GB")
    if info.has_cuda:
        print(f"  GPU:          {info.gpu_name}")
        print(f"  VRAM:         {info.vram_gb:.1f} GB")
    else:
        print(f"  GPU:          Not detected (CPU mode)")
    print("-" * 50)
    spec = MODEL_SPECS[info.recommended_model]
    print(f"  Recommended model:   {info.recommended_model}")
    print(f"    VRAM needed:  {spec['vram']}")
    print(f"    RAM needed:   {spec['ram']}")
    print(f"    Speed:        {spec['speed']}")
    print(f"    Quality:      {spec['quality']}")
    print(f"  Device:        {info.recommended_device}")
    print(f"  Compute type:  {info.recommended_compute}")
    print("=" * 50 + "\n")
