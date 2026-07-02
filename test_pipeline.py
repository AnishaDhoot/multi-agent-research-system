import unittest
from unittest.mock import patch, MagicMock
from pipeline import research_pipeline

class TestPipeline(unittest.TestCase):
    
    @patch('pipeline.build_search_agent')
    @patch('pipeline.build_reader_agent')
    def test_research_pipeline(self, mock_build_reader, mock_build_search):
        # Mock search agent output matching langgraph react agent
        mock_search_agent = MagicMock()
        mock_search_msg = MagicMock()
        mock_search_msg.content = "Mocked search results from https://example.com"
        mock_search_agent.invoke.return_value = {"messages": [mock_search_msg]}
        mock_build_search.return_value = mock_search_agent
        
        # Mock reader agent
        mock_reader_agent = MagicMock()
        mock_reader_msg = MagicMock()
        mock_reader_msg.content = "Mocked scraped content from example.com"
        mock_reader_agent.invoke.return_value = {"messages": [mock_reader_msg]}
        mock_build_reader.return_value = mock_reader_agent
        
        # Mock writer and critic directly
        with patch('pipeline.writer_chain') as mock_writer, patch('pipeline.critic_chain') as mock_critic:
            mock_writer.invoke.return_value = "Mocked report"
            mock_critic.invoke.return_value = "Mocked feedback"
            
            try:
                result = research_pipeline("Mock Topic")
                self.assertIsNotNone(result)
                self.assertIn("search_results", result)
                self.assertIn("scraped_content", result)
                self.assertIn("report", result)
                self.assertIn("feedback", result)
                
            except Exception as e:
                self.fail(f"research_pipeline() raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
