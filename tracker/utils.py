import hashlib
import hmac


def compute_github_hmac(key: bytes, body: bytes) -> str:
    return "sha1-" + hmac.new(key, body, hashlib.sha1).hexdigest()


def verify_github_signature(key: bytes, signature: str, body: bytes):
    expected_hmac = compute_github_hmac(key, body)
    return hmac.compare_digest(expected_hmac, signature)
