# Choosing the web search tool

Research for the `web_search` tool in `src/tools/web_search.py`.
Checked and tested on 2026-11-04. Free tiers change often, so check the
pricing pages again before building.

## Recommendation

- **Winner: Exa.** In our test, 80% of its results were useful (40 of 50).
  Tavily got 66% (33 of 50). Exa also has the biggest free quota that renews
  every month: $10 of credit, which is about 1,400 searches. It needs no card
  and has an official LangChain package (`langchain-exa`).
- **Backup: Tavily.** It also worked on every query, and its text snippets
  are the best: each one is the part of the page that answers the query. But
  it found fewer Egypt-specific pages, and 4 of its 50 results were Tavily's
  own company-profile pages. It gives 1,000 searches a month, no card.
- **No-key fallback: none is good enough for the agents.** DuckDuckGo via
  the `ddgs` package worked once. A few minutes later it was blocked on 9 of
  10 queries. Use it only for quick local experiments.
- **For reading one page:** Jina Reader (`r.jina.ai`) works with no key.
  You give it a URL and it returns the page as clean text, at 20 requests a
  minute.

## Test results

The test ran 10 fixed queries, at least two per agent, plus one in Arabic.
Each tool's top 5 results were marked useful (1) or not (0), so the best
possible score is 5 per query. A result counts as useful when it answers the
query for Egypt, or is the official source for it. The scripts and raw JSON
results were kept outside the repo.

| Query | Agent | Tavily | Exa |
|---|---|---|---|
| Shopify vs Magento headless API rate limits 2026 | Technical | 3 | 4 |
| Paymob API integration documentation webhooks | Technical | 5 | 5 |
| AWS EC2 pricing Bahrain region me-south-1 | Financial | 2 | 5 |
| Paymob transaction fees Egypt | Financial | 4 | 5 |
| Noon Egypt buy now pay later | Competitor | 3 | 3 |
| Amazon.eg same-day delivery Cairo | Competitor | 1 | 3 |
| Egypt Personal Data Protection Law 151 of 2020 executive regulations | Risk | 5 | 5 |
| e-commerce data breach Egypt | Risk | 5 | 5 |
| Jumia Egypt seller fees commission 2026 | Competitor | 3 | 3 |
| أسعار التوصيل نون مصر (Noon Egypt delivery prices) | Competitor | 2 | 2 |
| **Total** | | **33 / 50 (66%)** | **40 / 50 (80%)** |

Other numbers from the same runs:

| | Tavily | Exa | `ddgs` (no key) |
|---|---|---|---|
| Queries with an error | 0 of 20 | 0 of 20 | 1 of 10 in run 1, 9 of 10 in run 2 |
| Average time per query | 1.8 s | 1.1 s (1.8 s with the Egypt setting) | 2.9 s |
| Results from Egyptian sites (`.eg` or `/egypt` in the address) | 7 of 50 | 11 of 50 | n/a |
| Results with a publish date | 0 of 50 | 15 of 50 | 0 |
| Snippet | About 1,000–1,500 characters, the part that matches the query | Page text from the top, cut at 1,000 characters in our test | About 200 characters |

What went wrong:

- **Tavily** often returned pages from the wrong country. Examples: Paymob's
  Saudi pricing page, Jumia commissions for Kenya and Nigeria, and Amazon's
  US help page for "Amazon.eg same-day delivery". 4 results were Tavily's own
  `tavily.com/knowledge` company-profile pages, which are not real sources.
- **Exa** sometimes returned a generic home page (Noon, Amazon.eg), and once
  an old Saudi press release (Tabby, 2022). Its page text starts at the top
  of the page, so it can begin with menu text. Exa's `highlights` option
  returns the passages that match the query instead. The built tool uses it.
- **Both** did poorly on the Arabic query: 2 of 5 each. The useful results
  were blogs listing Noon's delivery fees. The rest were Noon's home or
  product pages.
- **The Egypt setting barely helps.** Tavily's `country="egypt"` and Exa's
  `userLocation="EG"` both only push Egyptian pages up the list. Neither
  keeps only Egyptian results. With the setting on, Exa returned 70% of the
  same URLs and got 0.7 s slower. Tavily returned 44% of the same URLs, but
  its count of Egyptian sites only went from 6 to 7. Writing "Egypt" in the
  query does more than either setting.

## How many searches we need

One analysis runs four agents that would use web search: Technical,
Financial, Competitor and Risk. Each makes about 5 searches. The validator
can send work back up to 2 times (`max_revisions: 2` in
`config/tasks.yaml`).

| Case | Searches per analysis |
|---|---|
| Normal run | 4 agents × 5 = **about 20** |
| Worst case (2 revision rounds) | 3 rounds × 20 = **about 60** |

How many analyses each free tier covers in a month:

| Service | Free searches | Renews | Normal runs | Worst-case runs |
|---|---|---|---|---|
| Exa | about 1,400 ($10 at $7 per 1,000) | Monthly | about 70 | about 23 |
| Tavily | 1,000 (1 credit per basic search) | Monthly | 50 | about 16 |
| Firecrawl | 500 (2 credits per 10 results) | Monthly | 25 | about 8 |
| Linkup | "4,000 queries" | Not stated | up to 200 | up to 66 |
| Serper | 2,500 | Once only | 125 in total | 41 in total |
| SerpApi | 250 | Monthly | about 12 | 4 |
| `ddgs` | No limit on paper | n/a | Blocked after about 10 searches in our test | n/a |

**No free tier covers a whole team during development.** For example, 4
people running 3 analyses a day for 20 work days is 240 runs, or about 4,800
searches. Two ways to handle it: each developer uses their own free key,
and tests use saved results instead of live calls.

## Scoring

Each criterion gets a score from 1 to 5. The total is out of 100 (the
weighted sum ÷ 5). Exa, Tavily and `ddgs` were scored from our tests. The
others were scored from their docs only.

| Criterion | Weight | Exa | Tavily | Firecrawl | Linkup | Serper | `ddgs` |
|---|---|---|---|---|---|---|---|
| Free quota vs. our need | 25% | 5 | 4 | 3 | 3 | 2 | 5 |
| Result quality for our queries | 25% | 4 | 3 | 3* | 3* | 4* | 3 |
| URL + useful content | 15% | 4 | 5 | 5 | 4 | 2 | 2 |
| LangChain integration | 10% | 5 | 5 | 3 | 4 | 4 | 3 |
| Speed and reliability | 10% | 4 | 4 | 3 | 3 | 4 | 1 |
| Filters (date, country, domains) | 10% | 4 | 4 | 4 | 3 | 4 | 2 |
| Terms of use, lock-in | 5% | 4 | 4 | 4 | 4 | 4 | 1 |
| **Total** | | **87** | **80** | **69** | **66** | **64** | **59** |

\* Estimated from the docs, not tested.

Why the scores differ:

- **Exa.** Its free $10 renews every month, and normal search costs $7 per
  1,000 (Lite is $4). The price covers up to 10 results, and page text comes
  with them. It loses one point on content because its text starts at the
  top of the page.
- **Tavily.** The free plan resets on the 1st of each month. A basic search
  costs 1 credit and an advanced one costs 2. The free key allows 100
  requests a minute. Its snippets are the best of all the tools, but its
  results were less relevant for Egypt. Nebius bought Tavily in 2026. The
  free plan has not changed since then, but it is a risk to watch.
- **Firecrawl.** It is built for reading pages, not for search. It allows
  only 10 searches a minute and 2 requests at once. In LangChain it is a
  document loader, not a search tool.
- **Linkup.** The pricing page says "Run 4,000 queries for free" but does
  not say whether that is per month. Quality is unknown.
- **Serper.** It returns Google results and has `gl=eg` / `hl=ar` for Egypt
  and Arabic. But its 2,500 free searches are given once only, and it
  returns short snippets, not page text.
- **`ddgs`.** It needs no key, but it works by scraping search engines. In
  our test the DuckDuckGo engine itself returned nothing. The results came
  from other engines, Bing included (one result was a Bing ad link). This
  can break at any time and goes against those engines' terms. In its one
  good run, 34 of 50 results were useful (68%), close to Tavily.

## Dropped early

- **Brave Search API.** It gives $5 of free credit a month (about 1,000
  searches), but asks for a credit card "to prevent abuse".
- **Google Programmable Search (JSON API).** It is closed to new sign-ups and
  shuts down on 1 January 2027.
- **Bing Search API.** Microsoft retired it in 2025.
- **Jina Search (`s.jina.ai`).** Its 10 million free tokens are given once
  only, and each search uses about 10,000 tokens. That is about 1,000
  searches in total. (Jina Reader is still useful. See above.)
- **SearXNG.** It is free and has no limits, but we would have to run and
  host it ourselves. Keep it in mind if every free quota turns out too small.

## How it fits this code

The tool is built in `src/tools/web_search.py`, as described below.

1. One function: `@register_tool def web_search(query: str) -> str`. Its
   docstring tells the LLM when to use it, and to write the country
   ("Egypt") into the query.
2. It calls Exa with `type="auto"`, 3 results, and `highlights` for the
   text. Highlights are the passages that match the query, which makes a
   better `Evidence.snippet` than the top of the page. A live check
   confirmed this: the Paymob result held "2.75% + 3 EGP per transaction".
   Each result is capped at 600 characters, about 500 tokens per search.
   Without a cap, one search returned about 10,000 characters (about 2,700
   tokens). Every result stays in the agent's conversation, and Groq's free
   tier allows 8,000 tokens per minute: with 5 results of 1,000 characters,
   three searches already broke that limit. `userLocation` is left off: in
   our test it changed little and slowed each call.
3. The output looks like `search_company_docs` in `src/tools/db_tool.py`:
   a `[source: <url>]` line, then the title, the publish date when Exa gives
   one, and the passages. The agents can copy the URL into
   `Evidence.source`.
4. The key is `EXA_API_KEY`, in `.env.example` and in `Settings`
   (`config/settings.py`). The client is created on the first search, so
   building the agents and running the tests need no key.
5. The module is imported in `src/tools/__init__.py`. `web_search` is in
   the `tools:` list of `technical`, `financial`, `competitor` and `risk`
   in `config/agents.yaml`.
6. It uses Exa's official Python SDK, `exa-py`, listed in `pyproject.toml`.
   The tool is our own `@register_tool` function, so it does not need the
   `langchain-exa` wrapper.

## Risks

| Risk | What to do |
|---|---|
| The free tier shrinks (Brave and Google already cut theirs) | Keep the tool to one function, so switching service is a one-file change. Tavily is the tested backup. |
| Revision loops use up the monthly quota | Cap searches per agent in the prompt. Use saved results in tests. |
| Weak results in Arabic (2 of 5 for both tools) | Ask the agents to search in English first and use Arabic only for local prices. Retest when the agents are built. |
| Generic home pages instead of the page with the answer | Read the page with Jina Reader when a snippet has no answer. |

## Sources

Official pages, read on 2026-11-04:

- Exa pricing: https://exa.ai/pricing
- Exa location filter: https://docs.exa.ai/changelog/geolocation-filter-support
- Tavily pricing: https://www.tavily.com/pricing
- Tavily credits: https://docs.tavily.com/documentation/api-credits
- Tavily rate limits: https://docs.tavily.com/documentation/rate-limits
- Tavily search parameters: https://docs.tavily.com/documentation/api-reference/endpoint/search
- Brave Search API: https://brave.com/search/api/
- Linkup pricing: https://www.linkup.so/pricing
- Firecrawl pricing: https://www.firecrawl.dev/pricing
- Google Custom Search JSON API: https://developers.google.com/custom-search/v1/overview
- Nebius buys Tavily: https://nebius.com/newsroom/nebius-announces-agreement-to-acquire-tavily-to-add-agentic-search-to-its-ai-cloud-platform
- LangChain + Exa: https://docs.langchain.com/oss/python/integrations/providers/exa_search
- LangChain + Tavily: https://docs.langchain.com/oss/python/integrations/providers/tavily

Other sources, used only where the official pages say nothing:

- Serper free queries: https://coldiq.com/blog/serper-pricing
- SerpApi free plan: https://www.honeyb.ai/blog/serpapi-pricing
- Jina free tokens: https://parallel.ai/articles/best-free-web-search-api
- `ddgs` rate limits: https://apiserpent.com/blog/scrape-duckduckgo-serp-for-free
