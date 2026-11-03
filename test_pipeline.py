import unittest
from unittest.mock import patch

import pipeline
from agents import CriticReview
from pipeline import research_pipeline

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
        reviews = [CriticReview(score=s, strengths=["x"], improvements=["y"], verdict="v") for s in scores]
        with patch("pipeline.plan_topic", return_value=["q1"]), \
             patch("pipeline.search_sources", return_value=SOURCES), \
             patch("pipeline.fetch_text_robust", side_effect=_fetch), \
             patch("pipeline.writer_chain") as writer, \
             patch("pipeline.revision_chain") as revision, \
             patch("pipeline.critic_chain") as critic:
            writer.invoke.return_value = "draft"
            revision.invoke.return_value = "revised"
            critic.invoke.side_effect = reviews
            return research_pipeline("topic"), writer, revision, critic

    def test_critic_failure_keeps_report(self):
        with patch("pipeline.plan_topic", return_value=["q1"]), \
             patch("pipeline.search_sources", return_value=SOURCES), \
             patch("pipeline.fetch_text_robust", return_value="text"), \
             patch("pipeline.writer_chain") as writer, \
             patch("pipeline.critic_chain") as critic:
            writer.invoke.return_value = "draft"
            critic.invoke.side_effect = RuntimeError("bad output")
            state = research_pipeline("topic")
        self.assertTrue(state["report"].startswith("draft"))
        self.assertIsNone(state["score"])
        self.assertEqual(state["revisions"], 0)

    def test_critic_review_format(self):
        review = CriticReview(score=7.5, strengths=["a"], improvements=["b"], verdict="ok")
        self.assertIn("Score: 7.5/10", review.format())
        with self.assertRaises(ValueError):
            CriticReview(score=11, strengths=[], improvements=[], verdict="")

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

    def test_multi_question_search_dedupes_and_interleaves(self):
        results = {
            "q1": [{"title": "A", "url": "u1", "snippet": ""}, {"title": "B", "url": "u2", "snippet": ""}],
            "q2": [{"title": "A", "url": "u1", "snippet": ""}, {"title": "C", "url": "u3", "snippet": ""}],
        }
        with patch("pipeline.search_sources", side_effect=lambda q, max_results: results[q]):
            urls = [s["url"] for s in pipeline._search_all(["q1", "q2"])]
        self.assertEqual(urls, ["u1", "u2", "u3"])

    def test_failed_search_for_one_question_is_skipped(self):
        def search(q, max_results):
            if q == "bad":
                raise RuntimeError("boom")
            return [{"title": "A", "url": "u1", "snippet": ""}]

        with patch("pipeline.search_sources", side_effect=search):
            self.assertEqual(len(pipeline._search_all(["bad", "good"])), 1)

    def test_uncited_sources_are_dropped_and_citations_renumbered(self):
        three = SOURCES + [{"title": "C", "url": "https://c.example", "snippet": "snippet c"}]
        with patch("pipeline.plan_topic", return_value=["q1"]), \
             patch("pipeline.search_sources", return_value=three), \
             patch("pipeline.fetch_text_robust", return_value="text"), \
             patch("pipeline.writer_chain") as writer, \
             patch("pipeline.critic_chain") as critic:
            writer.invoke.return_value = "Fact [1]. Another [1, 3]."
            critic.invoke.return_value = CriticReview(score=9, strengths=[], improvements=[], verdict="v")
            state = research_pipeline("topic")
        self.assertIn("Fact [1]. Another [1, 2].", state["report"])
        self.assertIn("[2] C - https://c.example", state["report"])
        self.assertNotIn("b.example", state["report"])

    def test_trust_ranking_prefers_authoritative_domains(self):
        self.assertGreater(pipeline._trust("https://www.nih.gov/x"), pipeline._trust("https://shop.example.com"))
        self.assertLess(pipeline._trust("https://medium.com/x"), 0)


if __name__ == "__main__":
    unittest.main()
