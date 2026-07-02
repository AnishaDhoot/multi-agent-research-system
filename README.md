# Multi-Agent Research System

A sophisticated AI-powered research automation system that leverages multiple specialized agents to conduct comprehensive web research, synthesize findings, and generate detailed reports with built-in quality assessment.

## 🎯 Overview

This system implements a multi-agent architecture where each AI agent has a specific role in the research process:
- **Search Agent**: Discovers relevant information using web search
- **Reader Agent**: Deep-dives into content by scraping and analyzing specific URLs
- **Writer Agent**: Synthesizes research into structured, professional reports
- **Critic Agent**: Evaluates report quality and provides constructive feedback

The system is built with modern AI frameworks including LangChain, LangGraph, and Google Gemini, complemented by a sleek Next.js frontend for interactive research sessions.

## ✨ Features

- **Automated Research Pipeline**: End-to-end research automation from topic to final report
- **Multi-Agent Architecture**: Specialized agents for different research tasks
- **Real-time Web Search**: Integration with Tavily for up-to-date information retrieval
- **Intelligent Content Scraping**: BeautifulSoup-based web scraping with content cleaning
- **Quality Assessment**: Built-in critic agent for report evaluation
- **Modern Web Interface**: Next.js frontend with React and Tailwind CSS
- **RESTful API**: FastAPI backend for seamless integration
- **Comprehensive Testing**: Unit tests for agents and pipeline components
- **Lazy Loading**: Efficient LLM initialization to optimize resource usage

## 🏗️ Architecture

### Research Pipeline Flow

```
User Topic → Search Agent → Reader Agent → Writer Agent → Critic Agent → Final Report
                ↓               ↓              ↓              ↓
          Web Search    URL Scraping    Report Synthesis  Quality Check
```

### Component Overview

**Backend (Python)**
- `agents.py`: Defines all AI agents and chains using LangGraph and LangChain
- `pipeline.py`: Orchestrates the research workflow
- `tools.py`: Implements web search and URL scraping tools
- `server.py`: FastAPI server for API endpoints

**Frontend (Next.js)**
- React-based UI for interactive research
- Real-time progress tracking
- Beautiful, modern interface with animations

## 🛠️ Tech Stack

### Backend
- **LangChain**: AI framework for building LLM applications
- **LangGraph**: Agent orchestration and workflow management
- **Google Gemini**: Primary LLM (gemini-2.5-flash)
- **Tavily**: Web search API
- **FastAPI**: Modern Python web framework
- **BeautifulSoup4**: Web scraping and HTML parsing
- **Pydantic**: Data validation and settings management

### Frontend
- **Next.js 16**: React framework with server components
- **React 19**: UI library
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS 4**: Utility-first CSS framework
- **Framer Motion**: Animation library
- **Lucide React**: Icon library

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- Google Gemini API key
- Tavily API key

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/AnishaDhoot/multi-agent-research-system.git
cd multi-agent-research-system
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_google_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### Frontend Setup

1. **Navigate to the frontend directory**
```bash
cd aetheris-research-ui/aetheris-export
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment**
```bash
cp .env.local.example .env.local
```

Edit `.env.local` if needed (default backend URL is `http://localhost:8000`):
```env
PYTHON_BACKEND_URL=http://localhost:8000
```

## 🚀 Usage

### Running the Backend

Start the FastAPI server:
```bash
uvicorn server:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Running the Frontend

Start the Next.js development server:
```bash
cd aetheris-research-ui/aetheris-export
npm run dev
```

The UI will be available at `http://localhost:3000`

### Command Line Usage

You can also run the research pipeline directly from the command line:

```bash
python pipeline.py
```

Enter a research topic when prompted, and the system will:
1. Search for relevant information
2. Scrape the most relevant URL
3. Generate a comprehensive report
4. Provide quality assessment

### API Endpoints

#### Health Check
```http
GET /health
```

#### Research Request
```http
POST /research
Content-Type: application/json

{
  "topic": "artificial intelligence in healthcare"
}
```

**Response:**
```json
{
  "search_results": "...",
  "scraped_content": "...",
  "report": "...",
  "feedback": "..."
}
```

## 📁 Project Structure

```
multi-agent-research-system/
├── agents.py              # AI agent definitions and chains
├── pipeline.py            # Research workflow orchestration
├── tools.py               # Web search and scraping tools
├── server.py              # FastAPI server
├── requirements.txt       # Python dependencies
├── test_agents.py         # Agent unit tests
├── test_pipeline.py       # Pipeline integration tests
├── .env                   # Environment variables (not tracked)
├── .gitignore             # Git ignore rules
└── aetheris-research-ui/  # Next.js frontend
    └── aetheris-export/
        ├── app/           # Next.js app directory
        ├── package.json   # Node.js dependencies
        ├── .env.local     # Frontend environment variables
        └── SETUP.md       # Frontend setup guide
```

## 🧪 Testing

### Run all tests
```bash
python -m unittest test_agents.py test_pipeline.py
```

### Run specific test files
```bash
python -m unittest test_agents.py
python -m unittest test_pipeline.py
```

### Test Coverage
- `test_agents.py`: Tests LLM initialization, agent building, and chain execution
- `test_pipeline.py`: Tests the complete research pipeline with mocked agents

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key for LLM |
| `TAVILY_API_KEY` | Yes | Tavily API key for web search |
| `PYTHON_BACKEND_URL` | No | Backend URL (default: `http://localhost:8000`) |

### Agent Configuration

You can modify agent behavior in `agents.py`:
- **LLM Model**: Change `gemini-2.5-flash` to other supported models
- **Temperature**: Adjust creativity (0 = more deterministic, 1 = more creative)
- **Prompts**: Customize system prompts for each agent

### Tool Configuration

Modify search and scraping behavior in `tools.py`:
- **Max Results**: Adjust `max_results` in web_search
- **Content Length**: Change text truncation limits in scrape_url
- **Timeout**: Adjust request timeout for web scraping

## 🎨 Frontend Features

- **Interactive Research Interface**: Clean, modern UI for entering research topics
- **Real-time Progress**: Visual feedback during research pipeline execution
- **Report Display**: Formatted presentation of research findings
- **Quality Metrics**: Display of critic agent evaluation
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode**: Modern dark theme with smooth animations

## 🔍 How It Works

### 1. Search Agent
Uses Tavily's search API to find recent, reliable information about the research topic. Returns titles, URLs, and content snippets from the most relevant sources.

### 2. Reader Agent
Analyzes search results, selects the most relevant URL, and scrapes the content using BeautifulSoup. Removes scripts, styles, and navigation elements for clean text extraction.

### 3. Writer Agent
Synthesizes search results and scraped content into a structured research report with:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources

### 4. Critic Agent
Evaluates the generated report and provides:
- Quality score (X/10)
- Strengths
- Areas to improve
- One-line verdict

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **LangChain**: For the excellent AI framework
- **LangGraph**: For agent orchestration capabilities
- **Google**: For Gemini AI model
- **Tavily**: For web search API
- **Next.js**: For the React framework

## 📧 Contact

For questions or suggestions, please open an issue on GitHub or contact the maintainers.

## 🗺️ Roadmap

- [ ] Add more specialized agents (citation manager, fact-checker)
- [ ] Implement research history and saved reports
- [ ] Add export options (PDF, Markdown)
- [ ] Support for multiple LLM providers
- [ ] Advanced filtering and source selection
- [ ] Collaborative research features
- [ ] API rate limiting and authentication
- [ ] Docker containerization for easy deployment

---

**Built with ❤️ using modern AI technologies**
