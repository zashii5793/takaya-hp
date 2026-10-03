# 自動公開（GitHub → さくら）

`main` に push すると、GitHub Actions がさくらのレンタルサーバーへ自動で転送する。
設定は `.github/workflows/deploy.yml`。

## 最初に1回だけ必要な設定

GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| 名前 | 値 |
|---|---|
| `FTP_SERVER` | `limegopher49.sakura.ne.jp` |
| `FTP_USERNAME` | `limegopher49` |
| `FTP_PASSWORD` | サーバーパスワード |

登録後は画面にも実行ログにも出ない。**パスワードはリポジトリに書かないこと。**

## 動くタイミング

- `main` に push したとき（`site/` `tools/` `assets/` のいずれかが変わったとき）
- **毎日 朝6時（日本時間）** — 新しいブログ記事を取り込んで反映するため
- Actions の画面で「Run workflow」を押したとき

## 流れ

1. Googleブログの記事を取り込む（`tools/fetch_blog.py`）
2. 口コミを取り込む（`tools/fetch_reviews.py`）
3. サイトを作る（`tools/build_site.py`）
4. `index.html` と `site.css` があるか確かめる
5. `site/` の中身を `~/www/` へ転送する（**変わったファイルだけ**送る）

1と2は、取り込めなくても公開を止めない（前回ぶんのまま進む）。

これで「Googleブログに投稿 → 翌朝6時にはタカヤHPの記事ページになっている」が自動で回る。
すぐ反映したいときは「Run workflow」を押す。

## 気をつけること

- **`~/www` は転送元と同じ状態に保たれる。** `site/` に無いファイルをサーバーに手で置くと、
  次の転送で消える可能性がある。置きたいものは `site/` に入れてリポジトリで管理する
- 転送の控え（`.ftp-deploy-state.json`）がサーバーに置かれる。`.htaccess` で
  ドットで始まるファイルを外から見せない設定にしてある
- 転送は **lftp** で行う。まず暗号化（FTPS）で試し、通らなければ平文のFTPで送り直す。
  さくらは FTPS が通らないことがあるため。実行ログにどちらで送ったかが出る
- 平文のFTPで送った場合、パスワードが暗号化されずに流れる。
  **FTPサブアカウント**（公開フォルダだけに権限を絞ったアカウント）を作って、
  そちらを Secrets に入れるのが安全

## 手で公開する場合

```
python3 tools/fetch_blog.py      # 記事を取り込む（任意）
python3 tools/fetch_reviews.py   # 口コミを取り込む（任意）
python3 tools/build_site.py      # サイトを作る
# site/ の中身を ~/www へアップロード
```
