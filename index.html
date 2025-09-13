#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape les montants de la prime à l'autoconsommation (€/kWc) depuis photovoltaique.info
et écrit data/primes.json au format consommé par le front.
"""
import os, sys, re, json, datetime
from urllib.request import urlopen, Request
from html.parser import HTMLParser

SOURCE_URL = "https://www.photovoltaique.info/fr/tarifs-dachat-et-autoconsommation/dispositifs-de-soutien-public/aides-au-photovoltaique/aides-au-photovoltaique/"
UA = "Mozilla/5.0 (compatible; EchomePrimesBot/1.0; +https://github.com/)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_FILE = os.path.join(ROOT, "data", "primes.json")

class TableCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.current = []
        self.tables = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "table":
            self.in_table = True
            self.current = []
    def handle_endtag(self, tag):
        if tag.lower() == "table" and self.in_table:
            self.in_table = False
            text = " ".join(self.current)
            self.tables.append(re.sub(r"\s+", " ", text).strip())
            self.current = []
    def handle_data(self, data):
        if self.in_table:
            t = data.strip()
            if t:
                self.current.append(t)

def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")

ROW_REGEX = re.compile(
    r"(?P<range>(?:≤|<)?\s*\d+\s*(?:–|-|à)\s*\d+\s*kWc|≤\s*\d+\s*kWc|\d+\s*kWc)"
    r".{0,80}?"
    r"(?P<eur>\d{2,4})\s*€\s*/?\s*kWc",
    re.IGNORECASE
)

DEFAULT = [
    ("≤ 3 kWc", 330),
    ("3–9 kWc", 250),
    ("9–36 kWc", 200),
    ("36–100 kWc", 100),
]

def parse(html: str):
    p = TableCollector(); p.feed(html)
    rows = []
    for t in p.tables:
        for m in ROW_REGEX.finditer(t):
            rg = re.sub(r"\s+", " ", m.group("range")).strip()
            try:
                val = int(m.group("eur"))
                rows.append((rg, val))
            except:
                pass
    out = []
    for label, fallback in DEFAULT:
        token = re.findall(r"\d+", label)
        first = token[0] if token else None
        found = None
        for rg, val in rows:
          # word boundary requires double escaping inside f-string if used; we avoid f-string here
          if first and re.search(r"\b"+re.escape(first)+r"\b", rg):
              found = val; break
        out.append( (label, found if found is not None else fallback) )
    return out

def main():
    try:
        html = fetch(SOURCE_URL)
        parsed = parse(html)
        payload = {
            "version": "auto",
            "source": SOURCE_URL,
            "last_updated": datetime.date.today().isoformat(),
            "prime_autoconsommation_eur_per_kwc": [
                {"range": label, "eur_per_kwc": int(val)} for label, val in parsed
            ],
            "notes": [
                "Montants indicatifs pour installations ≤ 100 kWc, versés en 5 annuités via EDF OA.",
                "Barèmes dégressifs mis à jour trimestriellement par la CRE."
            ]
        }
        os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("OK wrote", OUT_FILE)
        for r in payload["prime_autoconsommation_eur_per_kwc"]:
            print(f"- {r['range']}: {r['eur_per_kwc']} €/kWc")
        return 0
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
