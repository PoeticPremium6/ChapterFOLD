#!/usr/bin/env python3
"""
Fetch the best downloadable file from an AO3 work page.

Defaults:
- Normalizes chapter URLs to work URLs
- Prefers epub > html > pdf
- Saves with a safe filename

Usage:
    python ao3_fetch.py "https://archiveofourown.org/works/3171550/chapters/6887378"
    python ao3_fetch.py "https://archiveofourown.org/works/3171550" --prefer epub html pdf
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def safe_filename(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name[:180] or "ao3_work"


def normalize_work_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    m = re.search(r"^/works/(\d+)", path)
    if not m:
        raise ValueError(f"Could not determine AO3 work ID from URL: {url}")
    work_id = m.group(1)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or "archiveofourown.org"
    return f"{scheme}://{netloc}/works/{work_id}"


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            ),
            "Accept-Language": "en-GB,en;q=0.9",
        }
    )
    return session


def fetch_html(session: requests.Session, url: str) -> str:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_title_author(soup: BeautifulSoup) -> Tuple[str, str]:
    title = None
    author = None

    title_el = soup.select_one("h2.title.heading")
    if title_el:
        title = title_el.get_text(" ", strip=True)

    author_el = soup.select_one("h3.byline.heading a[rel='author']")
    if author_el:
        author = author_el.get_text(" ", strip=True)

    if not title:
        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content"):
            title = og["content"].strip()

    if not title:
        title = "AO3 Work"
    if not author:
        author = "Unknown Author"

    return title, author


def parse_download_links(soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
    formats: Dict[str, str] = {}

    for a in soup.select("li.download a, .download a, a"):
        text = a.get_text(" ", strip=True).lower()
        href = a.get("href")
        if not href:
            continue

        full_url = urljoin(base_url, href)

        for fmt in ("epub", "html", "pdf", "mobi", "azw3"):
            if fmt in text or fmt in href.lower():
                formats[fmt] = full_url

    return formats


def pick_format(available: Dict[str, str], preferred: List[str]) -> Tuple[str, str]:
    for fmt in preferred:
        fmt = fmt.lower()
        if fmt in available:
            return fmt, available[fmt]
    raise RuntimeError(f"No preferred format found. Available: {sorted(available.keys())}")


def download_file(
    session: requests.Session,
    url: str,
    out_dir: Path,
    filename_stem: str,
    fmt: str,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{filename_stem}.{fmt}"

    with session.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)

    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="AO3 chapter URL or work URL")
    parser.add_argument("--outdir", default="downloads", help="Directory to save file into")
    parser.add_argument(
        "--prefer",
        nargs="+",
        default=["epub", "html", "pdf"],
        help="Preferred download formats in order",
    )
    args = parser.parse_args()

    try:
        work_url = normalize_work_url(args.url)
    except Exception as e:
        print(f"URL error: {e}", file=sys.stderr)
        return 2

    session = build_session()

    try:
        html = fetch_html(session, work_url)
    except Exception as e:
        print(f"Failed to fetch AO3 work page: {e}", file=sys.stderr)
        return 3

    soup = BeautifulSoup(html, "lxml")
    title, author = parse_title_author(soup)
    download_links = parse_download_links(soup, work_url)

    if not download_links:
        print(
            "No download links found. The work may be restricted or require login.",
            file=sys.stderr,
        )
        return 4

    try:
        fmt, download_url = pick_format(download_links, args.prefer)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 5

    stem = safe_filename(f"{author} - {title}")
    out_path = download_file(session, download_url, Path(args.outdir), stem, fmt)

    print(f"Title:   {title}")
    print(f"Author:  {author}")
    print(f"Format:  {fmt}")
    print(f"Saved:   {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
