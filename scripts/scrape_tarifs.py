#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/scrape_tarifs.py
Scrape les tarifs photovoltaïques (surplus EDF OA) depuis photovoltaique.info
et met à jour data/tarifs.json au format consommé par assets/tarifs.js.

- Stdlib only (urllib, html.parser, re, json)
- Heuristique : recherche de lignes contenant kWc et €/kWh
- Tolérant aux changements mineurs de mise en page

Exécution locale :
  python scripts/scrape_tarifs.py
"""

from __future__ import annotations
import os, sys, json, re, datetime
from urllib.request import urlopen, Request
from html.parser import HTMLParser

SOURCE_URL = "https://www.photovoltaique.info/fr/tarifs-dachat-et-autoconsommation/"
UA = "Mozilla/5.0 (compatible; EchomeTarifsBot/1.0; +https://github.com/)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_FILE = os.path.join(ROOT, "data", "tarifs.json")

# --------- HTML parsing minimaliste (récupération brute des <table>) ---------
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
            # Normaliser les espaces
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                self.tables.append(text)
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

# --------- Extraction heuristique des lignes "plage kWc" + "€/kWh" ----------
ROW_REGEX = re.compile(
    r"(?P<range>(?:≤|<)?\s*\d+\s*(?:–|-|à)\s*\d+\s*kWc|≤\s*\d+\s*kWc|\d+\s*kWc)"
    r".{0,80}?"
    r"(?P<eur>0[,\.]\d{3,4})\s*€/?.{0,10}?kWh",
    re.IGNORECASE
)

def parse_tariffs_from_html(html: str) -> list[tuple[str, float]]:
    parser = TableCollector()
    parser.feed(html)
    rows = []
    for t in parser.tables:
        for m in ROW_REGEX.finditer(t):
            rang = re.sub(r"\s+", " ", m.group("range")).strip()
            eur = m.group("eur").replace(",", ".")
            try:
                val = float(eur)
                rows.append((rang, val))
            except ValueError:
                pass
    # dédupliquer en gardant l’ordre
    seen = set()
    uniq = []
    for r in rows:
        if r not in seen:
            uniq.append(r)
            seen.add(r)
    return uniq

# --------- Construction du payload attendu par le front ----------------------
DEFAULT_ROWS = [
    ("≤ 9 kWc", 0.040, "particuliers", 1000),
    ("9–36 kWc", 0.040, "petites pros", 5000),
    ("36–100 kWc", 0.0886, "PME/PMI", 20000),
]

def build_payload(extracted: list[tuple[str, float]]) -> dict:
    def _match(label_start: str) -> float | None:
        # on matche sur le premier nombre de la plage, ex: "≤ 9" → "9"
        token = re.findall(r"\d+", label_start)
        if not token:
            return None
        first = token[0]
        for rng, val in extracted:
            if re.search(rf"\b{re.escape(first)}\b", rng):
                return val
        return None

    edf_oa_surplus = []
    for label, fallback_val, seg, ex_kwh in DEFAULT_ROWS:
        val = _match(label) or fallback_val
        edf_oa_surplus.append(
            {
                "range": label,
                "segment": seg,
                "eur_per_kwh": round(float(val), 4),
                "example_surplus_kwh": int(ex_kwh),
            }
        )

    payload = {
        "version": "auto",
        "source": SOURCE_URL,
        "last_updated": datetime.date.today().isoformat(),
        "edf_oa_surplus": edf_oa_surplus,
        "notes": [
            "Données extraites automatiquement de photovoltaique.info (heuristique).",
            "Vérifier l'arrêté et les barèmes trimestriels (CRE) avant signature."
        ],
        "avg_autoconsommation_value_ttc_eur_per_kwh": 0.25
    }
    return payload

# --------- Main --------------------------------------------------------------
def main() -> int:
    try:
        html = fetch(SOURCE_URL)
        extracted = parse_tariffs_from_html(html)
        payload = build_payload(extracted)

        os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        print(f"Écrit: {OUT_FILE}")
        for r in payload["edf_oa_surplus"]:
            print(f"- {r['range']}: {r['eur_per_kwh']} €/kWh")
        return 0
    except Exception as e:
        print("ERREUR:", e, file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
