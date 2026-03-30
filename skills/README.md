# Workflows

Markdown SOPs that define how to accomplish specific tasks using the WAT framework.

## Structure of a Workflow File

Each workflow should cover:

1. **Objective** — What this workflow accomplishes
2. **Required Inputs** — What you need before starting (data, credentials, URLs, etc.)
3. **Steps** — Which tools to call, in what order, with what inputs
4. **Expected Outputs** — Where results end up (Google Sheet, Slides, local file, etc.)
5. **Edge Cases** — Known failure modes and how to handle them

## Example Workflow File

```markdown
# Scrape Single Website

## Objective
Extract structured content from a single URL for further processing.

## Required Inputs
- Target URL
- FIRECRAWL_API_KEY in .env

## Steps
1. Run `tools/scrape_single_site.py --url <URL>`
2. Output saved to `.tmp/scraped_<domain>.json`

## Expected Output
JSON file in `.tmp/` with page title, body text, and metadata.

## Edge Cases
- Rate limited: wait 60s and retry once
- Paywalled content: flag to user, do not attempt bypass
```

## Naming Convention

Use lowercase with underscores: `scrape_website.md`, `build_slide_deck.md`, `analyze_csv.md`
