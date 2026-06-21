import json
import subprocess
from pathlib import Path

# ... (other imports and code) ...

def generate_retention_report(log_files, retention_decisions):
    report = {
        "retained_files": [],
        "pruned_files": []
    }

    for file in log_files:
        if file in retention_decisions['retained']:
            report["retained_files"].append({
                "file_name": file,
                "size": get_file_size(file),
                "mtime": get_file_mtime(file),
                "retention_reason": retention_decisions['retained'][file]
            })
        elif file in retention_decisions['pruned']:
            report["pruned_files"].append({
                "file_name": file,
                "size": get_file_size(file),
                "mtime": get_file_mtime(file),
                "retention_reason": retention_decisions['pruned'][file]
            })

    return report


def get_file_size(file_name):
    return Path(file_name).stat().st_size


def get_file_mtime(file_name):
    return Path(file_name).stat().st_mtime

# ... (rest of the existing code) ...

# Example usage of the retention report generation
log_files = ["log1.log", "log2.log"]  # Example log files
retention_decisions = {
    "retained": {"log1.log": "kept for audit"},
    "pruned": {"log2.log": "exceeded retention period"}
}

retention_report = generate_retention_report(log_files, retention_decisions)
print(json.dumps(retention_report, indent=2))

# ... (rest of the existing code) ...