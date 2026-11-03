import os
import unittest
from unittest.mock import MagicMock, patch

import agents
# Import the methods to test
from agents import CriticReview, ResearchPlan, plan_topic, get_llm, writer_chain, critic_chain

class TestAgents(unittest.TestCase):
    def setUp(self):
        # Constructing the Gemini client only needs a key to be present, not valid.
        patcher = patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_llm(self):
        try:
            llm = get_llm()
            self.assertIsNotNone(llm)
            # Check if it has expected methods
            self.assertTrue(hasattr(llm, "invoke"))
        except Exception as e:
            self.fail(f"get_llm() failed with exception: {e}")

    def test_get_llm_selects_provider(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch('agents.LLM_PROVIDER', 'groq'), patch('agents.LLM_MODEL', None):
                llm = get_llm()
        self.assertEqual(type(llm).__name__, "ChatGroq")
        self.assertEqual(llm.model_name, "openai/gpt-oss-120b")
        with patch('agents.LLM_PROVIDER', 'nope'):
            with self.assertRaises(ValueError):
                get_llm()

    def test_groq_uses_json_schema_structured_output(self):
        fake_llm = MagicMock()
        with patch('agents.get_llm', return_value=fake_llm):
            with patch('agents.LLM_PROVIDER', 'groq'):
                agents.structured_llm(CriticReview)
            fake_llm.with_structured_output.assert_called_once_with(CriticReview, method="json_schema")

    def test_plan_topic_falls_back_to_topic_on_failure(self):
        with patch('agents.get_llm', side_effect=RuntimeError("no llm")):
            self.assertEqual(plan_topic("AI"), ["AI"])

    def test_plan_topic_caps_and_cleans_questions(self):
        plan = ResearchPlan(questions=["a", " ", "b", "c", "d", "e"])
        with patch('agents.planner_prompt') as prompt:
            prompt.__or__.return_value.invoke.return_value = plan
            self.assertEqual(plan_topic("AI"), ["a", "b", "c", "d"])

    @patch('agents.get_llm')
    def test_writer_chain(self, mock_get_llm):
        from langchain_core.language_models import FakeListChatModel
        # Mock the LLM to prevent actual API calls
        fake_llm = FakeListChatModel(responses=["Mocked Response"])
        mock_get_llm.return_value = fake_llm

        inputs = {"topic": "AI", "research": "Some research data"}
        try:
            # Recreate writer_chain local chain to ensure mock is used, 
            # or just test initialization
            writer_chain._chain = None  # reset to force re-init
            result = writer_chain.invoke(inputs)
            self.assertIsNotNone(result)
            self.assertEqual(result, "Mocked Response")
        except Exception as e:
            self.fail(f"writer_chain.invoke() failed with exception: {e}")

    @patch('agents.get_llm')
    def test_critic_chain(self, mock_get_llm):
        review = CriticReview(score=6, strengths=["s"], improvements=["i"], verdict="v")
        structured = MagicMock()
        structured.invoke.return_value = review
        fake_llm = MagicMock()
        fake_llm.with_structured_output.return_value = structured
        mock_get_llm.return_value = fake_llm

        try:
            critic_chain._chain = None  # reset to force re-init
            result = critic_chain.invoke({"report": "Mock research report."})
            fake_llm.with_structured_output.assert_called_once_with(CriticReview)
        except Exception as e:
            self.fail(f"critic_chain.invoke() failed with exception: {e}")

if __name__ == '__main__':
    unittest.main()
