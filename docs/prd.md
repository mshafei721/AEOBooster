# PRODUCT REQUIREMENTS DOCUMENT

**Project Codename:** AEOBooster\
**BMAD Workflow:** *workflow greenfield-fullstack\
**Command Used:** *create-prd

---

## 1. 📝 Overview

**AEOBooster** is a web-based platform that helps businesses optimize their websites for visibility inside AI chat platforms like ChatGPT, Claude, and Gemini.

The tool simulates 100+ customer-intent prompts to see if the business is mentioned in LLM responses, then provides a tailored improvement plan based on the business’s existing content. The outcome is a dynamic **AI Engine Optimization (AEO)** report and a visual, page-level improvement guide.

---

## 2. ✨ Goals

- Identify whether a user’s business appears in AI chatbot responses.
- Simulate real-world customer discovery prompts at scale.
- Score performance (AEO Score) based on LLM mentions, authority, context.
- Suggest precise edits tied to user website content (not just theory).
- Deliver clear, visual improvement steps to the user.

---

## 3. 🧑‍💼 Target Users

| Segment               | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| Small business owners | Want to know if they appear in AI tools like ChatGPT             |
| SEO professionals     | Looking to expand optimization from search engines to AI engines |
| Marketers / Agencies  | Need client-facing AEO visibility reports                        |
| Founders / Startups   | Early validation of their online discoverability                 |

---

## 4. ⚖️ Functional Requirements

### 4.1 Input & Setup

- User enters 1 or more website URLs.
- Optional: user provides business category or selects from dropdown.

### 4.2 Website Crawler

- Crawls site to extract:
  - Product/service pages
  - Metadata (titles, descriptions)
  - Blog or FAQ content
- Identifies core entities (brands, products, services) using NLP.

### 4.3 Dynamic Prompt Bank Generator

- Generates 100 prompt templates from prebuilt clusters:
  - [pain point], [best X], [affordable], [comparison], [support], [safety], etc.
- Injects user-specific entity tags from site crawl.
- Prompts are **generic** in nature, not tailored to the website—used for simulated discovery.

### 4.4 LLM Testing Engine

- Sends each prompt to selected LLM (default: Claude).
- Captures and stores response per prompt.

### 4.5 Scoring System

- For each prompt:
  - Checks if brand/product/service is mentioned.
  - Scores based on mention placement and authority context.
- Aggregates into total AEO Score.

| Score Breakdown              | Points |
| ---------------------------- | ------ |
| Mentioned in top 3 sentences | +3     |
| #1 recommendation            | +4     |
| Mentioned vaguely            | +1     |
| No mention                   | 0      |
| Mentioned competitor only    | -2     |

### 4.6 Gap & Opportunity Engine

- For low scoring prompts:
  - Locates missing keyword density or metadata in page content.
  - Uses NLP to match gaps between prompt expectations and site language.

### 4.7 Optimization Plan Output

- Generates:
  - AEO Scorecard
  - Missed prompt cluster types (e.g. “price-focused prompts fail”)
  - Per-page content fix recommendations
  - Suggested copy rewrites and additions
- Formats output as:
  - Step-by-step checklist
  - Downloadable PDF
  - Interactive report dashboard

---

## 5. 🧠 Non-Functional Requirements

- **LLM API Usage**: Claude (primary), GPT-4o (optional fallback)
- **Crawling Respect**: Follows robots.txt or use browser automation fallback
- **Mobile-first UI**: App must be responsive
- **LLM Output Caching**: Avoid redundant API calls per session
- **Security**: No storage of user credentials or cookies

---

## 6. ⚙️ Tech Stack

| Layer       | Tool                                              |
| ----------- | ------------------------------------------------- |
| Frontend    | React + Tailwind CSS                              |
| Backend     | FastAPI                                           |
| Web Scraper | Playwright (preferred), fallback to BeautifulSoup |
| LLM API     | Claude (Anthropic), optional GPT-4o               |
| Storage     | PostgreSQL or SQLite                              |
| Auth        | Clerk or Supabase                                 |
| Hosting     | Vercel (frontend) + Railway/Render (backend)      |

---

## 7. 📋 Success Criteria

- Users complete a full scan in <3 minutes
- Users receive ≥90% prompt coverage (even if low score)
- Suggested improvements are mapped to real site content (not generic)
- At least 3 prompts improve after edits (when re-tested)
- First 5 users generate >75% satisfaction in UX tests

---

## 8. ⛔ Out of Scope (Phase 1)

- Real-time competitor analysis
- CMS integrations (e.g., WordPress auto-fix)
- Bulk project reporting
- Multi-user/team collaboration

---

## 9. 📌 Open Questions

- Should we support user-uploaded sitemaps? only URL
- Should user be able to regenerate prompts with different focus? (e.g. only "price-sensitive buyers") the prompts should be based on price, quality, recommendations, etc. 
- Add industry-specific prompt packs? no should be for all

---

## 🛠️ Groomed Backlog

### 📊 Epics

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

### ✅ User Stories

#### E1. User Onboarding & Input
- US-001: As a user, I want to enter my website URL(s) to analyze their AEO performance.
- US-002: As a user, I want to optionally select my business category to better tailor prompts.
- US-003: As a user, I want a simple, responsive web interface to start the analysis easily.

#### E2. Website Crawling & Entity Extraction
- US-004: As a system, I need to crawl the provided URL(s) and extract structured content like product pages, services, blog posts, metadata, etc.
- US-005: As a system, I need to extract business-relevant entities (product names, service categories, brand terms) using NLP.

#### E3. Dynamic Prompt Generation
- US-006: As a system, I need to generate 100 generic consumer-style prompts based on price, quality, recommendations, etc.
- US-007: As a system, I must inject extracted user entities into prompt templates while keeping them generic.
- US-008: As a user, I want the prompts to simulate real-world search behaviors.

#### E4. Prompt Testing via LLM
- US-009: As a system, I want to send all 100 prompts to an LLM (Claude by default) and store the full response for each.
- US-010: As a system, I should retry failed or slow API calls with a timeout handler.
- US-011: As a user, I want to know when the prompt testing phase is in progress or completed.

#### E5. Scoring Engine
- US-012: As a system, I need to parse each LLM response and determine if the user’s business was mentioned.
- US-013: As a system, I want to apply the AEO scoring rubric to each prompt.
- US-014: As a user, I want to see my total AEO Score and how each prompt contributed to it.

#### E6. Gap & Optimization Suggestions
- US-015: As a system, I want to compare the low-scoring prompt expectations with content gaps on the user’s site.
- US-016: As a user, I want specific rewrite suggestions per page or product/service block to improve AEO Score.
- US-017: As a user, I want to understand which prompt categories I’m weak in (e.g. pricing-related queries).

#### E7. Report Generation
- US-018: As a user, I want a visual, step-by-step improvement guide based on the scan results.
- US-019: As a user, I want to export the report as a downloadable PDF.
- US-020: As a user, I want to view missed opportunities and map them to my site content visually.

#### E8. Infra, Auth & Hosting
- US-021: As a user, I want to log in securely with email/social login (via Clerk or Supabase).
- US-022: As a system, I want to cache LLM results to reduce duplicate API costs.
- US-023: As a dev, I want deployment on Vercel (frontend) + Railway/Render (backend).

### 🛠️ Technical Tasks

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

