import os
import unittest
from public_interface.bunny_signer import get_secure_embed_url

class TestBunnySigner(unittest.TestCase):
    def test_unsigned_when_no_key(self):
        # Ensure we return a non-signed embed url when no key is present
        os.environ.pop('BUNNY_SECURITY_KEY', None)
        url = get_secure_embed_url(library_id=389178, video_id='abc123', security_key=None)
        self.assertIn('embed/389178/abc123', url)

    def test_signed_when_key_present(self):
        # Provide a fake key and expect token in the URL
        fake_key = 'fake-uuid-key'
        # Use deterministic expires timestamp so signature is predictable
        expires_ts = 1700000000
        url = get_secure_embed_url(library_id=389178, video_id='abc123', security_key=fake_key, expires_ts=expires_ts)
        self.assertIn('token=', url)
        self.assertIn('expires=1700000000', url)

    def test_token_matches_expected_hmac(self):
        # Verify the token value matches HMAC-SHA256 over canonical string using urlsafe base64
        fake_key = 'my-secret-key'
        expires_ts = 1700000000
        url = get_secure_embed_url(library_id=111, video_id='videoX', security_key=fake_key, expires_ts=expires_ts)

        # Extract token from url
        import urllib.parse as up
        q = up.urlparse(url).query
        params = dict([p.split('=',1) for p in q.split('&')])
        token = params.get('token')

        # Compute expected token
        import hmac, hashlib, base64
        message = f"{111}/videoX/{expires_ts}".encode('utf-8')
        sig = hmac.new(fake_key.encode('utf-8'), message, hashlib.sha256).digest()
        expected = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')

        self.assertEqual(token, expected)

if __name__ == '__main__':
    unittest.main()
