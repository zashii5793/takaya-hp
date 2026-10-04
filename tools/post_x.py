#!/usr/bin/env python3
"""作った文章を X へ投稿する。

必要な Secrets（GitHub の Settings → Secrets and variables → Actions）
  X_API_KEY / X_API_SECRET            アプリの Key と Secret
  X_ACCESS_TOKEN / X_ACCESS_SECRET    アカウントの Access Token と Secret
    ※ アプリの権限を「Read and write」にしてから Access Token を作り直すこと。
       Read only のまま作ったトークンでは 403 になる。

投稿できた記事は .state/social.json の "x" に記録し、二重投稿を防ぐ。
"""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT_DIR = ROOT / "assets" / "social"
STATE = ROOT / ".state" / "social.json"
PENDING = ROOT / ".state" / "pending.txt"
ENDPOINT = "https://api.x.com/2/tweets"
KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")


def main():
    missing = [k for k in KEYS if not os.environ.get(k)]
    if missing:
        print(f"Xの鍵がそろっていないので、投稿しません（未設定: {', '.join(missing)}）")
        return 0
    if not PENDING.is_file():
        print("投稿するものがありません")
        return 0
    slugs = [s for s in PENDING.read_text(encoding="utf-8").split("\n") if s.strip()]
    if not slugs:
        print("投稿するものがありません")
        return 0

    from requests_oauthlib import OAuth1Session
    with open(STATE, encoding="utf-8") as f:
        state = json.load(f)
    state.setdefault("x", [])
    posted = set(state["x"])

    sess = OAuth1Session(
        os.environ["X_API_KEY"], client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_SECRET"])

    failed = 0
    for slug in slugs:
        if slug in posted:
            print(f"  {slug}: 投稿済みなので飛ばします")
            continue
        f = TEXT_DIR / f"{slug}.json"
        if not f.is_file():
            print(f"  {slug}: 文章が見つかりません")
            continue
        text = json.loads(f.read_text(encoding="utf-8"))["x_post"]
        try:
            r = sess.post(ENDPOINT, json={"text": text}, timeout=30)
        except Exception as e:
            print(f"  {slug}: つながりませんでした（{type(e).__name__}: {e}）")
            failed += 1
            continue
        if r.status_code == 201:
            tid = (r.json().get("data") or {}).get("id", "")
            print(f"  {slug}: 投稿しました https://x.com/i/web/status/{tid}")
            posted.add(slug)
        else:
            print(f"  {slug}: 投稿できませんでした HTTP {r.status_code} {r.text[:300]}")
            if r.status_code == 403:
                print("    → アプリの権限を Read and write にして、"
                      "Access Token を作り直してください")
            failed += 1

    state["x"] = sorted(posted)
    with open(STATE, "w", encoding="utf-8") as fp:
        json.dump(state, fp, ensure_ascii=False, indent=1)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
