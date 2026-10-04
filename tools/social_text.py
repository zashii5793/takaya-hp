#!/usr/bin/env python3
"""ブログ記事から、SNS用の文章と動画の文言をつくる。

Claude に記事を読ませて、X用・Instagram用の文章と、30秒動画に出す
文言を書いてもらう。API が使えないときは、記事の見出しと書き出しから
決まった形に当てはめる（止まらないようにするため）。
"""
import os
import re

MODEL = "claude-opus-5-5"
MAX_BODY = 6000          # 記事本文をこの長さまでにして渡す
X_LIMIT = 100            # X本文の上限。URL（23字）とハッシュタグぶんを残す


SYSTEM = """あなたは岡山市中区の自動車整備・販売会社「タカヤモーター株式会社」の
広報担当です。自社ブログの記事をもとに、SNSの投稿文と短い動画の文言を書きます。

守ること：
- 読み手は岡山市周辺にお住まいの、クルマを持っている一般の方です
- 専門用語はかみくだき、具体的に書く
- 誇張しない。記事に書いていないことは書かない
- 「〜しましょう」「〜ですね」の連発や、感嘆符の多用は避ける
- 絵文字は使わない
- 事故の第一報は保険会社へ、という当社の方針に反する書き方はしない
- 価格や数字は、記事に書かれているものだけを使う"""

PROMPT = """次のブログ記事から、SNS投稿用の文章と動画の文言を作ってください。

タイトル: {title}
カテゴリ: {cat}
記事URL: {url}

本文:
{body}

作るもの：

1. x_text — X（旧Twitter）の本文。{x_limit}文字以内。記事の要点が分かり、
   続きを読みたくなる書き出し。URLとハッシュタグは入れない（別で足します）。

2. ig_caption — Instagramのキャプション。200〜300文字。Xより少し丁寧に、
   記事の中身を3〜4文で。最後に「詳しくはプロフィールのリンクから」と添える。
   ハッシュタグは入れない（別で足します）。

3. hashtags — ハッシュタグを5〜8個。#は付けない。日本語のみ。
   「岡山」「車検」など、地域と内容が分かるもの。

4. video_title — 動画の1枚目に出す見出し。20文字以内。記事の核心を一言で。

5. video_points — 動画の2〜4枚目に出す要点。ちょうど3つ。
   各24文字以内。記事の中身から、読み手の役に立つことを選ぶ。

6. video_closing — 動画の最後に出す一言。16文字以内。"""


def _sentences(text):
    """本文を文の区切りで分ける。動画の文言を途中で切らないため"""
    out = []
    for part in re.split(r"(?<=[。！？])", (text or "").replace("\n", "")):
        part = part.strip()
        if part:
            out.append(part)
    return out


def _fallback(post, url):
    """APIが使えないときの、決まった形"""
    title = re.sub(r"\.vol\d+.*$", "", post["title"]).strip()
    body = post.get("plain", "")
    sents = _sentences(body)
    lead = sents[0] if sents else body[:60]
    points = []
    for s in sents:
        if len(s) <= 26:
            points.append(s)
        if len(points) == 3:
            break
    while len(points) < 3:
        points.append("")
    return {
        "x_text": f"{title}｜{lead}"[:X_LIMIT],
        "ig_caption": (f"{title}\n\n{' '.join(sents[:4])[:280]}\n\n"
                       "詳しくはプロフィールのリンクから。"),
        "hashtags": ["岡山", "岡山市", "車検", "カーライフ", "タカヤモーター"],
        "video_title": title[:22],
        "video_points": points,
        "video_closing": "続きはHPで",
        "by_ai": False,
    }


def build(post, url, body_text):
    """post は posts.json の1件。body_text は記事の本文（文字だけ）"""
    post = dict(post, plain=body_text)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  ANTHROPIC_API_KEY が無いので、決まった形で作ります")
        return _fallback(post, url)
    try:
        import anthropic
        from pydantic import BaseModel

        class Social(BaseModel):
            x_text: str
            ig_caption: str
            hashtags: list[str]
            video_title: str
            video_points: list[str]
            video_closing: str

        client = anthropic.Anthropic()
        res = client.messages.parse(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            messages=[{"role": "user", "content": PROMPT.format(
                title=post["title"], cat=post.get("cat", "お知らせ"), url=url,
                x_limit=X_LIMIT, body=body_text[:MAX_BODY])}],
            output_format=Social,
        )
        out = res.parsed_output.model_dump()
        u = res.usage
        print(f"  Claudeで作りました（入力 {u.input_tokens} / 出力 {u.output_tokens} トークン）")
    except Exception as e:
        print(f"  Claudeが使えませんでした（{type(e).__name__}: {e}）")
        print("  決まった形で作ります")
        return _fallback(post, url)

    # 長さの保険。モデルが守らなかったときに、ここで整える
    out["x_text"] = out["x_text"].strip()[:X_LIMIT]
    out["video_title"] = out["video_title"].strip()[:22]
    pts = [p.strip()[:26] for p in out["video_points"] if p.strip()][:3]
    while len(pts) < 3:
        pts.append("")
    out["video_points"] = pts
    out["video_closing"] = out["video_closing"].strip()[:18]
    out["hashtags"] = [h.lstrip("#").strip() for h in out["hashtags"] if h.strip()][:8]
    out["by_ai"] = True
    return out
