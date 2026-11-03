import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import server

RESULT = {"report": "r", "feedback": "f", "score": 9.0}


class TestServer(unittest.TestCase):
    def setUp(self):
        server._hits.clear()
        self.client = TestClient(server.app)

    def test_empty_and_overlong_topics_are_rejected(self):
        self.assertEqual(self.client.post("/research", json={"topic": "  "}).status_code, 400)
        long_topic = "x" * (server.MAX_TOPIC_CHARS + 1)
        self.assertEqual(self.client.post("/research", json={"topic": long_topic}).status_code, 400)

    def test_errors_do_not_leak_exception_text(self):
        with patch("server._run", side_effect=RuntimeError("secret api key abc")):
            response = self.client.post("/research", json={"topic": "ai"})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret", response.text)

    def test_rate_limit(self):
        with patch("server._run", return_value=RESULT):
            codes = [
                self.client.post("/research", json={"topic": "ai"}).status_code
                for _ in range(server.RATE_LIMIT_PER_MINUTE + 1)
            ]
        self.assertEqual(codes[-1], 429)
        self.assertTrue(all(c == 200 for c in codes[:-1]))

    def test_busy_server_returns_503(self):
        slots = [server._run_slots.acquire() for _ in range(server.MAX_CONCURRENT_RUNS)]
        try:
            response = self.client.post("/research", json={"topic": "ai"})
        finally:
            for _ in slots:
                server._run_slots.release()
        self.assertEqual(response.status_code, 503)

    def test_job_lifecycle(self):
        def fake_run(topic, on_progress=None):
            on_progress("writing")
            return RESULT

        with patch("server._run", side_effect=fake_run):
            job_id = self.client.post("/jobs", json={"topic": "ai"}).json()["job_id"]
            for _ in range(50):
                job = self.client.get(f"/jobs/{job_id}").json()
                if job["status"] != "running":
                    break
                time.sleep(0.05)
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["result"], RESULT)
        self.assertEqual(self.client.get("/jobs/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main()
