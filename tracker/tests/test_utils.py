from tracker.utils import compute_github_hmac, verify_github_signature

shared_secret = b"00000000000"
signature = "sha1-76f675f5babc40e8cc64405dcaa9049541380c18"


def test_compute_github_hmac():
    hmac = compute_github_hmac(shared_secret, "test".encode())
    assert hmac == signature


def test_verify_github_signature():
    assert verify_github_signature(shared_secret, signature, "test".encode())
