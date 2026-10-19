import os, json, httpx

SYSTEM = """You are a sceptical buy-side equity analyst. You receive paragraphs ADDED to and REMOVED from
a company's SEC 10-K 'Risk Factors' vs. the prior year. Return ONLY JSON:
{"headline": str, "alert_score": 1-10 (10 = investors should act now),
 "new_risks": [{"title": str, "why_it_matters": str, "severity": "low|medium|high"}],
 "dropped_risks": [{"title": str, "interpretation": str}],
 "tone_shift": str, "analyst_questions": [str, str, str]}
Only use the supplied text. Boilerplate rewording is NOT a new risk. Max 5 items per list.
This is analysis, not investment advice."""

def _clip(paras, n=7000):
    return "\n".join(f"- {p}" for p in paras)[:n]

async def analyze(added, removed):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return {"error": "GROQ_API_KEY not set - showing raw diff only"}
    body = {"model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": f"ADDED:\n{_clip(added)}\n\nREMOVED:\n{_clip(removed)}"}]}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post("https://api.groq.com/openai/v1/chat/completions", json=body,
                         headers={"Authorization": f"Bearer {key}"})
    if r.status_code != 200:
        return {"error": f"LLM error {r.status_code}: {r.text[:200]}"}
    return json.loads(r.json()["choices"][0]["message"]["content"])
