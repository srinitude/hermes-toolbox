"""Credential-key recognition with public placeholder exemptions."""
from __future__ import annotations

import ast
import re

CREDENTIAL_KEYS = {
    'apikey', 'accesstoken', 'refreshtoken', 'password', 'secret',
    'awssecretaccesskey', 'authorization', 'authorizationheader', 'authheader',
    'credential', 'cookie', 'privatekey',
}
PLACEHOLDER_MARKERS = {
    'changeme', 'dummy', 'example', 'placeholder', 'redacted', 'sample',
}
PLACEHOLDER_WORDS = PLACEHOLDER_MARKERS | {
    'a', 'api', 'ask', 'credential', 'here', 'is', 'key', 'me', 'password',
    'please', 'replace', 'secret', 'test', 'this', 'token', 'user', 'value', 'your',
}
PRIVATE_KEY_RE = re.compile(
    r'-----BEGIN (?:(?:OPENSSH|RSA|EC|DSA|ENCRYPTED) )?PRIVATE KEY-----'
)
ASSIGNMENT_RE = re.compile(
    r'["\']?(?P<key>[A-Z_][A-Z0-9_-]*)["\']?\s*[:=]\s*'
    r'(?P<value>""".*?"""|\'\'\'.*?\'\'\'|"[^"\n]*"|\'[^\'\n]*\'|'
    r'\$\{[^}\n]+\}|<[^>\n]+>|\[[A-Z][A-Z0-9_-]*\]|[^\s,#}\n]+)',
    re.IGNORECASE | re.DOTALL,
)


def credential_key(value: str) -> bool:
    normalized = re.sub(r'[_-]', '', value).casefold()
    return (normalized in CREDENTIAL_KEYS
            or normalized.endswith(
                ('apikey', 'password', 'secret', 'secretkey', 'secretaccesskey',
                 'authorization', 'authorizationheader', 'cookie', 'privatekey'))
            or normalized.endswith('token') and normalized != 'token')


def public_placeholder_credential(value: str) -> bool:
    normalized = value.strip().strip('"\'').strip()
    if re.fullmatch(r'\$\{[A-Za-z_][A-Za-z0-9_]*\}', normalized):
        return True
    if normalized.startswith('<') and normalized.endswith('>'):
        inner = normalized[1:-1]
        words = [word for word in re.split(r'[^a-z0-9]+', inner.casefold()) if word]
        return bool(words) and set(words) <= PLACEHOLDER_WORDS
    words = [word for word in re.split(r'[^a-z0-9]+', normalized.casefold()) if word]
    markers = set(words) & PLACEHOLDER_MARKERS
    explicit_your_value = {'your', 'here'}.issubset(words)
    return bool(words) and set(words) <= PLACEHOLDER_WORDS and bool(
        markers or explicit_your_value or words == ['ask', 'user'])


def sensitive_credential(value: object) -> bool:
    if not isinstance(value, str):
        return value not in (None, False)
    normalized = value.strip().strip('"\'').strip()
    return bool(normalized) and not public_placeholder_credential(normalized)


def _target_names(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Attribute):
        return [target.attr]
    if (isinstance(target, ast.Subscript)
            and isinstance(target.slice, ast.Constant)
            and isinstance(target.slice.value, str)):
        return [target.slice.value]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for item in target.elts for name in _target_names(item)]
    return []


def _target_values(target: ast.expr, value: ast.expr) -> list[tuple[str, ast.expr]]:
    if (isinstance(target, (ast.Tuple, ast.List))
            and isinstance(value, (ast.Tuple, ast.List))
            and len(target.elts) == len(value.elts)):
        return [pair for item, item_value in zip(target.elts, value.elts)
                for pair in _target_values(item, item_value)]
    return [(name, value) for name in _target_names(target)]


def _assignments(node: ast.AST) -> list[tuple[str, ast.expr]]:
    if isinstance(node, ast.Assign):
        return [pair for target in node.targets
                for pair in _target_values(target, node.value)]
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return _target_values(node.target, node.value)
    if isinstance(node, ast.AugAssign):
        return _target_values(node.target, node.value)
    if isinstance(node, ast.NamedExpr):
        return _target_values(node.target, node.value)
    return []


def _structured_assignments(node: ast.AST) -> list[tuple[str, ast.expr]]:
    if isinstance(node, ast.Dict):
        return [(key.value, value) for key, value in zip(node.keys, node.values)
                if isinstance(key, ast.Constant) and isinstance(key.value, str)]
    if isinstance(node, ast.Call):
        pairs = [(item.arg, item.value) for item in node.keywords if item.arg]
        if (isinstance(node.func, ast.Name) and node.func.id == 'setattr'
                and len(node.args) >= 3 and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)):
            pairs.append((node.args[1].value, node.args[2]))
        return pairs
    return []


def _static_string(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Constant) and isinstance(node.value, bytes):
        return node.value.decode('utf-8', errors='replace')
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _static_string(node.left), _static_string(node.right)
        return left + right if left is not None and right is not None else None
    if isinstance(node, ast.JoinedStr):
        values = [_static_string(value) for value in node.values]
        if any(value is None for value in values):
            return None
        return ''.join(value or '' for value in values)
    return None


def python_credential_assignment(text: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        pairs = _assignments(node) + _structured_assignments(node)
        for name, value in pairs:
            resolved = _static_string(value)
            if credential_key(name) and resolved is not None and sensitive_credential(resolved):
                return True
    return False


def private_key_block(text: str) -> bool:
    return bool(PRIVATE_KEY_RE.search(text))


def credential_assignment(text: str) -> bool:
    return (private_key_block(text)
            or any(credential_key(match.group('key'))
                   and sensitive_credential(match.group('value'))
                   for match in ASSIGNMENT_RE.finditer(text)))
