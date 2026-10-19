import os, re
from bs4 import BeautifulSoup

def hdr():
    return {"User-Agent": os.getenv("SEC_USER_AGENT", "FinDiff dev@example.com")}

async def cik_for(c, ticker):
    r = await c.get("https://www.sec.gov/files/company_tickers.json", headers=hdr())
    for v in r.json().values():
        if v["ticker"] == ticker.upper():
            return str(v["cik_str"]).zfill(10), v["title"]
    return None, None

async def latest_filings(c, cik, form="10-K", n=2):
    r = await c.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=hdr())
    d = r.json()["filings"]["recent"]
    out = []
    for i, f in enumerate(d["form"]):
        if f == form:
            acc = d["accessionNumber"][i].replace("-", "")
            out.append({"date": d["filingDate"][i],
                        "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{d['primaryDocument'][i]}"})
        if len(out) == n:
            break
    return out

async def risk_paragraphs(c, url):
    r = await c.get(url, headers=hdr())
    text = BeautifulSoup(r.text, "html.parser").get_text("\n")
    text = re.sub(r"[ \t\xa0]+", " ", text)
    starts = [m.start() for m in re.finditer(r"item\s*1a\.?\s*[-–—:]?\s*risk\s*factors", text, re.I)]
    ends = [m.start() for m in re.finditer(r"item\s*1b\.?\s*[-–—:]?\s*unresolved", text, re.I)]
    best = ""
    for s in starts:  # table of contents hits are short; the real section is the longest span
        e = next((x for x in ends if x > s), None)
        if e and e - s > len(best):
            best = text[s:e]
    return [p.strip() for p in best.split("\n") if len(p.strip()) > 80]

def _words(p):
    return set(re.findall(r"[a-z]{3,}", p.lower()))

def _novel(src, ref, thr=0.5):
    ref_w = [_words(p) for p in ref]
    out = []
    for p in src:
        w = _words(p)
        best = max((len(w & r) / (len(w | r) or 1) for r in ref_w), default=0)
        if best < thr:
            out.append(p)
    return out

def diff(old, new):
    return {"added": _novel(new, old), "removed": _novel(old, new)}
