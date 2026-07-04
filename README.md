# Buying Signals Detection System (lite)

**Status: in-progress.**

Ingests raw events from several independent sources -- a job board scrape,
a funding news feed, a tech-stack tracker, and website analytics --
normalizes them into one unified `Signal` schema, removes duplicates (the
same event often gets scraped twice from different job boards), and rolls
them up into a per-company signal-strength score.

See [`example_output.md`](./example_output.md) for a full run, including a
worked example of the dedup step catching a duplicate hiring post.

## Why this is a separate project from `signal-prospecting`

This is the detection/normalization layer: turn messy, source-specific raw
events into one clean shape. [`signal-prospecting`](https://github.com/highhsenberg/signal-prospecting)
is the scoring/qualification/routing layer that consumes signals in that
shape. Splitting them means either can change independently.

## Install

No external dependencies beyond the Python standard library.

## Usage

```bash
python detect_signals.py --sources-dir sample_sources
```

## Project structure

```
detect_signals.py                          -- normalize + dedupe + roll-up
sample_sources/hiring_postings.json         -- raw job board scrape (includes a duplicate)
sample_sources/funding_news.json            -- raw funding announcements
sample_sources/tech_changes.json            -- raw tech-stack tracker events
sample_sources/website_activity.json        -- raw website analytics
example_output.md                           -- full example run with reasoning
```

## Limitations / next steps (why this is marked in-progress)

- Sources are static JSON files; a production version polls each source on
  a schedule (or receives webhooks) instead of reading from disk.
- No persistent store yet -- every run re-processes all raw records. Adding
  a signals table (with a `first_seen_at` per signal) is the next step,
  which would also make true "new signal since last run" detection
  possible instead of re-deriving everything each time.
- Dedup is exact-match on `(company, signal_type, detail)`; near-duplicate
  detection (e.g. the same role posted with slightly different wording)
  would need fuzzy matching.
