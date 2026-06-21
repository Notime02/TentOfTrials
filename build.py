import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict

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


def split_diagnostic_logd(logd_path: Path, chunk_size: int = DIAGNOSTIC_CHUNK_SIZE) -> list[Path]:
    """Split an oversized .logd into numbered .logd chunks and remove the original."""
    if logd_path.stat().st_size <= chunk_size:
        return [logd_path]


def export_sarif_diagnostics(findings: List[Dict[str, str]], output_path: Path) -> None:
    """Export AI diagnostics findings in SARIF format."""
    sarif_output = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "AI Diagnostics",
                        "version": "1.0",
                        "informationUri": "https://example.com",
                    }
                },
                "results": []
            }
        ]
    }

    for finding in findings:
        # Redact secret-looking values
        message = finding["message"].replace("secret", "[REDACTED]")
        sarif_output["runs"][0]["results"].append({
            "ruleId": finding["rule_id"],
            "level": finding["severity"],
            "message": {"text": message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding["file_path"],
                        },
                        "region": {
                            "startLine": finding.get("line", 1)
                        }
                    }
                }
            ]
        })

    with open(output_path, 'w') as f:
        json.dump(sarif_output, f, indent=4)

# Example usage (this should be called in the appropriate place in your code):
# findings = [
#     {"rule_id": "R1", "severity": "error", "message": "Found issue", "file_path": "src/main.rs", "line": 10},
#     {"rule_id": "R2", "severity": "warning", "message": "secret found", "file_path": "src/lib.rs", "line": 20}
# ]
# export_sarif_diagnostics(findings, DIAGNOSTIC_DIR / f"sarif-{current_commit_id()}.sarif.json")
