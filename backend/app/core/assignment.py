import hashlib


def deterministic_bucket(key: str) -> float:
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
    value = int(digest[:8], 16)
    return (value % 10000) / 10000
