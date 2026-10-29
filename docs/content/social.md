# SNS連携（ブログ → X・Instagram）

新しいブログ記事が出たら、X と Instagram へ自動で投稿する。

```
Googleブログに投稿
   ↓ 毎朝6時（日本時間）
記事をタカヤHPへ取り込む
   ↓
Claude が記事を読んで、X用・Instagram用の文章と動画の文言を書く
   ↓
30秒の縦動画をつくる（文字だけ・1080×1920）
   ↓
さくらへ転送（動画も公開URLに置かれる）
   ↓
X へ投稿 ／ Instagram へリール投稿
```

## 二重投稿を防ぐしくみ

`.state/social.json` に「どこまで投稿したか」を記録し、毎回この記録に書き戻す。

**初回は1件も投稿しない。** 記録ファイルが無い1回目は、そのとき存在する記事を
すべて「投稿済み」として記録するだけで終わる。これが無いと、167件の記事が
いっぺんに流れてしまう。

さらに2つの歯止めがある。

| 決まり | 既定 | 変え方 |
|---|---|---|
| 1回の実行で扱う記事の数 | 1件 | 環境変数 `SOCIAL_MAX_PER_RUN` |
| 古い記事は扱わない | 7日より前 | 環境変数 `SOCIAL_MAX_AGE_DAYS` |

## 手で止めたいとき

Actions の「Run workflow」で **「SNSへの投稿を飛ばす」にチェック**を入れると、
サイトの公開だけ行う。

---

# 必要な設定

GitHub → **Settings** → **Secrets and variables** → **Actions**

## 1. 文章を書かせる（Claude）

| 名前 | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic の APIキー（console.anthropic.com で発行） |

**未設定でも動く。** その場合は記事の見出しと最初の数文から、決まった形に
当てはめた文章になる（やや機械的）。

費用の目安：1記事あたり数円。モデルは `claude-opus-5-5`。

## 2. X（旧Twitter）

developer.x.com でアプリを作り、4つの値を登録する。

| 名前 | どこで取るか |
|---|---|
| `X_API_KEY` | アプリの Consumer Keys → API Key |
| `X_API_SECRET` | 同 API Key Secret |
| `X_ACCESS_TOKEN` | Authentication Tokens → Access Token |
| `X_ACCESS_SECRET` | 同 Access Token Secret |

> ⚠️ **順番に注意。** 先にアプリの権限を **Read and write** に変更してから、
> Access Token を**作り直す**こと。Read only のまま作ったトークンでは、
> 投稿時に 403 になる。

無料枠で月500投稿まで。1日1記事なら十分。

## 3. Instagram

Instagram は外部からの投稿に条件が多い。**この4つを順にそろえる。**

1. Instagram を **プロアカウント**（ビジネス or クリエイター）にする
2. **Facebookページ**と連携する
3. developers.facebook.com でアプリを作り、
   **instagram_business_content_publish** の権限を付ける
4. 長期アクセストークンを発行する

| 名前 | 値 |
|---|---|
| `IG_USER_ID` | Instagram プロアカウントの ID（数字） |
| `IG_ACCESS_TOKEN` | 長期アクセストークン |
| `IG_API_VERSION` | 省略可。既定 `v23.0`。Meta側で古くなったら上げる |

> ⚠️ **トークンは約60日で切れる。** 切れると Instagram への投稿だけが
> 止まる（サイトの公開と X への投稿は続く）。実行の記録に
> 「トークンが切れている可能性があります」と出るので、そのとき取り直す。

---

# 作られるもの

| 場所 | 中身 |
|---|---|
| `assets/social/<slug>.json` | X用・Instagram用の文章、ハッシュタグ、動画の文言 |
| `site/social/<slug>.mp4` | 30秒の縦動画（1080×1920） |
| `.state/social.json` | どこまで投稿したかの記録 |

文章と動画はリポジトリに残さない（毎回つくり直す）。記録だけ残す。

## 動画の中身

| 枚 | 内容 | 秒 |
|---|---|---|
| 1 | タイトル（赤地・白文字） | 6 |
| 2〜4 | 要点3つ（白地・番号つき） | 各6 |
| 5 | 締めの一言＋ URL（赤地） | 6 |

合計30秒。Instagram のリールは音声トラックが無いと弾かれることがあるため、
無音のトラックを入れてある。

---

# うまくいかないとき

実行の記録（Actions のログ）を見る。

| 記録 | 原因と対処 |
|---|---|
| `ANTHROPIC_API_KEY が無いので、決まった形で作ります` | キー未設定。文章は出るが機械的 |
| `ffmpeg が無いので動画は作りません` | 支度の工程が失敗している。ログの上の方を見る |
| `HTTP 403`（X） | アプリの権限が Read only。権限を変えてトークンを作り直す |
| `トークンが切れている可能性があります`（Instagram） | 長期トークンを取り直す |
| `変換が終わりませんでした` | 動画がMetaの条件に合っていない。サイズ・長さを確認 |
| `初回のため、既存 N件を投稿済みとして記録しました` | 正常。次回から新着だけを扱う |

## 手で試す

```
python3 tools/fetch_blog.py      # 記事を取り込む
python3 tools/make_social.py     # 文章と動画をつくる（投稿はしない）
python3 tools/post_x.py          # Xへ投稿
python3 tools/post_instagram.py  # Instagramへ投稿
```

`tools/make_social.py` までなら投稿されないので、中身の確認に使える。
