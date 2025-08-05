# Backend Architecture

**Framework:** FastAPI

## Services

### Auth
- **Method:** Clerk (preferred) or Supabase

### Crawler
- **Engine:** Playwright (fallback: BeautifulSoup)
- **Notes:** Scrape metadata, content, titles, descriptions

### NLP
- **Method:** spaCy or simple entity regex
- **Goal:** Extract product, brand, service terms

### Prompt Engine
- **Input:** Entity tags + 100 prompt templates
- **Output:** Dynamic prompt batch per user

### LLM Caller
- **Primary:** Claude API
- **Fallback:** GPT-4o (via OpenAI API)
- **Control:** Rate limit + async queue

### Scoring
**Logic:**
- Mention in top 3 lines: +3
- #1 recommendation: +4
- Mentioned vaguely: +1
- No mention: 0
- Competitor mention only: -2

### Optimizer
- **Input:** Score gaps + page structure
- **Output:** Rewrite suggestions (text, title, FAQ)

### Report Builder
- **Outputs:** JSON + styled HTML/PDF + dashboard API