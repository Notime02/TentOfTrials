import argparse
import shutil
from pathlib import Path

# Assuming MODULES is a list of module objects with a 'name' attribute
MODULES = [...]  # Placeholder for actual module definitions

ROOT = Path(__file__).parent
DIAGNOSTIC_DIR = ROOT / 'diagnostic'

class Colors:
    GRAY = '\033[90m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'

def color(msg, color):
    return f'{color}{msg}\033[0m'

def list_modules():
    print("Available modules:")
    for module in MODULES:
        print(f"- {module.name}")

def validate_modules(names):
    valid_names = {m.name for m in MODULES}
    not_found = set(names) - valid_names
    return not_found, valid_names

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build script')
    parser.add_argument('--module', type=str, help='Comma-separated list of modules to build')
    parser.add_argument('--list-modules', action='store_true', help='List available modules')
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    if args.list_modules:
        list_modules()
        exit(0)

    if args.module == 'all':
        selected = MODULES
    else:
        names = [n.strip() for n in args.module.split(',')]
        not_found, valid_names = validate_modules(names)
        if not_found:
            print(f'  {color("✗ Unknown modules:", Colors.RED)} {', '.join(not_found)}')
            print(f'    Available: {', '.join(valid_names)}')
            exit(1)
        selected = [m for m in MODULES if m.name in names]

    if not selected:
        print(f'  No modules selected.')
        exit(0)

    if args.clean:
        print(f'\n  {color("Cleaning build artifacts...", Colors.YELLOW)}')
        for module in selected:
            clean_module(module, args.verbose)

        diagnostic_artifacts = [ROOT / 'build.logd']
        if DIAGNOSTIC_DIR.exists():
            diagnostic_artifacts.extend(DIAGNOSTIC_DIR.glob('build-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f].logd'))
            diagnostic_artifacts.extend(DIAGNOSTIC_DIR.glob('build-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-part*.logd'))
            diagnostic_artifacts.extend(DIAGNOSTIC_DIR.glob('build-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f].json'))
            diagnostic_artifacts.extend(DIAGNOSTIC_DIR.glob('build-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-metadata.json'))
        for artifact in diagnostic_artifacts:
            if artifact.exists():
                if artifact.is_dir():
                    shutil.rmtree(artifact)
                else:
                    artifact.unlink()
                print(f'  {color("▸", Colors.YELLOW)} Removed {artifact.relative_to(ROOT)}')
        print(f'\n  {color("Clean complete.", Colors.GREEN)}')
        exit(0)
