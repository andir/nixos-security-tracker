"""
GitHubEvent signature verification functions

This module provides those functions required to verify the webhooks we are
receiving. GitHub sends a SHA1 and SHA256 based HMAC with each of the events.
The shared key that has been agreed upon (out out bands) serves as key for the
HMAC.

This module should be self-contained as much as possible as we are using it
within the VM test to generate fake events with valid signatures.
"""
import hashlib
import hmac


def compute_github_hmac(key: bytes, body: bytes) -> str:
    return "sha1-" + hmac.new(key, body, hashlib.sha1).hexdigest()


def verify_github_signature(key: bytes, signature: str, body: bytes):
    expected_hmac = compute_github_hmac(key, body)
    return hmac.compare_digest(expected_hmac, signature)
