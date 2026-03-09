# Job-Searching & Auto-Applying AI Agent

An autonomous AI agent that finds, analyzes, and applies to jobs matching your CV using **Python**, **Ollama** (Local LLMs), **CrewAI** (Multi-agent orchestration), **FAISS** (Vector Search), and **Playwright** (Browser automation).

## 🚀 Features

- **CV Parsing**: Extracts skills and experience directly from your PDF CV.
- **Semantic Job Matching**: Uses `Sentence-Transformers` and `FAISS` to evaluate job descriptions against your CV using vector embeddings.
- **Local AI Analysis**: Utilizes `Ollama` (e.g., `qwen3.5:cloud`) to deeply analyze job relevance and generate a fit score entirely locally without requiring paid API keys like OpenAI.
- **Multi-Agent Orchestration**: Powered by `CrewAI`, dividing workloads between a Job Finder, Job Analyzer, and Application Submitter.
- **Automated LinkedIn Applications**: Uses `Playwright` infused with your authenticated session to navigate job portals and automatically complete "Easy Apply" applications.
- **Session Injection**: securely injects your active LinkedIn session to completely bypass bot-detecting login walls.

## 🛠️ Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) running locally with your desired model (e.g., `qwen3.5:cloud`)
- Supported OS: Linux / macOS / Windows

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/taherfarg/job-ai-agent.git
   cd job-ai-agent
   ```

2. **Set up a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

   *(Note: You can generate the `requirements.txt` based on the imports in the project if one is not yet provided).*

## ⚙️ Configuration

1. Place your CV in the `data/` folder (e.g., `data/TAHER FARG CV.pdf`).
2. Update `config.py`:
   - Set `CV_PATH` to point to your new CV file.
   - Set `LLM_MODEL` to your locally running Ollama model (e.g., `"qwen3.5:cloud"`).
   - Ensure you configure your target job URL (e.g., LinkedIn Jobs Search URL).

## 🔑 Authentication (Bypassing LinkedIn Walls)

To allow Playwright to apply for jobs on your behalf, you need to save an authenticated session.

1. Run the session saver script:
   ```bash
   python automation/save_session.py
   ```
2. A headed Chromium browser will open. Manually log into your LinkedIn account.
3. Once you see your LinkedIn feed, **close the browser window**. 
4. A file called `linkedin_session.json` is generated in your `data/` folder. The agent will inject this into future headless runs.

## 🏃 Usage

Once configured and authenticated, simply run the main pipeline:

```bash
python main.py
```

Watch the terminal as the agents fetch jobs, score them against your CV, and trigger Playwright to auto-apply to the top matches!

## 🛡️ Privacy & Security

- **Wait! Do not commit your session:** `data/linkedin_session.json` contains your active authentication tokens. Do not share it!
- **Local Processing**: Ollama runs the intelligence offline, ensuring your data is not sent to external AI providers.

## 📜 License

MIT License
