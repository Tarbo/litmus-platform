import hashlib
from typing import Any


def deterministic_bucket(key: str) -> float:
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
    value = int(digest[:16], 16)
    return value / float(0xFFFFFFFFFFFFFFFF)


def unit_bucket(experiment_id: str, unit_id: str, salt: str, namespace: str) -> float:
    return deterministic_bucket(f'{experiment_id}:{unit_id}:{salt}:{namespace}')


def _coerce_version_parts(value: Any) -> list[int]:
    text = str(value)
    parts: list[int] = []
    for token in text.split('.'):
        if token.isdigit():
            parts.append(int(token))
        else:
            break
    return parts


def _compare_versions(left: Any, right: Any) -> int:
    l_parts = _coerce_version_parts(left)
    r_parts = _coerce_version_parts(right)
    size = max(len(l_parts), len(r_parts))
    l_parts += [0] * (size - len(l_parts))
    r_parts += [0] * (size - len(r_parts))
    if l_parts < r_parts:
        return -1
    if l_parts > r_parts:
        return 1
    return 0


def attribute_matches_rule(value: Any, rule: Any) -> bool:
    if isinstance(rule, dict):
        for operator, expected in rule.items():
            if operator == 'in':
                if value not in (expected or []):
                    return False
            elif operator == 'eq':
                if value != expected:
                    return False
            elif operator == 'neq':
                if value == expected:
                    return False
            elif operator == 'gte':
                if _compare_versions(value, expected) < 0:
                    return False
            elif operator == 'lte':
                if _compare_versions(value, expected) > 0:
                    return False
            else:
                return False
        return True
    if isinstance(rule, list):
        return value in rule
    return value == rule


def matches_targeting(targeting: dict, attributes: dict[str, Any]) -> bool:
    if not targeting:
        return True
    for key, rule in targeting.items():
        if key not in attributes:
            return False
        if not attribute_matches_rule(attributes[key], rule):
            return False
    return True
