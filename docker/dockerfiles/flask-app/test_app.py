import unittest

from app import app


class FlaskExampleTests(unittest.TestCase):
    def test_homepage_is_readable(self):
        response = app.test_client().get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hello from Flask in Docker!", response.data)

    def test_health_endpoint(self):
        response = app.test_client().get("/health")
        self.assertEqual(response.json, {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
