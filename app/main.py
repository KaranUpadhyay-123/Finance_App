import httpx
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
load_dotenv()
from . import sec, llm  # noqa: E402

app = FastAPI(title="FinDiff")
CACHE = {}
STATIC = Path(__file__).parent.parent / "static"

async def prices(c, t):
    try:
        r = await c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=2y&interval=1wk",
                        headers={"User-Agent": "Mozilla/5.0"})
        res = r.json()["chart"]["result"][0]
        return [{"t": ts, "c": cl} for ts, cl in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if cl]
    except Exception:
        return []

@app.get("/api/analyze/{ticker}")
async def analyze(ticker: str):
    ticker = ticker.upper().strip()
    if ticker in CACHE:
        return CACHE[ticker]
    async with httpx.AsyncClient(timeout=40, follow_redirects=True) as c:
        cik, name = await sec.cik_for(c, ticker)
        if not cik:
            raise HTTPException(404, "Ticker not found on SEC EDGAR (US-listed companies only)")
        fl = await sec.latest_filings(c, cik)
        if len(fl) < 2:
            raise HTTPException(404, "Need at least two 10-K filings to compare")
        new, old = await sec.risk_paragraphs(c, fl[0]["url"]), await sec.risk_paragraphs(c, fl[1]["url"])
        if not new or not old:
            raise HTTPException(422, "Could not locate Risk Factors section in a filing")
        d = sec.diff(old, new)
        out = {"ticker": ticker, "company": name, "filings": fl,
               "stats": {"old_paras": len(old), "new_paras": len(new),
                         "added": len(d["added"]), "removed": len(d["removed"])},
               "added": d["added"][:15], "removed": d["removed"][:15],
               "ai": await llm.analyze(d["added"], d["removed"]),
               "prices": await prices(c, ticker)}
    CACHE[ticker] = out
    return out

app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
