"""Synthetic credential payloads shared by package-safety regressions."""
from __future__ import annotations


PYTHON_CASE = ('settings.api_key = "abcdef0123456789abcdef"\n'
               'settings.api_key = b"synthetic-private-value-2026"\n'
               'settings.api_key = f"abcdef0123456789abcdef"\n'
               'settings.api_key = "abcdef0123" + "456789abcdef"\n'
               'config = {"client_secret": "abcdef0123456789"}\n'
               'configure(session_cookie="abcdef0123456789")\n'
               'setattr(settings, "password", "S3cure!9")\n')


def variant_case(cookie: str, password: str, token: str) -> str:
    return (f'{cookie}: abcdef0123456789abcdef\n'
            f'{password}: S3cure!9\n'
            f'{password}: Correct-Horse-sample-Battery-2026\n'
            f'{password}: ${{PASSWORD:-Correct-Horse-Battery-2026}}\n'
            f'{password}: <Correct-Horse-Battery-2026>\n'
            f'{token}: abcdefsample0123456789\n')


def credential_cases() -> dict[str, str]:
    key = 'api' + '_key'
    escaped = 'api' + '\\u005fkey'
    pwd_field = 'pass' + 'word'
    aws_key = 'aws_' + 'secret_access_key'
    client_key = 'client_' + 'secret_key'
    auth_key = 'authorization' + '_header'
    cookie_key = 'session_' + 'cookie'
    token_key = 'github_' + 'token'
    return {
        'quoted.json': f'{{"{key}":"abcdef0123456789abcdef"}}\n',
        'escaped.json': f'{{"{escaped}":"abcdef0123456789abcdef"}}\n',
        'fenced.md': f'```json\n{{"{escaped}":"abcdef0123456789abcdef"}}\n```\n',
        'tilde.md': f'~~~json\n{{"{escaped}":"abcdef0123456789abcdef"}}\n~~~\n',
        'quad.md': f'````json\n{{"{escaped}":"abcdef0123456789abcdef"}}\n````\n',
        'info.md': f'````json title="credential example"\n{{"{escaped}":"abcdef0123456789abcdef"}}\n````\n',
        'tilde-info.md': f'~~~~json title="credential example"\n{{"{escaped}":"abcdef0123456789abcdef"}}\n~~~~\n',
        'aws.json': f'{{"{aws_key}":"abcdefghijklmnopqrstuvwxyz0123456789ABCD"}}\n',
        'client.json': f'{{"{client_key}":"abcdef0123456789abcdef"}}\n',
        'authorization.yaml': f'{auth_key}: "Bearer abcdef0123456789abcdef"\n',
        'variants.yaml': variant_case(cookie_key, pwd_field, token_key),
        'attribute.py': PYTHON_CASE,
        'config.toml': f'{key} = """abcdef0123456789abcdef"""\n',
        'block.yaml': f'{key}: >\n  abcdef0123456789abcdef\n',
        'phrase.json': f'{{"{pwd_field}":"Correct Horse Battery Staple! 2026"}}\n',
    }
