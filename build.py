import os
import subprocess
import sys
import time
import platform
import shutil
import datetime
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

ROOT = Path(__file__).resolve().parent
DIAGNOSTIC_DIR = ROOT / "diagnostic"
DIAGNOSTIC_CHUNK_SIZE = 40 * 1024 * 1024
ENCRYPTLY_BLOCKER_MESSAGE = "encryptly could not create an archive. You may have timed out; try launching it in the background and waiting for it to finish with no timeout due to a bug in encryptly."

def current_commit_id() -> str:
    """Return the first 4 bytes (8 hex chars) of HEAD for stable per-commit diagnostics."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit = result.stdout.strip()
        if result.returncode == 0 and len(commit) >= 8:
            return commit[:8]
    except Exception:
        pass
    return "00000000"


def diagnostic_paths_for_commit() -> tuple[Path, Path, str]:
    """Return stable diagnostic artifact paths under diagnostic/ for the current commit."""
    DIAGNOSTIC_DIR.mkdir(parents=True, exist_ok=True)
    commit_id = current_commit_id()
    logd_path = DIAGNOSTIC_DIR / f"build-{commit_id}.logd"
    metadata_path = DIAGNOSTIC_DIR / f"build-{commit_id}.json"
    return logd_path, metadata_path, commit_id


class Module:
    def __init__(self, name: str, build_dir: Optional[str] = None):
        self.name = name
        self.build_dir = build_dir


VALID_MODULES = ['backend', 'frontend', 'database']  # Example valid modules

ENCRYPTLY_DIR = ROOT / "tools" / "encryptly"
ENCRYPTLY_BINARIES = {
    "linux-x64": ENCRYPTLY_DIR / "linux-x64" / "encryptly",
    "linux-arm64": ENCRYPTLY_DIR / "linux-arm64" / "encryptly",
    "macos-arm64": ENCRYPTLY_DIR / "macos-arm64" / "encryptly",
    "macos-x64": ENCRYPTLY_DIR / "macos-x64" / "encryptly",
    "windows-x64": ENCRYPTLY_DIR / "windows-x64" / "encryptly.exe",
    "windows-arm64": ENCRYPTLY_DIR / "windows-arm64" / "encryptly.exe",
}
LEGACY_ENCRYPTLY_BIN = ENCRYPTLY_DIR / "encryptly"


def validate_modules(module_names: str) -> List[str]:
    modules = [name.strip() for name in module_names.split(',')]
    invalid_modules = [name for name in modules if name not in VALID_MODULES]
    if invalid_modules:
        print(f"Invalid module names: {', '.join(invalid_modules)}")
        print(f"Valid modules are: {', '.join(VALID_MODULES)}")
        return []  # Return empty list if there are invalid modules
    return modules


def run_cmd(cmd: list[str], **kwargs) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, **kwargs
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        return result.returncode == 0, output.strip()
    except Exception as e:
        return False, str(e)


def _normalize_os() -> Optional[str]:
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return None


def detect_encryptly_platform() -> Optional[str]:
    os_name = _normalize_os()
    # Assuming _normalize_arch is defined elsewhere in your file
    arch = _normalize_arch(platform.machine()) 
    if os_name is None or arch is None:
        return None
    return f"{os_name}-{arch}"


def get_encryptly_bin() -> Optional[Path]:
    target = detect_encryptly_platform()
    if target is not None:
        binary = ENCRYPTLY_BINARIES.get(target)
        if binary is not None and binary.exists():
            return binary

    if LEGACY_ENCRYPTLY_BIN.exists():
        return LEGACY_ENCRYPTLY_BIN

    return None


def encryptly_platform_help() -> str:
    detected = detect_encryptly_platform() or "unsupported"
    available = ", ".join(sorted(ENCRYPTLY_BINARIES))
    return f"detected {detected}; available: {available}"


def check_encryptly_runs(timeout: int = 600) -> tuple[bool, str]:
    """Verify encryptly can create a diagnostic bundle before doing any build work."""
    encryptly_bin = get_encryptly_bin()
    if encryptly_bin is None:
        return False, f"encryptly binary not found ({encryptly_platform_help()})"

    workspace = Path.home() / ".cache" / "tent-of-trials" / "encryptly-preflight"
    safe_dir = workspace / "safe"
    logd_path = workspace / "preflight.logd"
    try:
        shutil.rmtree(workspace, ignore_errors=True)
        safe_dir.mkdir(parents=True, exist_ok=True)
        (safe_dir / "preflight.txt").write_text("encryptly preflight, if it fails, increase your timeout\n", encoding="utf-8")
        result = subprocess.run(
            [
                str(encryptly_bin),
                "pack",
                str(logd_path),
                "--include",
                str(workspace),
                "--max-file-size",
                "32000",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if not logd_path.exists():
            return False, "encryptly preflight completed without creating a .logd"
        return True, "encryptly preflight passed"
    except subprocess.TimeoutExpired:
        return False, f"encryptly preflight TIMEOUT ({timeout}s)"
    except Exception as e:
        return False, str(e)


def verify_binary(module: Module) -> Optional[str]:
    if module.build_dir is None:
        return None
    path = module.build_dir
    if module.name == "backend":
        target = path / "debug" / module.name
        if not target.exists():
            target = path / "release" / module.name
        if target.exists():
            return str(target)
    if path.exists():
        return str(path)
    return None


def collect_system_info() -> str:
    lines = [
        # ... (truncated) ...
    ]
    return '\n'.join(lines)


def write_diagnostic_report(metadata_path: Path, report: dict) -> None:
    metadata_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"    {color('✓', Colors.GREEN)} {metadata_path.relative_to(ROOT)}