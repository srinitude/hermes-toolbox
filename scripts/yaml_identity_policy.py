"""Cycle-safe decoded YAML scalar contexts for privacy validation."""
from __future__ import annotations

import base64
import binascii

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

from credential_policy import credential_key

DecodedScalar = tuple[str, int, bool, bool]
BINARY_TAG = 'tag:yaml.org,2002:binary'


def _scalar_value(node: ScalarNode) -> str:
    if node.tag != BINARY_TAG:
        return str(node.value)
    try:
        payload = base64.b64decode(''.join(str(node.value).split()), validate=False)
    except (binascii.Error, ValueError, TypeError):
        return str(node.value)
    return payload.decode('utf-8', errors='ignore')


def _mapping_values(node: MappingNode, active: set[int]) -> list[DecodedScalar]:
    values = []
    for key, value in node.value:
        values.extend(_walk(key, active))
        key_text = _scalar_value(key) if isinstance(key, ScalarNode) else ''
        values.extend(_walk(value, active, key_text.casefold() == 'author',
                            credential_key(key_text)))
    return values


def _walk(node: object, active: set[int], author: bool = False,
          credential: bool = False) -> list[DecodedScalar]:
    if id(node) in active:
        return []
    if isinstance(node, ScalarNode):
        return [(_scalar_value(node), node.start_mark.line + 1, author, credential)]
    active.add(id(node))
    if isinstance(node, SequenceNode):
        values = [item for child in node.value
                  for item in _walk(child, active, author, credential)]
    elif isinstance(node, MappingNode):
        values = _mapping_values(node, active)
    else:
        values = []
    active.remove(id(node))
    return values


def decoded_yaml_scalars(text: str) -> list[DecodedScalar] | None:
    try:
        yaml.safe_load(text)
        root = yaml.compose(text, Loader=yaml.SafeLoader)
    except (yaml.YAMLError, TypeError, ValueError, OverflowError):
        return None
    return _walk(root, set()) if root is not None else []
