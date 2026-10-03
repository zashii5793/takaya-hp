#!/usr/bin/env python3
"""Googleブログ（Blogger）の記事を取り込んで、タカヤHPの記事ページを作れるようにする。

使い方（インターネットに出られる端末で）:
    python3 tools/fetch_blog.py          # 記事を取り込む
    python3 tools/build_site.py          # 記事ページを作る
    site/ をサーバーへアップロード

取り込んだ記事は assets/blog/posts.json に入る。
取り込みに失敗しても前回ぶんが残るので、ビルドは通る。

Blogger は1回のお願いでは全部返さないことがあるため、ブログ側が申告する
総数（openSearch$totalResults）を見ながら、最後まで順に取りに行く。
取れた数が総数に足りないときは、その旨を表示する。

なお、画面での自動表示（blog-feed.js）はこれとは別で、こちらを動かさなくても
新しい記事はお知らせ欄に出る。この取り込みは「記事本文をタカヤHP側に持つ」ためのもの。
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BLOG_ID = "2118329274297060498"
FEED = f"https://www.blogger.com/feeds/{BLOG_ID}/posts/default"
PAGE = 150          # 1回に取る件数。Blogger は大きすぎると黙って減らして返すことがある
MAX_PAGES = 40      # 無限ループよけ（150×40 = 6000件まで）
DEST = os.path.join(ROOT, "assets", "blog", "posts.json")
TIMEOUT = 30


def page_url(start):
    return f"{FEED}?alt=json&max-results={PAGE}&start-index={start}"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "takaya-hp build"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))["feed"]


def total_of(feed):
    """ブログ側が申告している記事の総数。取りこぼしの判定に使う"""
    try:
        return int((feed.get("openSearch$totalResults") or {}).get("$t"))
    except (TypeError, ValueError):
        return None


def permalink(links):
    for l in links or []:
        if l.get("rel") == "alternate" and l.get("type") == "text/html":
            return l.get("href", "")
    return ""


def slug_of(url, post_id):
    """記事のファイル名。Blogger のURLの末尾を使う（例 .../2024/05/syaken.html → syaken）"""
    m = re.search(r"/([^/]+)\.html$", url or "")
    s = m.group(1) if m else ""
    s = re.sub(r"[^a-zA-Z0-9\-_]", "-", s).strip("-").lower()
    if not s or s == "blog-post":
        s = "post-" + re.sub(r"\D", "", post_id or "")[-10:]
    return s[:60] or "post"


def main():
    print(f"取り込み元: {FEED}")

    # Blogger は1回のお願いでは全部返さない。最後まで順に取りに行く
    entries, total, start = [], None, 1
    try:
        for _ in range(MAX_PAGES):
            feed = fetch(page_url(start))
            if total is None:
                total = total_of(feed)
                print(f"  ブログ側の申告: {total}件" if total is not None
                      else "  ブログ側の総数は申告されませんでした")
            got = feed.get("entry") or []
            print(f"  {start}件目から {len(got)}件 受け取りました")
            if not got:
                break
            entries += got
            start += len(got)
            if total is not None and len(entries) >= total:
                break
    except Exception as e:
        print(f"  取り込めませんでした: {e}")
        print("  前回ぶんをそのまま使います（site/ は作り直せます）")
        return 1

    if total is not None and len(entries) < total:
        print(f"  ※ {total}件あるはずが {len(entries)}件しか取れていません。"
              f"取りこぼしの可能性があります")

    posts, seen = [], set()
    for e in entries:
        url = permalink(e.get("link"))
        if not url:
            continue
        pid = (e.get("id") or {}).get("$t", "")
        s = slug_of(url, pid)
        while s in seen:                      # 同じファイル名が出たら番号を足す
            s += "-2"
        seen.add(s)
        posts.append({
            "slug": s,
            "title": (e.get("title") or {}).get("$t", "").strip() or "（無題）",
            "published": (e.get("published") or {}).get("$t", ""),
            "updated": (e.get("updated") or {}).get("$t", ""),
            "categories": [c.get("term", "") for c in e.get("category", []) if c.get("term")],
            "content": (e.get("content") or e.get("summary") or {}).get("$t", ""),
            "source": url,
        })

    posts.sort(key=lambda p: p["published"], reverse=True)
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=1)
    print(f"  {len(posts)}件を保存しました → {os.path.relpath(DEST, ROOT)}")
    if posts:
        print(f"  最新: {posts[0]['published'][:10]}  {posts[0]['title']}")
        print(f"  最古: {posts[-1]['published'][:10]}  {posts[-1]['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
