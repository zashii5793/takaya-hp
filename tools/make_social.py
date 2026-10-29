#!/usr/bin/env python3
"""新しいブログ記事から、SNS投稿の材料をつくる。

  入力  assets/blog/posts.json（tools/fetch_blog.py が作る）
  出力  assets/social/<slug>.json   X用・Instagram用の文章
        site/social/<slug>.mp4      30秒の縦動画
        .state/social.json          どこまで投稿したかの記録

安全のための決まりごと
  1. 記録ファイルが無い初回は、既存の記事をすべて「投稿済み」として
     記録するだけで、1件も投稿しない（167件が一度に流れるのを防ぐ）
  2. 1回の実行で扱うのは MAX_PER_RUN 件まで
  3. 公開から MAX_AGE_DAYS 日より古い記事は扱わない
"""
import datetime
import html
import json
import os
import pathlib
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import social_text
import social_video

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "assets" / "blog" / "posts.json"
TEXT_DIR = ROOT / "assets" / "social"
VIDEO_DIR = ROOT / "site" / "social"
STATE = ROOT / ".state" / "social.json"
SITE_URL = "https://www.takayagroup.co.jp"

MAX_PER_RUN = int(os.environ.get("SOCIAL_MAX_PER_RUN", "1"))
MAX_AGE_DAYS = int(os.environ.get("SOCIAL_MAX_AGE_DAYS", "7"))


class _Strip(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buf = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("p", "br", "div", "li", "h2", "h3", "h4"):
            self.buf.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.buf.append(d)


def plain(raw):
    p = _Strip()
    try:
        p.feed(raw or "")
    except Exception:
        return re.sub(r"<[^>]+>", " ", raw or "")
    t = html.unescape("".join(p.buf))
    return re.sub(r"\n{2,}", "\n", re.sub(r"[ \t　]+", " ", t)).strip()


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        return None
    for k in ("prepared", "x", "instagram"):
        s.setdefault(k, [])
    return s


def save_state(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)


def main():
    try:
        with open(POSTS, encoding="utf-8") as f:
            posts = json.load(f)
    except (OSError, ValueError) as e:
        print(f"記事が読めません: {e}")
        return 1
    if not posts:
        print("記事が0件なので、何もしません")
        return 0

    state = load_state()
    if state is None:
        # 初回。既存ぶんはすべて投稿済みとして記録し、1件も投稿しない
        slugs = [p["slug"] for p in posts]
        save_state({"prepared": slugs, "x": slugs, "instagram": slugs,
                    "note": "初回のため、既存の記事はすべて投稿済みとして記録しました"})
        print(f"初回のため、既存 {len(slugs)}件を投稿済みとして記録しました（投稿はしません）")
        print("次回から、新しく増えた記事だけを扱います")
        return 0

    done = set(state["prepared"])
    today = datetime.date.today()
    new = []
    for p in posts:
        if p["slug"] in done:
            continue
        try:
            d = datetime.date.fromisoformat((p.get("published") or "")[:10])
        except ValueError:
            continue
        age = (today - d).days
        if age > MAX_AGE_DAYS:
            print(f"  見送り（{age}日前の記事）: {p['title'][:40]}")
            done.add(p["slug"])          # 古いものは以後の判定から外す
            continue
        new.append(p)

    state["prepared"] = sorted(done)
    if not new:
        save_state(state)
        print("新しい記事はありません")
        return 0

    new.sort(key=lambda p: p.get("published", ""))   # 古い順に処理する
    target = new[:MAX_PER_RUN]
    if len(new) > MAX_PER_RUN:
        print(f"新しい記事が {len(new)}件ありますが、今回は {MAX_PER_RUN}件だけ扱います")

    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    for p in target:
        slug = p["slug"]
        url = f"{SITE_URL}/blog/{slug}.html"
        print(f"\n■ {p['title']}")
        body = plain(p.get("content"))
        t = social_text.build(
            {"title": p["title"], "cat": (p.get("categories") or ["お知らせ"])[0]},
            url, body)

        mp4 = VIDEO_DIR / f"{slug}.mp4"
        t["video_ok"] = social_video.build(
            t["video_title"], t["video_points"], t["video_closing"], mp4)
        t["slug"] = slug
        t["url"] = url
        t["title"] = p["title"]
        t["video_url"] = f"{SITE_URL}/social/{slug}.mp4"
        tags = " ".join("#" + h for h in t["hashtags"])
        t["x_post"] = f"{t['x_text']}\n{url}\n{tags}"
        t["ig_post"] = f"{t['ig_caption']}\n\n{tags}"

        with open(TEXT_DIR / f"{slug}.json", "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False, indent=1)
        state["prepared"] = sorted(set(state["prepared"]) | {slug})
        print(f"  X用: {t['x_text'][:40]}…")
        print(f"  タグ: {tags}")

    save_state(state)
    with open(ROOT / ".state" / "pending.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(p["slug"] for p in target))
    print(f"\n{len(target)}件ぶんの材料を作りました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
