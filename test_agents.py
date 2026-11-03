import os
import unittest
from unittest.mock import patch

# Import the methods to test
from agents import get_llm, build_search_agent, build_reader_agent, writer_chain, critic_chain

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

    def test_build_search_agent(self):
        try:
            agent = build_search_agent()
            self.assertIsNotNone(agent)
            self.assertTrue(hasattr(agent, "invoke"))
        except Exception as e:
            self.fail(f"build_search_agent() failed with exception: {e}")

    def test_build_reader_agent(self):
        try:
            agent = build_reader_agent()
            self.assertIsNotNone(agent)
            self.assertTrue(hasattr(agent, "invoke"))
        except Exception as e:
            self.fail(f"build_reader_agent() failed with exception: {e}")

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
        from langchain_core.language_models import FakeListChatModel
        # Mock the LLM to prevent actual API calls
        fake_llm = FakeListChatModel(responses=["Mocked Response"])
        mock_get_llm.return_value = fake_llm

        inputs = {"report": "Mock research report."}
        try:
            critic_chain._chain = None  # reset to force re-init
            result = critic_chain.invoke(inputs)
            self.assertIsNotNone(result)
            self.assertEqual(result, "Mocked Response")
        except Exception as e:
            self.fail(f"critic_chain.invoke() failed with exception: {e}")

if __name__ == '__main__':
    unittest.main()
