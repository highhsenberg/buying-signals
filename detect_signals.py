#!/usr/bin/env python3
"""
Buying Signals Detection System (lite)
-----------------------------------------
Ingests raw events from several independent mock sources -- a job board
scrape, a funding news feed, a tech-stack tracker, and website analytics --
normalizes them into one unified Signal schema, removes duplicates (the
same event often gets scraped twice from different job boards), and rolls
them up into a per-company signal-strength score.

This is the detection/normalization layer that feeds a downstream scoring
and routing system (see the `signal-prospecting` project for that half of
the pipeline).

Status: in-progress -- multi-source support and dedup are working; a real
version would poll these sources on a schedule instead of reading static
files, and add a persistent store so signals aren't re-processed every run.

Usage:
    python detect_signals.py --sources-dir sample_sources
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List

DOMAIN_TO_COMPANY = {
    "northwinddata.com": "Northwind Data",
    "fieldworksai.com": "Fieldworks AI",
}


@dataclass(frozen=True)
class Signal:
    source: str
    company: str
    signal_type: str
    detail: str
    days_ago: int
    weight: float


def _load(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_hiring(raw: List[Dict[str, Any]]) -> List[Signal]:
    return [
        Signal(
            source="job_board",
            company=r["employer"],
            signal_type="hiring",
            detail=f"Posted {r['role']}",
            days_ago=r["days_since_posted"],
            weight=2.0,
        )
        for r in raw
    ]


def normalize_funding(raw: List[Dict[str, Any]]) -> List[Signal]:
    return [
        Signal(
            source="funding_news",
            company=r["org"],
            signal_type="funding",
            detail=f"Raised {r['round']} (${r['amount']:,})",
            days_ago=r["days_ago"],
            weight=3.0,
        )
        for r in raw
    ]


def normalize_tech(raw: List[Dict[str, Any]]) -> List[Signal]:
    return [
        Signal(
            source="tech_tracker",
            company=DOMAIN_TO_COMPANY.get(r["domain"], r["domain"]),
            signal_type="tech_change",
            detail=f"Added {r['tool_added']}",
            days_ago=r["days_ago"],
            weight=1.5,
        )
        for r in raw
    ]


def normalize_website(raw: List[Dict[str, Any]]) -> List[Signal]:
    signals = []
    for r in raw:
        weight = 2.0 if r["pricing_page_visits"] >= 3 else 1.0
        signals.append(
            Signal(
                source="website_analytics",
                company=r["account"],
                signal_type="website_activity",
                detail=f"{r['pageviews_last_7d']} pageviews, {r['pricing_page_visits']} pricing page visits (7d)",
                days_ago=0,
                weight=weight,
            )
        )
    return signals


def dedupe(signals: List[Signal]) -> tuple[List[Signal], int]:
    seen = set()
    unique: List[Signal] = []
    duplicates = 0
    for s in signals:
        key = (s.company, s.signal_type, s.detail)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(s)
    return unique, duplicates


def main() -> None:
    parser = argparse.ArgumentParser(description="Buying Signals Detection System (lite)")
    parser.add_argument("--sources-dir", default="sample_sources")
    args = parser.parse_args()

    d = args.sources_dir
    raw_signals: List[Signal] = []
    raw_signals += normalize_hiring(_load(os.path.join(d, "hiring_postings.json")))
    raw_signals += normalize_funding(_load(os.path.join(d, "funding_news.json")))
    raw_signals += normalize_tech(_load(os.path.join(d, "tech_changes.json")))
    raw_signals += normalize_website(_load(os.path.join(d, "website_activity.json")))

    unique, duplicates = dedupe(raw_signals)

    print(f"Detected {len(unique)} unique signals from {len(raw_signals)} raw records ({duplicates} duplicates removed)\n")

    by_company: Dict[str, List[Signal]] = {}
    for s in unique:
        by_company.setdefault(s.company, []).append(s)

    totals = {company: sum(s.weight for s in sigs) for company, sigs in by_company.items()}

    for company in sorted(totals, key=lambda c: totals[c], reverse=True):
        print(f"=== {company} (signal strength: {totals[company]}) ===")
        for s in sorted(by_company[company], key=lambda s: s.days_ago):
            print(f"  [{s.source}] {s.signal_type}: {s.detail} ({s.days_ago}d ago, weight {s.weight})")
        print()


if __name__ == "__main__":
    main()
