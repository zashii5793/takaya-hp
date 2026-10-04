#!/usr/bin/env python3
"""作った動画と文章を Instagram へリールとして投稿する。

必要な Secrets
  IG_USER_ID         Instagram プロアカウントの ID（数字）
  IG_ACCESS_TOKEN    長期アクセストークン（約60日で切れる。切れたら取り直す）
  IG_API_VERSION     省略可。既定は v23.0。Meta 側で古くなったら上げる

前提（Meta の決まり）
  - Instagram が「プロアカウント」になっていること
  - Facebookページと連携されていること
  - Meta開発者アプリに instagram_business_content_publish の権限があること
  - 動画が公開URLから取得できること（当社は さくら のサーバーに置いている）

流れ
  1. 動画URLを渡して「入れ物」を作る
  2. 変換が終わるまで待つ（status_code が FINISHED になるまで）
  3. 公開する
"""
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT_DIR = ROOT / "assets" / "social"
STATE = ROOT / ".state" / "social.json"
PENDING = ROOT / ".state" / "pending.txt"
VER = os.environ.get("IG_API_VERSION", "v23.0")
BASE = f"https://graph.facebook.com/{VER}"
WAIT_SEC = 15
WAIT_TRIES = 24          # 15秒 × 24 = 最大6分待つ


def _wait_ready(requests, cid, token):
    for i in range(WAIT_TRIES):
        time.sleep(WAIT_SEC)
        r = requests.get(f"{BASE}/{cid}",
                         params={"fields": "status_code,status", "access_token": token},
                         timeout=30)
        if r.status_code != 200:
            return False, f"状態が取れません HTTP {r.status_code} {r.text[:200]}"
        st = r.json().get("status_code", "")
        if st == "FINISHED":
            return True, ""
        if st == "ERROR":
            return False, f"変換に失敗しました: {r.json().get('status', '')}"
        print(f"    変換中…（{(i + 1) * WAIT_SEC}秒）")
    return False, "変換が終わりませんでした（6分待っても FINISHED になりません）"


def main():
    token = os.environ.get("IG_ACCESS_TOKEN")
    ig_id = os.environ.get("IG_USER_ID")
    if not token or not ig_id:
        print("Instagramの設定が無いので、投稿しません"
              "（IG_USER_ID / IG_ACCESS_TOKEN）")
        return 0
    if not PENDING.is_file():
        print("投稿するものがありません")
        return 0
    slugs = [s for s in PENDING.read_text(encoding="utf-8").split("\n") if s.strip()]
    if not slugs:
        print("投稿するものがありません")
        return 0

    import requests
    with open(STATE, encoding="utf-8") as f:
        state = json.load(f)
    state.setdefault("instagram", [])
    posted = set(state["instagram"])

    failed = 0
    for slug in slugs:
        if slug in posted:
            print(f"  {slug}: 投稿済みなので飛ばします")
            continue
        f = TEXT_DIR / f"{slug}.json"
        if not f.is_file():
            print(f"  {slug}: 文章が見つかりません")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("video_ok"):
            print(f"  {slug}: 動画が作れていないので飛ばします")
            continue

        print(f"  {slug}: 入れ物を作ります")
        r = requests.post(f"{BASE}/{ig_id}/media", data={
            "media_type": "REELS", "video_url": d["video_url"],
            "caption": d["ig_post"], "share_to_feed": "true",
            "access_token": token}, timeout=60)
        if r.status_code != 200:
            print(f"    作れませんでした HTTP {r.status_code} {r.text[:400]}")
            if r.status_code in (190, 401) or "expired" in r.text.lower():
                print("    → トークンが切れている可能性があります。取り直してください")
            failed += 1
            continue
        cid = r.json().get("id")

        ok, why = _wait_ready(requests, cid, token)
        if not ok:
            print(f"    {why}")
            failed += 1
            continue

        r = requests.post(f"{BASE}/{ig_id}/media_publish",
                          data={"creation_id": cid, "access_token": token}, timeout=60)
        if r.status_code == 200:
            print(f"    投稿しました（ID {r.json().get('id', '')}）")
            posted.add(slug)
        else:
            print(f"    公開できませんでした HTTP {r.status_code} {r.text[:400]}")
            failed += 1

    state["instagram"] = sorted(posted)
    with open(STATE, "w", encoding="utf-8") as fp:
        json.dump(state, fp, ensure_ascii=False, indent=1)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
