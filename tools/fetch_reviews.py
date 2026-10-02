#!/usr/bin/env python3
"""口コミ収集サービス（reviews.aiobridge.jp）から、公開済みの口コミを取り込む。

使い方（インターネットに出られる端末で）:
    python3 tools/fetch_reviews.py
    python3 tools/build_site.py
    site/ をサーバーへアップロード

なぜ取り込む方式にしているか:
    貼り付けるだけの「埋め込みタグ」は JavaScript で口コミを出すため、
    JavaScript を動かさない AI の巡回ロボットには中身が見えない。
    ここで HTML として取り込み、ページ本文に書き出しておくことで、
    検索にも AI にも読まれる形にしている。

口コミが増えたら、もう一度これを実行してビルドし直す。
"""
import os
import re
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SLUG = "takaya-group"
URL = f"https://reviews.aiobridge.jp/embed/{SLUG}.html"
DEST = os.path.join(ROOT, "assets", "reviews", "embed.html")
TIMEOUT = 20


def main():
    print(f"取り込み元: {URL}")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "takaya-hp build"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace").strip()
    except Exception as e:
        print(f"  取り込めませんでした: {e}")
        print("  前回ぶんをそのまま使います（site/ は作り直せます）")
        return 1

    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    before = ""
    if os.path.isfile(DEST):
        with open(DEST, encoding="utf-8") as f:
            before = f.read().strip()
    with open(DEST, "w", encoding="utf-8") as f:
        f.write(body + ("\n" if body else ""))

    if not body:
        print("  公開ぶんの口コミはまだありません（0件）。口コミ欄は出しません")
    else:
        n = len(re.findall(r'itemprop="review"|class="[^"]*review', body))
        print(f"  {len(body)}文字を保存しました（口コミらしき箇所 {n} 件）")
        print(f"  前回と{'同じ' if body == before else '違う'}内容です")

    # 構造化データが入っている場合は、Google の方針に触れる可能性があるので知らせる
    if re.search(r'"@type"\s*:\s*"(Review|AggregateRating)"', body):
        print()
        print("  ※ この HTML には Review／AggregateRating の構造化データが入っています。")
        print("     自社サイトに自社の評価を出すマークアップは、Google の検索結果では")
        print("     星の表示に使われません（自作自演の口コミとみなされる方針のため）。")
        print("     AI に読ませる目的なら有効ですが、Google 対策としては効きません。")
        print("     外す場合は、この節だけ取り除いてから保存してください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
