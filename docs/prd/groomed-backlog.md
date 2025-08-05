# 🛠️ Groomed Backlog

## 📊 Epics

| ID | Epic                                 |
|----|--------------------------------------|
| E1 | User onboarding & input flow         |
| E2 | Website crawling & entity extraction |
| E3 | Dynamic prompt generation            |
| E4 | Prompt testing via LLM               |
| E5 | Scoring engine & AEO score calculation |
| E6 | Gap analysis & optimization suggestions |
| E7 | Visual output & report generation    |
| E8 | Infrastructure, auth, and deployment |

## ✅ User Stories

### E1. User Onboarding & Input
- US-001: As a user, I want to enter my website URL(s) to analyze their AEO performance.
- US-002: As a user, I want to optionally select my business category to better tailor prompts.
- US-003: As a user, I want a simple, responsive web interface to start the analysis easily.

### E2. Website Crawling & Entity Extraction
- US-004: As a system, I need to crawl the provided URL(s) and extract structured content like product pages, services, blog posts, metadata, etc.
- US-005: As a system, I need to extract business-relevant entities (product names, service categories, brand terms) using NLP.

### E3. Dynamic Prompt Generation
- US-006: As a system, I need to generate 100 generic consumer-style prompts based on price, quality, recommendations, etc.
- US-007: As a system, I must inject extracted user entities into prompt templates while keeping them generic.
- US-008: As a user, I want the prompts to simulate real-world search behaviors.

### E4. Prompt Testing via LLM
- US-009: As a system, I want to send all 100 prompts to an LLM (Claude by default) and store the full response for each.
- US-010: As a system, I should retry failed or slow API calls with a timeout handler.
- US-011: As a user, I want to know when the prompt testing phase is in progress or completed.

### E5. Scoring Engine
- US-012: As a system, I need to parse each LLM response and determine if the user’s business was mentioned.
- US-013: As a system, I want to apply the AEO scoring rubric to each prompt.
- US-014: As a user, I want to see my total AEO Score and how each prompt contributed to it.

### E6. Gap & Optimization Suggestions
- US-015: As a system, I want to compare the low-scoring prompt expectations with content gaps on the user’s site.
- US-016: As a user, I want specific rewrite suggestions per page or product/service block to improve AEO Score.
- US-017: As a user, I want to understand which prompt categories I’m weak in (e.g. pricing-related queries).

### E7. Report Generation
- US-018: As a user, I want a visual, step-by-step improvement guide based on the scan results.
- US-019: As a user, I want to export the report as a downloadable PDF.
- US-020: As a user, I want to view missed opportunities and map them to my site content visually.

### E8. Infra, Auth & Hosting
- US-021: As a user, I want to log in securely with email/social login (via Clerk or Supabase).
- US-022: As a system, I want to cache LLM results to reduce duplicate API costs.
- US-023: As a dev, I want deployment on Vercel (frontend) + Railway/Render (backend).

## 🛠️ Technical Tasks

- TT-001: Build initial project scaffolding (FastAPI backend, React frontend)
- TT-002: Integrate Playwright crawler with URL input
- TT-003: Implement entity extraction using spaCy or LLM-based parsing
- TT-004: Build prompt bank manager (100 dynamic templates)
- TT-005: Connect to Claude API with prompt queue + retry mechanism
- TT-006: Create scoring engine logic (token-based or regex-based)
- TT-007: Build optimization suggester using NLP + prompt–content comparison
- TT-008: Build frontend visual report component with charts/tables
- TT-009: Add PDF export with styled summaries
- TT-010: Secure backend endpoints with auth middleware

