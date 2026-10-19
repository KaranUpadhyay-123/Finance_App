# FinDiff - AI diff of SEC 10-K Risk Factors

Most "AI + finance" demos wrap a chatbot around stock prices. FinDiff does something analysts actually do:
it compares **this year's vs last year's 10-K Risk Factors**, finds what was genuinely added/removed
(deterministic Jaccard-similarity diff, so boilerplate rewording is filtered *before* the LLM sees it),
and uses an LLM to rate severity, interpret dropped risks and suggest questions for management.
Results are overlaid on the stock price with the filing date marked.

**100% free:** SEC EDGAR (no key), Yahoo chart endpoint (no key), and Groq free-tier models.
The default analysis model is `openai/gpt-oss-120b`; set `GROQ_MODEL` to another active Groq model to override it.

## Run
```
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # add GROQ_API_KEY and your email in SEC_USER_AGENT
uvicorn app.main:app --reload
```
Open http://localhost:8000 and try NVDA, TSLA, META.

## Design decisions (interview talking points)
- **Hybrid pipeline:** classic NLP diff narrows ~200 paragraphs to the changed few, so the LLM gets small,
  grounded input -> lower cost, less hallucination.
- **Grounded prompt:** model may only use supplied text; raw evidence paragraphs are shown beside every claim.
- **Structured JSON output** with a fixed schema, graceful fallback to raw diff if no API key.
- **Section extraction** picks the longest "Item 1A -> Item 1B" span to skip table-of-contents false hits.
- In-memory cache avoids refetching; SEC politeness via User-Agent.

## Extend ideas
10-Q comparison, multi-ticker watchlist, embeddings-based clustering, persistent DB, evaluation set of known risk changes.
