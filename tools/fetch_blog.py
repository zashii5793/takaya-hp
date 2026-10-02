#!/usr/bin/env python3
"""Googleブログ（Blogger）の記事を取り込んで、タカヤHPの記事ページを作れるようにする。

使い方（インターネットに出られる端末で）:
    python3 tools/fetch_blog.py          # 記事を取り込む
    python3 tools/build_site.py          # 記事ページを作る
    site/ をサーバーへアップロード

取り込んだ記事は assets/blog/posts.json に入る。
取り込みに失敗しても前回ぶんが残るので、ビルドは通る。

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
URL = (f"https://www.blogger.com/feeds/{BLOG_ID}/posts/default"
       "?alt=json&max-results=500")
DEST = os.path.join(ROOT, "assets", "blog", "posts.json")
TIMEOUT = 30


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
    print(f"取り込み元: {URL}")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "takaya-hp build"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            feed = json.loads(r.read().decode("utf-8", "replace"))["feed"]
    except Exception as e:
        print(f"  取り込めませんでした: {e}")
        print("  前回ぶんをそのまま使います（site/ は作り直せます）")
        return 1

    posts, seen = [], set()
    for e in feed.get("entry", []):
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
