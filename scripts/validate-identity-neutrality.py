#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
validator_path = REPO / 'scripts' / 'validate-public-safety.py'
spec = importlib.util.spec_from_file_location('public_safety_validator', validator_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

errors = module.validate()
if errors:
    print('Identity-neutrality validation failed:', file=sys.stderr)
    for err in errors:
        print(f'- {err}', file=sys.stderr)
    raise SystemExit(1)
print('Identity-neutrality validation passed.')
