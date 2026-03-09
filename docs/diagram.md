```mermaid
graph TD
    User([User Context & CV]) --> VectorDB[(FAISS Vector Database)]
    VectorDB -- CV Embeddings --> JobAnalyzer
    
    subagent_sched[[Daily Scheduler (Cron)]] --> Orchestrator
    
    subgraph Multi_Agent_CrewAI_System [Multi-Agent CrewAI System]
        Orchestrator{Crew Workflow}
        
        Orchestrator --> JobFinder(Job Finder Agent)
        JobFinder --> Scrapers[External Scraping Modules]
        Scrapers -- Raw Job Data --> JobFinder
        JobFinder -- Structured JSON Lists --> Orchestrator
        
        Orchestrator --> JobAnalyzer(Job Analyzer Agent)
        JobAnalyzer -- Fetch similarity distances --> VectorDB
        JobAnalyzer -- Query reasoning --> LocalLLM((Local LLM: Llama3))
        LocalLLM -- Match Score & Decision --> JobAnalyzer
        JobAnalyzer -- Approved URLs --> Orchestrator
        
        Orchestrator --> Applier(Application Agent)
        Applier --> PlaywrightBot[Playwright Automation Bot]
    end

    PlaywrightBot -- Autonomously fill forms & Upload CV --> JobBoards(Job Application Portals)
    JobBoards -. Success / Failure status .-> Applier
    Applier -- Final Logs --> Tracker[(CSV / SQLite DB)]
    
    FeedbackLoop[Rejection Email Parser] -. Feedback .-> Config(Agent Configuration Loop)
    Config -. Updates .-> CV_Tweaks(Dynamic CV Tailoring)
```
