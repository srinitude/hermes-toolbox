#!/usr/bin/env python3
"""Public-safety validator. Thin CLI over safety_checks and package_checks."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_checks import check_repo_package_manifests, check_repo_personalities
from public_manifest import fingerprint_errors
from safety_checks import validate_text_safety


def validate(repo: Path = REPO) -> list[str]:
    errors = validate_text_safety(repo)
    errors.extend(check_repo_package_manifests(repo))
    errors.extend(check_repo_personalities(repo))
    errors.extend(fingerprint_errors(repo))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    errors = validate()
    if args.json:
        print(json.dumps({'ok': not errors, 'errors': errors}, indent=2))
    elif errors:
        print('Public-safety validation failed:', file=sys.stderr)
        for err in errors:
            print(f'- {err}', file=sys.stderr)
    else:
        print('Public-safety validation passed.')
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
