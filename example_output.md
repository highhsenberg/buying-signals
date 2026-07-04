# Example run

```
$ python detect_signals.py --sources-dir sample_sources

Detected 7 unique signals from 8 raw records (1 duplicates removed)

=== Northwind Data (signal strength: 8.5) ===
  [website_analytics] website_activity: 340 pageviews, 4 pricing page visits (7d) (0d ago, weight 2.0)
  [job_board] hiring: Posted GTM Engineer (3d ago, weight 2.0)
  [tech_tracker] tech_change: Added Clay (15d ago, weight 1.5)
  [funding_news] funding: Raised Series A ($12,000,000) (21d ago, weight 3.0)

=== Fieldworks AI (signal strength: 4.5) ===
  [website_analytics] website_activity: 120 pageviews, 1 pricing page visits (7d) (0d ago, weight 1.0)
  [tech_tracker] tech_change: Added Smartlead (5d ago, weight 1.5)
  [job_board] hiring: Posted SDR Manager (9d ago, weight 2.0)
```

## What the dedup step is doing

`sample_sources/hiring_postings.json` contains the same Northwind Data /
GTM Engineer posting twice, on purpose -- exactly what happens when a
hiring signal gets scraped from two job boards on the same day. `dedupe()`
keys on `(company, signal_type, detail)` and keeps the first occurrence,
so the downstream signal-strength score doesn't double-count it. The run
above reports this honestly: "1 duplicates removed" rather than silently
inflating Northwind Data's score.

## Why this is a separate project from `signal-prospecting`

This project is the detection/normalization layer: turn messy, source-specific
raw events into one clean `Signal` shape. `signal-prospecting` is the
scoring/qualification/routing layer that consumes signals in that shape.
Splitting them means either can change independently -- adding a new
source here (e.g. a G2 review tracker) doesn't require touching the
scoring rubric at all.
