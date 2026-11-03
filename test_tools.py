import unittest
from unittest.mock import MagicMock, patch

import tools


def _response(body=b"<html><nav>menu</nav><p>Hello world</p></html>", redirect_to=None):
    r = MagicMock()
    r.is_redirect = redirect_to is not None
    r.headers = {"Location": redirect_to} if redirect_to else {}
    r.content = body
    return r


class TestIsSafeUrl(unittest.TestCase):
    def test_rejects_bad_schemes_and_private_hosts(self):
        self.assertFalse(tools.is_safe_url("file:///etc/passwd"))
        self.assertFalse(tools.is_safe_url("ftp://example.com"))
        self.assertFalse(tools.is_safe_url("http://127.0.0.1/admin"))
        self.assertFalse(tools.is_safe_url("http://169.254.169.254/latest/meta-data"))
        self.assertFalse(tools.is_safe_url("http://[::1]/"))

    def test_accepts_public_ip(self):
        self.assertTrue(tools.is_safe_url("https://8.8.8.8/"))


class TestFetchText(unittest.TestCase):
    @patch("tools.is_safe_url", return_value=True)
    @patch("tools.requests.get")
    def test_extracts_text_and_strips_nav(self, get, _):
        get.return_value = _response()
        self.assertEqual(tools.fetch_text("https://example.com"), "Hello world")

    @patch("tools.requests.get")
    def test_unsafe_url_is_never_requested(self, get):
        with self.assertRaises(ValueError):
            tools.fetch_text("http://127.0.0.1/")
        get.assert_not_called()

    @patch("tools.is_safe_url", side_effect=lambda u: "internal" not in u)
    @patch("tools.requests.get")
    def test_redirect_to_unsafe_host_is_blocked(self, get, _):
        get.return_value = _response(redirect_to="http://internal/secret")
        with self.assertRaises(ValueError):
            tools.fetch_text("https://example.com")
        self.assertEqual(get.call_count, 1)


class TestSearchSources(unittest.TestCase):
    def test_maps_tavily_results(self):
        client = MagicMock()
        client.search.return_value = {"results": [{"title": "T", "url": "https://x", "content": "c"}]}
        with patch("tools._get_tavily", return_value=client):
            self.assertEqual(
                tools.search_sources("q"), [{"title": "T", "url": "https://x", "snippet": "c"}]
            )

    def test_search_retries_then_succeeds(self):
        client = MagicMock()
        client.search.side_effect = [RuntimeError("429"), {"results": []}]
        with patch("tools._get_tavily", return_value=client), patch("tools.time.sleep"):
            self.assertEqual(tools.search_sources("q"), [])
        self.assertEqual(client.search.call_count, 2)

    def test_search_gives_up_after_max_attempts(self):
        client = MagicMock()
        client.search.side_effect = RuntimeError("down")
        with patch("tools._get_tavily", return_value=client), patch("tools.time.sleep"):
            with self.assertRaises(RuntimeError):
                tools.search_sources("q")
        self.assertEqual(client.search.call_count, tools.SEARCH_ATTEMPTS)


if __name__ == "__main__":
    unittest.main()
