#!/usr/bin/env python3
# scripts/scrape_tarifs.py
# Scrapes official photovoltaic tariffs from photovoltaique.info and writes /data/tarifs.json
# Run locally or via GitHub Actions.
import os, sys, json, re, datetime
from urllib.request import urlopen, Request
from html.parser import HTMLParser

SOURCE_URL = "https://www.photovoltaique.info/fr/tarifs-dachat-et-autoconsommation/"
UA = "Mozilla/5.0 (compatible; EchomeTarifsBot/1.0; +https://github.com/<your-repo>)"
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "tarifs.json")

class SimpleTextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_table = False
        self.buffer = []
    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
            self.buffer = []
    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            self.in_table = False
            self.text.append("\n".join(self.buffer))
            self.buffer = []
    def handle_data(self, data):
        if self.in_table:
            t = data.strip()
            if t:
                self.buffer.append(t)

def fetch(url):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")

def parse_tables(raw):
    # Heuristic: look for rows containing 'kWc' and '€/kWh'
    # Fallback to previous values if parsing fails.
    parser = SimpleTextHTMLParser()
    parser.feed(raw)
    tables = parser.text

    # Find lines that look like tariff rows; example variants
    pattern = re.compile(r"(?P<range>(?:≤|<|≤\s*)?\s*\d+\s*(?:–|-|à)\s*\d+\s*kWc|≤\s*\d+\s*kWc|\\d+\\s*kWc).*?(?P<eur>0[,\\.]\\d{3,4})\\s*€/\\s*kWh", re.IGNORECASE)
    rows = []
    for t in tables:
        for m in pattern.finditer(t.replace("\n"," ")):
            rng = re.sub(r"\s+", " ", m.group("range")).strip()
            eur = m.group("eur").replace(",", ".")
            try:
                val = float(eur)
                rows.append((rng, val))
            except:
                continue
    # Deduplicate keep order
    seen = set(); unique = []
    for r in rows:
        if r not in seen:
            unique.append(r); seen.add(r)
    return unique

def build_payload(rows):
    # Map rows to our expected structure with simple rules
    # Defaults if not found
    defaults = [
        ("≤ 9 kWc", 0.040, "particuliers", 1000),
        ("9–36 kWc", 0.040, "petites pros", 5000),
        ("36–100 kWc", 0.0886, "PME/PMI", 20000),
    ]
    out = []
    for label, val, seg, ex_kwh in defaults:
        # find a row that mentions the start of label (rough match)
        match = next((r for r in rows if label.split()[0] in r[0]), None)
        if match:
            out.append({"range": label, "segment": seg, "eur_per_kwh": match[1], "example_surplus_kwh": ex_kwh})
        else:
            out.append({"range": label, "segment": seg, "eur_per_kwh": val, "example_surplus_kwh": ex_kwh})
    payload = {
        "version": "auto",
        "source": SOURCE_URL,
        "last_updated": datetime.date.today().isoformat(),
        "edf_oa_surplus": out,
        "notes": [
            "Données extraites automatiquement de photovoltaique.info (heuristique).",
            "Vérifier l'arrêté et barèmes trimestriels (CRE) avant signature."
        ],
        "avg_autoconsommation_value_ttc_eur_per_kwh": 0.25
    }
    return payload

def main():
    try:
        html = fetch(SOURCE_URL)
        rows = parse_tables(html)
        payload = build_payload(rows)
        os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("OK wrote", OUT_FILE)
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()