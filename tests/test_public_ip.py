import io
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
import public_ip


class PublicIPTests(unittest.TestCase):
    def test_only_public_ipv4(self):
        self.assertEqual(public_ip.public_ipv4(' 8.8.8.8\n'), '8.8.8.8')
        for value in ('127.0.0.1', '10.0.0.1', '192.168.1.1', '::1', 'invalid'):
            with self.assertRaises(ValueError):
                public_ip.public_ipv4(value)

    def test_https_fallback(self):
        with patch('public_ip.socket.socket', side_effect=OSError), patch('public_ip.urllib.request.urlopen', return_value=io.BytesIO(b'8.8.4.4\n')):
            self.assertEqual(public_ip.detect(), '8.8.4.4')

    def test_lookup_failure_is_explicit(self):
        with patch('public_ip.socket.socket', side_effect=OSError), patch('public_ip.urllib.request.urlopen', side_effect=OSError):
            with self.assertRaisesRegex(ValueError, '--host'):
                public_ip.detect()
