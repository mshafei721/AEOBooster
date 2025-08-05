# 4. ⚖️ Functional Requirements

## 4.1 Input & Setup

- User enters 1 or more website URLs.
- Optional: user provides business category or selects from dropdown.

## 4.2 Website Crawler

- Crawls site to extract:
  - Product/service pages
  - Metadata (titles, descriptions)
  - Blog or FAQ content
- Identifies core entities (brands, products, services) using NLP.

## 4.3 Dynamic Prompt Bank Generator

- Generates 100 prompt templates from prebuilt clusters:
  - [pain point], [best X], [affordable], [comparison], [support], [safety], etc.
- Injects user-specific entity tags from site crawl.
- Prompts are **generic** in nature, not tailored to the website—used for simulated discovery.

## 4.4 LLM Testing Engine

- Sends each prompt to selected LLM (default: Claude).
- Captures and stores response per prompt.

## 4.5 Scoring System

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

## 4.6 Gap & Opportunity Engine

- For low scoring prompts:
  - Locates missing keyword density or metadata in page content.
  - Uses NLP to match gaps between prompt expectations and site language.

## 4.7 Optimization Plan Output

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
