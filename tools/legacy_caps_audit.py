import os
import re
import sys
from pathlib import Path

# Define the directory to search for legacy files
SEARCH_DIR = Path('.').resolve()

def audit_legacy_comments():
    legacy_pattern = re.compile(r'\bLEGACY\b')
    violations = []

    for root, _, files in os.walk(SEARCH_DIR):
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                with file_path.open('r') as f:
                    content = f.readlines()

                # Check if the file contains legacy references
                if any('legacy' in line.lower() for line in content):
                    # Check for LEGACY comment
                    if not any(legacy_pattern.search(line) for line in content):
                        violations.append(file_path)
                        # Add LEGACY comment
                        content.append('# LEGACY\n')
                        with file_path.open('w') as f:
                            f.writelines(content)

    return violations

if __name__ == '__main__':
    violations = audit_legacy_comments()
    if violations:
        print(f'Found {len(violations)} files with missing LEGACY comments:')
        for violation in violations:
            print(violation)
        sys.exit(1)
    else:
        print('All files pass the LEGACY comment check.')
        sys.exit(0)