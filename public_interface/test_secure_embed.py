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
        url = get_secure_embed_url(library_id=389178, video_id='abc123', security_key=fake_key)
        self.assertIn('token=', url)
        self.assertIn('expires=', url)

if __name__ == '__main__':
    unittest.main()
