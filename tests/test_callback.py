import threading
import unittest
import urllib.request

from entity_github_app.callback_server import CallbackHandler
from http.server import ThreadingHTTPServer


class CallbackTests(unittest.TestCase):
    def test_callback_returns_200(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), CallbackHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with urllib.request.urlopen(
                f"http://{host}:{port}/github/callback", timeout=3
            ) as response:
                body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn("ENTITY Evidence Bridge", body)
                self.assertIn("No user OAuth token", body)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
