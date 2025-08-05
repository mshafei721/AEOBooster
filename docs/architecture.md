system:

&nbsp; name: AEOBooster

&nbsp; type: Web Application

&nbsp; purpose: Help businesses optimize their websites for AI chatbot visibility using prompt simulation and scoring.

&nbsp; core\_idea: Simulate 100+ customer-style prompts, run them against Claude/GPT, and assess how well a business appears in responses. Generate visual improvement steps based on actual site content.



frontend:

&nbsp; framework: React

&nbsp; styling: Tailwind CSS

&nbsp; ui\_modules:

&nbsp;   - InputForm: Accepts website URLs and optional business type

&nbsp;   - Dashboard: Displays prompt progress, score summary

&nbsp;   - PromptGrid: Visual table of all 100 prompts with result states

&nbsp;   - OptimizationChecklist: Step-by-step improvement guide per page

&nbsp;   - Exporter: PDF/CSV download button



backend:

&nbsp; framework: FastAPI

&nbsp; services:

&nbsp;   - auth:

&nbsp;       method: Clerk (preferred) or Supabase

&nbsp;   - crawler:

&nbsp;       engine: Playwright (fallback: BeautifulSoup)

&nbsp;       notes: Scrape metadata, content, titles, descriptions

&nbsp;   - nlp:

&nbsp;       method: spaCy or simple entity regex

&nbsp;       goal: Extract product, brand, service terms

&nbsp;   - prompt\_engine:

&nbsp;       input: Entity tags + 100 prompt templates

&nbsp;       output: Dynamic prompt batch per user

&nbsp;   - llm\_caller:

&nbsp;       primary: Claude API

&nbsp;       fallback: GPT-4o (via OpenAI API)

&nbsp;       control: Rate limit + async queue

&nbsp;   - scoring:

&nbsp;       logic:

&nbsp;         - Mention in top 3 lines: +3

&nbsp;         - #1 recommendation: +4

&nbsp;         - Mentioned vaguely: +1

&nbsp;         - No mention: 0

&nbsp;         - Competitor mention only: -2

&nbsp;   - optimizer:

&nbsp;       input: Score gaps + page structure

&nbsp;       output: Rewrite suggestions (text, title, FAQ)

&nbsp;   - report\_builder:

&nbsp;       outputs: JSON + styled HTML/PDF + dashboard API



storage:

&nbsp; database: PostgreSQL (or SQLite for local dev)

&nbsp; schema:

&nbsp;   - users: id, email, auth\_token

&nbsp;   - projects: id, user\_id, site\_url, created\_at

&nbsp;   - prompts: id, project\_id, type, text, score, result\_text

&nbsp;   - entities: id, project\_id, type, value

&nbsp;   - reports: id, project\_id, json\_data, pdf\_link



llm:

&nbsp; strategy:

&nbsp;   - Prompt Cluster Library (static YAML file)

&nbsp;   - Entity Injector (dynamic)

&nbsp;   - Async call handler (with Claude fallback to GPT)

&nbsp;   - JSON result parser and indexer



infra:

&nbsp; hosting:

&nbsp;   frontend: Vercel

&nbsp;   backend: Render or Railway

&nbsp;   db: Supabase / Railway PostgreSQL

&nbsp; optional:

&nbsp;   jobs: Celery + Redis or async FastAPI tasks

&nbsp;   pdf: puppeteer container or pdfkit in backend



security:

&nbsp; - Auth token via Clerk

&nbsp; - Rate-limiting LLM API

&nbsp; - No persistent user cookies

&nbsp; - Follow robots.txt for all crawls



deployment:

&nbsp; dev:

&nbsp;   - Local SQLite + mock LLM

&nbsp;   - ngrok for frontend testing

&nbsp; prod:

&nbsp;   - Domain setup via Vercel

&nbsp;   - Backend Docker deploy on Railway

&nbsp;   - Claude API key environment variable

