"""Fixture plugin that registers one bundled skill for real-runtime tests."""
from __future__ import annotations

from pathlib import Path


def register(ctx) -> None:
    ctx.register_skill(
        'demo',
        Path(__file__).resolve().parent / 'skills' / 'demo' / 'SKILL.md',
        description='Demo bundled skill fixture.',
    )
