import base64
import subprocess
import tempfile
import unittest
from pathlib import Path

from entity_github_app.github_api import DEFAULT_OPENSSL, create_app_jwt


def b64decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


class JwtTests(unittest.TestCase):
    @unittest.skipUnless(DEFAULT_OPENSSL.is_file(), "portable OpenSSL unavailable")
    def test_rs256_signature_verifies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            private_key = root / "private.pem"
            public_key = root / "public.pem"
            subprocess.run([str(DEFAULT_OPENSSL), "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(private_key)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([str(DEFAULT_OPENSSL), "pkey", "-in", str(private_key), "-pubout", "-out", str(public_key)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            token = create_app_jwt("12345", private_key)
            header, payload, signature = token.split(".")
            sig_file = root / "sig.bin"
            msg_file = root / "msg.bin"
            sig_file.write_bytes(b64decode(signature))
            msg_file.write_bytes(f"{header}.{payload}".encode("ascii"))
            result = subprocess.run([str(DEFAULT_OPENSSL), "dgst", "-sha256", "-verify", str(public_key), "-signature", str(sig_file), str(msg_file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0, result.stderr.decode())


if __name__ == "__main__":
    unittest.main()
