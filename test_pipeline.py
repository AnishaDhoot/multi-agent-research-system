import unittest
from unittest.mock import patch

import pipeline
from pipeline import _parse_score, research_pipeline

SOURCES = [
    {"title": "A", "url": "https://a.example", "snippet": "snippet a"},
    {"title": "B", "url": "https://b.example", "snippet": "snippet b"},
]


def _fetch(url):
    if "b.example" in url:
        raise ValueError("blocked")
    return "page text a"


class TestPipeline(unittest.TestCase):
    def _run(self, scores):
        feedbacks = [f"Score: {s}/10\n\nStrengths:\n- x" for s in scores]
        with patch("pipeline.search_sources", return_value=SOURCES), \
             patch("pipeline.fetch_text", side_effect=_fetch), \
             patch("pipeline.writer_chain") as writer, \
             patch("pipeline.revision_chain") as revision, \
             patch("pipeline.critic_chain") as critic:
            writer.invoke.return_value = "draft"
            revision.invoke.return_value = "revised"
            critic.invoke.side_effect = feedbacks
            return research_pipeline("topic"), writer, revision, critic

    def test_parse_score(self):
        self.assertEqual(_parse_score("Score: 7.5/10"), 7.5)
        self.assertEqual(_parse_score("Score: 9 / 10"), 9.0)
        self.assertIsNone(_parse_score("no score here"))

    def test_passing_report_is_not_revised(self):
        state, _, revision, _ = self._run([9])
        revision.invoke.assert_not_called()
        self.assertEqual(state["revisions"], 0)
        self.assertEqual(state["score"], 9.0)

    def test_low_score_triggers_revision_until_pass(self):
        state, _, revision, critic = self._run([5, 9])
        self.assertEqual(revision.invoke.call_count, 1)
        self.assertEqual(critic.invoke.call_count, 2)
        self.assertEqual(state["revisions"], 1)
        self.assertTrue(state["report"].startswith("revised"))

    def test_revisions_are_capped(self):
        state, _, revision, _ = self._run([3] * (pipeline.MAX_REVISIONS + 1))
        self.assertEqual(revision.invoke.call_count, pipeline.MAX_REVISIONS)
        self.assertEqual(state["revisions"], pipeline.MAX_REVISIONS)

    def test_sources_appended_and_scrape_failure_falls_back_to_snippet(self):
        state, writer, _, _ = self._run([9])
        self.assertIn("## Sources\n[1] A - https://a.example\n[2] B - https://b.example", state["report"])
        research = writer.invoke.call_args.args[0]["research"]
        self.assertIn("page text a", research)
        self.assertIn("snippet b", research)
        self.assertEqual([s["scraped"] for s in state["sources"]], [True, False])
        for key in ("search_results", "scraped_content", "report", "feedback"):
            self.assertIn(key, state)


if __name__ == "__main__":
    unittest.main()
