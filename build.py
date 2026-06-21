import os
import subprocess
from typing import Optional, List

class Module:
    def __init__(self, name: str, build_dir: Optional[str] = None):
        self.name = name
        self.build_dir = build_dir

VALID_MODULES = ['backend', 'frontend', 'database']  # Example valid modules


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


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Build script')
    parser.add_argument('--module', type=str, help='Comma-separated list of modules to build')
    parser.add_argument('--list-modules', action='store_true', help='List valid modules')
    args = parser.parse_args()

    if args.list_modules:
        print(f"Valid modules are: {', '.join(VALID_MODULES)}")
        return

    if args.module:
        modules = validate_modules(args.module)
        if not modules:
            exit(1)  # Exit with error if there are invalid modules
        # Proceed with build commands using validated modules

if __name__ == '__main__':
    main()