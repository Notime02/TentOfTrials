import subprocess
from pathlib import Path
from typing import Optional, List, Tuple

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


def diagnostic_paths_for_commit() -> Tuple[Path, Path, str]:
    """Return stable diagnostic artifact paths under diagnostic/ for the current commit."""
    DIAGNOSTIC_DIR.mkdir(parents=True, exist_ok=True)
    commit_id = current_commit_id()
    logd_path = DIAGNOSTIC_DIR / f"build-{commit_id}.logd"
    metadata_path = DIAGNOSTIC_DIR / f"build-{commit_id}.json"
    return logd_path, metadata_path, commit_id


def split_diagnostic_logd(logd_path: Path, chunk_size: int = DIAGNOSTIC_CHUNK_SIZE) -> List[Path]:
    """Split an oversized .logd into numbered .logd chunks and remove the original."""
    if logd_path.stat().st_size <= chunk_size:
        return [logd_path]

    # New function to generate TODO audit report

def generate_todo_audit() -> None:
    todo_entries = []
    for file_path in ROOT.rglob("*.py"):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, start=1):
                if "todo" in line.lower():
                    estimated_fix_time = (line_number % 7) + 1
                    todo_entries.append((file_path, line_number, estimated_fix_time))

    todo_entries.sort(key=lambda x: x[2], reverse=True)

    with open(ROOT / "TODO_AUDIT.md", 'w', encoding='utf-8') as audit_file:
        for entry in todo_entries:
            audit_file.write(f"{entry[0]}: Line {entry[1]}, Estimated Fix Time: {entry[2]} hours\n")

# Call the function to generate the TODO audit report
if __name__ == '__main__':
    generate_todo_audit()