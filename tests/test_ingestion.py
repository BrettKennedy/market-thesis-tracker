from __future__ import annotations

import json
from pathlib import Path

import feedparser
from ingest_news import build_news_events
from ingest_sec import build_company_ticker_map, build_filing_events


def test_build_news_events_handles_matched_and_unmatched_entries(repo_root):
    feed_text = (repo_root / "tests" / "fixtures" / "news_feed.xml").read_text(encoding="utf-8")
    parsed = feedparser.parse(feed_text)

    events = build_news_events(
        parsed,
        feed_url="https://example.com/test-feed",
        local_path=Path("/tmp/news_snapshot.jsonl"),
        tracked_tickers={"VRT"},
        theme_map={"VRT": ["AI Infrastructure Buildout Is Durable"]},
        limit=10,
        fallback_date="2026-03-10",
    )

    assert any(event.ticker == "VRT" for event in events)
    assert any(event.ticker is None for event in events)
    assert events[0].event_date == "2026-03-09"


def test_build_news_events_normalizes_rfc2822_dates():
    parsed = feedparser.parse(
        """
        <rss version="2.0">
          <channel>
            <item>
              <title>VRT expands AI cooling capacity</title>
              <description>VRT adds capacity.</description>
              <pubDate>Mon, 10 Mar 2026 12:00:00 GMT</pubDate>
              <link>https://example.com/vrt</link>
            </item>
          </channel>
        </rss>
        """
    )

    events = build_news_events(
        parsed,
        feed_url="https://example.com/test-feed",
        local_path=Path("/tmp/news_snapshot.jsonl"),
        tracked_tickers={"VRT"},
        theme_map={"VRT": ["AI Infrastructure Buildout Is Durable"]},
        limit=10,
        fallback_date="2026-03-01",
    )

    assert len(events) == 1
    assert events[0].event_date == "2026-03-10"


def test_build_filing_events_uses_sec_payload(repo_root):
    company_payload = json.loads(
        (repo_root / "tests" / "fixtures" / "sec_company_tickers.json").read_text(encoding="utf-8")
    )
    submissions_payload = json.loads(
        (repo_root / "tests" / "fixtures" / "sec_submissions_vrt.json").read_text(encoding="utf-8")
    )

    ticker_map = build_company_ticker_map(company_payload)
    events = build_filing_events(
        "VRT",
        ["AI Infrastructure Buildout Is Durable"],
        submissions_payload,
        fallback_date="2026-03-10",
        limit=2,
        local_path=Path("/tmp/sec_snapshot.jsonl"),
    )

    assert ticker_map["VRT"] == "0001884082"
    assert len(events) == 2
    assert events[0].event_type == "sec_10-q"
    assert "Archives/edgar/data/1884082" in (events[0].url or "")
