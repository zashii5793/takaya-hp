#!/usr/bin/env python3
"""site/ 配下の静的HTMLを生成する。

使い方:  python3 tools/build_site.py
- ヘッダー・フッター・共通CTAはここで一元管理し、各ページに展開する
- 文章はすべて現行サイトの文言とご本人に確認いただいた内容（docs/01-concept.md 3-1）
- 写真枠は assets/photos/ にファイルが入るまでイメージ図（SVG）
"""
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "site")

FORM = "https://docs.google.com/forms/d/1dqDrili-aAHTuZznA2gH81imzFE-1Ae7TnBwVE7lZE8/viewform"
FORM_EMBED = FORM + "?embedded=true"
MAP_EMBED = ("https://maps.google.com/maps?q=%E3%82%BF%E3%82%AB%E3%83%A4%E3%83%A2%E3%83%BC%E3%82%BF%E3%83%BC%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE"
             "&ll=34.6752208,133.9613749&z=17&hl=ja&output=embed")
MAP_LINK = ("https://www.google.co.jp/maps/place/%E3%82%BF%E3%82%AB%E3%83%A4%E3%83%A2%E3%83%BC%E3%82%BF%E3%83%BC%E3%88%B1+%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/"
            "@34.6752252,133.9588,17z/data=!3m1!4b1!4m6!3m5!1s0x355408b5db6dfb9d:0x653a5f5af1c074f5!8m2!3d34.6752208!4d133.9613749!16s%2Fg%2F1vb99wz9?hl=ja")
HOURS = "8:30–17:30／火曜定休"

NAV = [
    ("services/index.html", "サービス"),
    ("recruit.html", "採用情報"),
    ("blog/index.html", "ブログ"),
    ("company.html", "会社概要"),
    ("access.html", "アクセス"),
    ("contact.html", "お問い合わせ"),
]

# SNS・外部リンク（URL 受領後に差し替え。None のものは「準備中」表示）
SOCIAL = [
    ("Instagram", None),
    ("Facebook", None),
    ("LINE", None),
]
LOTUS_URL = "https://www.lotas.co.jp/"  # ロータスクラブ（2026-09-10 受領）

SERVICES = [
    # slug, 番号, 名称, 1行説明, 画像, 写真タグ
    ("cars", "01", "クルマを探す・買い取る", "新車は日本車の全メーカー。中古車はご希望条件で業者オークションから探すオーダー形式。", "exterior-road", ""),
    ("lease", "02", "法人・個人リース", "税金・保険・車検・整備まで月額に含めたメンテナンスリースと、ファイナンスリース。", "lease", "イメージ図／写真差し替え予定：リース車両"),
    ("inspection", "03", "車検・点検・整備", "国産車は全メーカー対応、輸入車もOK。45分のニュースマイル車検。", "mechanic-engine", ""),
    ("bodywork", "04", "板金・コーティング", "傷・へこみの修理から塗装まで。東京海上日動リペアネット取扱。", "paint-booth", ""),
    ("insurance", "05", "自動車保険", "東京海上日動・損保ジャパンの代理店。購入から保険まで一つの窓口で。", "president", ""),
]


# 詳細ページだけ差し替える画像（カードは SERVICES の画像のまま）
DETAIL_IMG = {
    "lease": ("drive", "イメージ図：快適なドライブを（写真差し替え予定）"),
    "inspection": ("mechanic-lift", ""),
    "bodywork": ("bodywork-sanding", ""),
}


# 採用パンフレット（2026-09-10 受領）から切り出した写真。alt はここで一元管理
PHOTOS = {
    "exterior-road": "タカヤモーター 社屋と展示場（岡山市中区高屋）",
    "building": "タカヤモーター フロント社屋",
    "factory": "整備工場（リフト・車検ライン）",
    "mechanic-lift": "リフトアップした車両の下回りを整備する整備士",
    "mechanic-engine": "エンジンルームを点検する整備士",
    "bodywork-sanding": "板金作業（研磨）",
    "paint-booth": "塗装ブースでの塗装作業",
    "staff": "整備スタッフ",
    "president": "打ち合わせの様子",
}


def ph(root, img, tag, extra_class=""):
    if img in PHOTOS:
        return (f'<div class="ph ph--photo {extra_class}"><img src="{root}assets/img/photos/{img}.jpg" '
                f'alt="{PHOTOS[img]}" loading="lazy"></div>')
    return (f'<div class="ph {extra_class}"><img src="{root}assets/img/{img}.svg" alt="" loading="lazy">'
            f'<span class="tag">{tag}</span></div>')


def header(root, active):
    items = ""
    for href, label in NAV:
        cls = ' class="is-active"' if href.split("/")[0] == active else ""
        items += f'<li><a href="{root}{href}"{cls}>{label}</a></li>'
    return f'''<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{root}index.html">
      <span class="brand__mark">ロゴ</span>
      <span><span class="brand__name">TakayaCarGroup／タカヤモーター(株)</span><br><span class="brand__sub">タカヤリース株式会社</span></span>
    </a>
    <button class="nav-toggle" aria-label="メニュー" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="nav" aria-label="グローバルナビ"><ul>{items}</ul></nav>
    <a class="header-tel" href="tel:0120100152"><small>フリーダイヤル</small><strong>0120-100-152</strong></a>
  </div>
</header>'''


def sp_bar(root):
    return f'''<div class="sp-bar">
  <a href="tel:0120100152">📞 0120-100-152</a>
  <a href="{root}contact.html">お問い合わせ</a>
</div>'''


def cta(root):
    return f'''<section class="cta sec--alt">
  <div class="wrap">
    <div>
      <h2>お見積り・ご相談は無料です</h2>
      <p>「これは直りますか」「いくらぐらいですか」だけでも構いません。お電話でもフォームでもお受けします。</p>
    </div>
    <div class="cta__actions">
      <a class="tel-big" href="tel:0120100152"><small>タカヤモーター フリーダイヤル</small><strong>0120-100-152</strong></a>
      <a class="btn btn--primary" href="{FORM}" target="_blank" rel="noopener">お問い合わせフォーム</a>
    </div>
  </div>
</section>'''


def lotus_html():
    if LOTUS_URL:
        return f'<a href="{LOTUS_URL}" target="_blank" rel="noopener" style="color:inherit">ロータスクラブ（全日本ロータス同友会）会員</a>'
    return 'ロータスクラブ（全日本ロータス同友会）会員'


def social_html(root):
    out = f'<li><a href="{root}blog/index.html">ブログ</a></li>'
    for name, href in SOCIAL:
        if href is None:
            out += f'<li><span class="social__off" title="URL 受領後に有効化">{name}（準備中）</span></li>'
        else:
            out += f'<li><a href="{href}" target="_blank" rel="noopener">{name}</a></li>'
    return out


def footer(root):
    svc = "".join(f'<li><a href="{root}services/{slug}.html">{name}</a></li>' for slug, _, name, *_ in SERVICES)
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <p class="f-name">TakayaCarGroup<br>タカヤモーター株式会社／タカヤリース株式会社</p>
        <p>〒703-8233 岡山市中区高屋21-1<br>営業時間 8:30–17:30／定休日 毎週火曜日ほか<br>創立 昭和40年5月10日（タカヤモーター）</p>
        <p>{lotus_html()}</p>
        <p><span class="todo">認証工場番号・古物商許可番号・保険代理店登録 要確認</span></p>
        <ul class="social">{social_html(root)}</ul>
      </div>
      <div><h4>サービス</h4><ul>{svc}</ul></div>
      <div><h4>会社について</h4><ul>
        <li><a href="{root}company.html">会社概要</a></li>
        <li><a href="{root}recruit.html">採用情報</a></li>
        <li><a href="{root}blog/index.html">ブログ</a></li>
        <li><a href="{root}access.html">アクセス</a></li>
        <li><a href="{root}contact.html">お問い合わせ</a></li>
        <li><a href="{root}privacy.html">プライバシーポリシー</a></li>
      </ul></div>
    </div>
    <p class="copy">© 1965– TAKAYA MOTOR CO., LTD. / TAKAYA LEASE CO., LTD.</p>
  </div>
</footer>
<script src="{root}assets/js/site.js"></script>'''


def page(path, title, desc, body, active=""):
    root = "../" if "/" in path else ""
    full_title = "タカヤモーター株式会社｜岡山市中区の車検・整備・新車中古車・リース・保険" if path == "index.html" \
        else f"{title}｜タカヤモーター株式会社（岡山市中区）"
    html = f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Barlow+Semi+Condensed:wght@500;600;700&display=swap">
<link rel="stylesheet" href="{root}assets/css/site.css">
</head>
<body>
{header(root, active)}
<main>
{body}
</main>
{cta(root)}
{footer(root)}
{sp_bar(root)}
</body>
</html>
'''
    dst = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", path)


def page_head(root, crumbs, title, lead, extra=""):
    c = " › ".join(f'<a href="{root}{h}">{l}</a>' if h else l for h, l in crumbs)
    return f'''<section class="page-head"><div class="wrap">
  <p class="crumbs">{c}</p>
  <h1>{title}</h1>
  <p class="lead">{lead}</p>
  {extra}
</div></section>'''


def svc_nav(root, active):
    items = ""
    for slug, num, name, *_ in SERVICES:
        cls = ' class="is-active"' if slug == active else ""
        items += f'<li><a href="{root}services/{slug}.html"{cls}>{num} {name}</a></li>'
    return '<ul class="svc-nav">' + items + '</ul>'


def contact_row(root, primary_label, tel=None):
    tel_html = f'<a class="btn btn--ghost" href="tel:{tel[1]}">{tel[0]} {tel[2]}</a>' if tel else ""
    return f'''<div class="btn-row">
  <a class="btn btn--outline" href="{FORM}" target="_blank" rel="noopener">{primary_label}</a>
  <a class="btn btn--ghost" href="{FORM}" target="_blank" rel="noopener">お問い合わせフォーム</a>
  {tel_html}
  <span class="muted">お電話 0120-100-152（{HOURS}）</span>
</div>'''


# ======================================================================
# トップページ：どんな会社か／何をしているか／どこにあるか の3点に絞る
# ======================================================================
def build_index():
    root = ""
    svc_cards = "".join(f'''
    <a class="card" href="services/{slug}.html">
      {ph(root, img, tag)}
      <div class="card__body">
        <span class="card__num">{num}</span>
        <h3>{name}</h3>
        <p>{desc}</p>
        <span class="card__more">くわしく見る →</span>
      </div>
    </a>''' for slug, num, name, desc, img, tag in SERVICES)

    body = f'''
<section class="hero">
  <div class="wrap">
    <div>
      <p class="hero__since"><span>SINCE 1965 ・ OKAYAMA</span></p>
      <h1>お客様満足No.1を目指し、<br>質の高いカーサービスを。</h1>
      <p class="hero__lead">地域のみなさまに支えられて60年。一台一台、お客様のご事情に合わせたきめ細かな対応で、これからも安心、信頼のサービスをお届けします。</p>
      <ul class="pills">
        <li>スズキ・ダイハツ 代理店</li>
        <li>国産車は全メーカー 車検・整備OK</li>
        <li>輸入車も対応</li>
      </ul>
      <div class="btn-row">
        <a class="btn btn--primary" href="contact.html">お問い合わせ</a>
        <a class="btn btn--ghost" href="#service">サービスを見る</a>
      </div>
    </div>
    {ph(root, "exterior-road", "")}
  </div>
</section>

<section class="stats">
  <div class="wrap">
    <div class="stat"><strong>1965<small>年</small></strong><span>創立（昭和40年5月10日）</span></div>
    <div class="stat"><strong>8<small>業務</small></strong><span>ワンストップで対応</span></div>
    <div class="stat"><strong>45<small>分</small></strong><span>車検ライン（自社の指定工場）</span></div>
    <div class="stat"><strong>60<small>年</small></strong><span>地域に支えられて</span></div>
  </div>
</section>

<section class="sec" id="about">
  <div class="wrap split">
    <div>
      <span class="eyebrow">ABOUT</span>
      <h2 class="sec-title">岡山市中区で60年。<br>クルマのことを、まとめて相談できる会社です。</h2>
      <p class="lead">タカヤモーター（昭和40年創立）とタカヤリース（昭和59年創立）の2社で、新車・中古車の販売、買取、リース、車検・整備、板金塗装、自動車保険まで8つの業務を行っています。スズキ・ダイハツの代理店ですが、国産車は全メーカー、輸入車の整備もお受けします。</p>
      <a class="link-more" href="company.html">会社概要を見る →</a>
    </div>
    <div>
      <p class="muted" style="letter-spacing:.06em">大切にしていること</p>
      <ul class="dash-list" style="margin-top:8px">
        <li>お客様にとって、何がベストかを優先して対応します</li>
        <li>おクルマの代替ありきの提案はしません</li>
        <li>大切なおクルマをながく乗りたい方には、どんな点検や修理が必要かを丁寧に説明します</li>
      </ul>
    </div>
  </div>
</section>

<section class="sec sec--alt" id="service">
  <div class="wrap">
    <span class="eyebrow">SERVICE</span>
    <h2 class="sec-title">おクルマのことはすべてワンストップで対応可能です！</h2>
    <p class="lead">各メーカー新車・中古車販売、車の買取、リース、各種ローン、車検、一般整備、鈑金塗装、損害保険代理業務。この8業務を、5つの窓口でお受けします。</p>
    <div class="cards cards--5">{svc_cards}
    </div>
  </div>
</section>

<section class="news">
  <div class="wrap">
    <div class="news__head">
      <span class="eyebrow">NEWS / BLOG</span>
      <p class="news__title">お知らせ・ブログ</p>
    </div>
    <ul class="news__list">
      <li><time>2026.08.20</time><a href="blog/index.html">現行ブログの記事タイトルが入ります（移行後に差し替え）</a></li>
      <li><time>2026.08.06</time><a href="blog/index.html">現行ブログの記事タイトルが入ります（移行後に差し替え）</a></li>
    </ul>
    <a class="link-more" href="blog/index.html">一覧を見る →</a>
  </div>
</section>

<section class="sec" id="access">
  <div class="wrap split split--media">
    <div>
      <span class="eyebrow">ACCESS</span>
      <h2 class="sec-title">アクセス</h2>
      <div class="info-list" style="margin-top:20px">
        <div><h4>所在地</h4><p>〒703-8233<br>岡山市中区高屋21-1</p><a class="link-more" style="margin-top:6px" href="{MAP_LINK}" target="_blank" rel="noopener">Google マップで見る →</a></div>
        <div><h4>営業時間</h4><p>8:30 – 17:30</p><p class="muted">定休日：毎週火曜日／年末年始・ゴールデンウィーク・盆休み</p></div>
        <div><h4>お電話</h4>
          <p>タカヤモーター <a href="tel:0120100152" style="font-family:var(--f-num);font-weight:700;font-size:20px;text-decoration:none;color:var(--ink)">0120-100-152</a><br>
             タカヤリース <a href="tel:0120556649" style="font-family:var(--f-num);font-weight:700;font-size:20px;text-decoration:none;color:var(--ink)">0120-556-649</a></p></div>
      </div>
      <a class="link-more" href="access.html">部署別の電話番号・くわしいアクセス →</a>
    </div>
    <div class="map"><iframe src="{MAP_EMBED}" title="タカヤモーター株式会社 所在地（Google マップ）" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>
  </div>
</section>
'''
    page("index.html", "トップ", "岡山市中区高屋のタカヤモーター／タカヤリース。新車・中古車販売、買取、リース、車検・整備、板金塗装、自動車保険まで8業務をワンストップで。スズキ・ダイハツ代理店、国産全メーカー・輸入車の整備に対応。", body, active="index.html")


# ======================================================================
# サービス一覧
# ======================================================================
def build_services_index():
    root = "../"
    cards = "".join(f'''
    <a class="card" href="{slug}.html">
      {ph(root, img, tag)}
      <div class="card__body">
        <span class="card__num">{num}</span>
        <h3>{name}</h3>
        <p>{desc}</p>
        <span class="card__more">くわしく見る →</span>
      </div>
    </a>''' for slug, num, name, desc, img, tag in SERVICES)
    body = page_head(root, [("index.html", "トップ"), (None, "サービス")], "サービス",
                     "各メーカー新車・中古車販売、車の買取、リース、各種ローン、車検、一般整備、鈑金塗装、損害保険代理業務。この8業務を、5つの窓口でお受けします。") + f'''
<section class="sec"><div class="wrap">
  <div class="cards cards--3" style="margin-top:0">{cards}</div>
</div></section>'''
    page("services/index.html", "サービス", "タカヤモーターの5つのサービス窓口：クルマを探す・買い取る／法人・個人リース／車検・点検・整備／板金・コーティング／自動車保険。", body, active="services")


def svc_page(slug, title, lead_html, content_html, contact_html):
    root = "../"
    _, num, name, _, img, tag = next(s for s in SERVICES if s[0] == slug)
    img, tag = DETAIL_IMG.get(slug, (img, tag))
    body = page_head(root, [("index.html", "トップ"), ("services/index.html", "サービス"), (None, name)],
                     f'<span class="card__num" style="display:block;margin-bottom:4px">{num}</span>{name}', lead_html,
                     svc_nav(root, slug)) + f'''
<section class="sec"><div class="wrap detail">
  {ph(root, img, tag)}
  <div>
    {content_html}
    {contact_html}
  </div>
</div></section>'''
    page(f"services/{slug}.html", title, re.sub(r"<[^>]+>", "", lead_html)[:120], body, active="services")


def build_cars():
    makers = "".join(f"<li>{m}</li>" for m in ["トヨタ", "ホンダ", "日産", "ダイハツ", "スズキ", "マツダ", "三菱", "スバル", "いすゞ", "三菱ふそう", "日野"])
    content = f'''
<h2>新車は全メーカー、中古車はオーダー形式</h2>
<p class="lead"><strong>新車は日本車の全メーカーをお取り扱いしています。</strong>中古車はご希望の条件を伺い、業者オークションから探してご提案する「オーダー形式」です。買取・下取りもあわせてご相談いただけます。</p>
<div class="tiles">
  <div class="tile"><strong class="jp">全メーカー</strong><span>新車は日本車の全メーカー取り扱い</span></div>
  <div class="tile"><strong class="jp">オーダー形式</strong><span>中古車はご希望条件で業者オークションから探します</span></div>
  <div class="tile"><strong>1<small style="font-family:var(--f-jp);font-size:14px;color:var(--ink)">社完結</small></strong><span>車両・オプション・諸費用までワンストップ</span></div>
</div>
<div class="box-grid">
  <div class="box">
    <h4>新車販売</h4>
    <p class="sub">日本車 全メーカー取り扱い（トラックも含む）</p>
    <ul class="chips">{makers}</ul>
    <ul class="dash-list">
      <li>各ディーラーの店舗を回る手間なく、<strong>複数メーカーの比較検討（見積もり等）</strong>が可能です。</li>
      <li>特定メーカーの影響がないため、<strong>中立的な立場から客観的なアドバイス</strong>ができます。</li>
      <li>車両本体からオプション・諸費用まで、<strong>すべてワンストップ</strong>でご提供できます。</li>
    </ul>
  </div>
  <div class="box">
    <h4>中古車はオーダー形式</h4>
    <p class="sub">ご希望の一台を業者オークションから</p>
    <p>店頭在庫は多くありませんが、<strong>ご予算・車種・年式・走行距離などの条件を伺い、業者オークションから条件に合う一台を探してご提案</strong>します。「この車種のこの年式で、走行○万km以内」といったご相談から承ります。</p>
    <ul class="chips chips--lg"><li>買取・下取り</li><li>各種ローン</li><li>購入後の整備・車検・保険まで</li></ul>
  </div>
</div>
<div class="box box--alt" style="margin-top:20px;display:flex;gap:20px;align-items:center;flex-wrap:wrap">
  <div style="flex:1 1 280px">
    <h4 style="font-size:14px">一部の在庫車はカーセンサーにも掲載しています</h4>
    <p style="margin-top:6px;font-size:13px">写真・走行距離・価格は掲載ページが最新です。掲載車以外も、上記のオーダー形式でお探しできます。</p>
  </div>
  <a class="btn btn--dark" href="#">カーセンサー掲載車を見る →</a>
  <p style="flex-basis:100%;margin:0"><span class="todo">要確認：カーセンサーの掲載店ページURL</span></p>
</div>'''
    svc_page("cars", "クルマを探す・買い取る",
             "新車は日本車の全メーカー。中古車はご希望条件を伺って業者オークションから探すオーダー形式。買取・下取り、各種ローンもご相談ください。",
             content, contact_row("../", "クルマ探しを相談する", ("営業直通", "0862721021", "086-272-1021")))


def build_lease():
    rows = [("車両代・登録費用・取得税", "○", "○ 新車登録時のみも可能"), ("重量税（新規登録時＋車検時）", "○", "○"),
            ("自賠責保険（新規登録時＋車検時）", "○", "○"), ("自動車税（全リース期間分）", "○", "○"),
            ("任意保険（全リース期間分）※1", "○", "△ 選択自由"), ("事故処理サービス ※2", "○", "△ 選択自由"),
            ("法定点検", "○", "－"), ("車検整備", "○", "△ 選択自由"), ("一般整備及び故障修理 ※3", "○", "－"),
            ("各種消耗品の交換", "○", "－"), ("タイヤ交換 ※4", "○", "－"), ("バッテリーの交換 ※4", "○", "－")]
    tr = "".join(f"<tr><td>{a}</td><td><strong>{b}</strong></td><td>{c}</td></tr>" for a, b, c in rows)
    content = f'''
<h2>メンテナンスリースとファイナンスリース</h2>
<p class="lead"><strong>税金・保険・車検・整備・消耗品まで月額に含めた「メンテナンスリース」</strong>と、車両代と税金を中心にした「ファイナンスリース」の2種類。法人の社用車から個人のマイカーまで、ご事情に合わせてお選びいただけます。</p>
<div class="table-box">
  <div class="table-box__head"><strong>リース料に含まれる項目</strong></div>
  <div class="table-scroll"><table>
    <thead><tr><th>項目</th><th class="col-b">メンテナンスリース</th><th class="col-b">ファイナンスリース</th></tr></thead>
    <tbody>{tr}</tbody>
  </table></div>
  <p class="table-box__note">○ 含まれる　△ ご希望で追加　－ 含まれない　<span class="todo">※1〜※4 の注記文は要確認</span></p>
</div>
<p class="muted" style="margin-top:14px"><span class="todo">要確認</span> 契約期間・最低台数・個人契約の可否・月額の目安</p>'''
    svc_page("lease", "法人・個人リース",
             "税金・保険・車検・整備・消耗品まで月額に含めたメンテナンスリースと、車両代と税金を中心にしたファイナンスリース。法人の社用車から個人のマイカーまで。",
             content, contact_row("../", "リースの相談をする", ("タカヤリース", "0120556649", "0120-556-649")))


def build_inspection():
    def price_row(name, desc, prices, badge=""):
        cells = "".join(f'<td class="num">{p}<small>円〜</small></td>' for p in prices)
        b = f'<span class="badge">{badge}</span>' if badge else ""
        return f'<tr><td><p class="name">{name}{b}</p><p class="desc">{desc}</p></td>{cells}</tr>'
    content = f'''
<h2>国産車は全メーカー、輸入車もお受けします</h2>
<p class="lead"><strong>スズキ・ダイハツの代理店ですが、国産車は全メーカーの車検・点検・整備に対応しています。</strong>輸入車もお受けします（国産車より日数をいただきます）。約60年におよぶ実績、経験をもとに質の高いサービスをご提供します。</p>
<p class="lead">大切なおクルマをながく乗りたい方には、どんな点検や修理が必要かを丁寧にご説明します。オイル交換などの日常の整備から、タイヤ交換、ドライブレコーダーの取り付け、カスタムまでお受けします。ご希望の場合は引取り・納車サービスも承ります。</p>
<div class="table-box">
  <div class="table-box__head"><strong>ニュースマイル車検</strong><span class="muted">早期予約（60日前）で 2,200円割引</span><span class="right">2026年8月改訂</span></div>
  <div class="table-scroll"><table>
    <thead><tr><th>コース</th><th>軽自動車<br><small>全車</small></th><th>小型自動車<br><small>1.0t迄</small></th><th>中型自動車<br><small>1.5t迄</small></th><th>大型自動車<br><small>2.0t迄</small></th></tr></thead>
    <tbody>
      {price_row("ニューサービスコース", "立ち合い車検／所要時間の目安 60分", ["50,760", "62,660", "71,960", "82,910"])}
      {price_row("スマイルコース", "1日お預かり／洗車サービス・ご来店時レンタカー無料", ["57,360", "72,560", "81,860", "92,260"], "おすすめ")}
      {price_row("プレミアムコース", "1〜2日お預かり／洗車・フロントガラス撥水・ボディコート撥水・ご来店時レンタカー無料", ["62,860", "79,160", "89,560", "101,610"])}
      <tr class="sub"><td>うち法定諸費用</td><td>38,110円</td><td>47,810円</td><td>56,010円</td><td>64,210円</td></tr>
    </tbody>
  </table></div>
  <p class="table-box__note">表示価格は「法定諸費用＋基本技術料」から早期予約割引（60日前）2,200円を引いた総額（税込）です。部品代とその工賃は含まれていません。お車の状態により部品交換で料金が追加になる場合があります。<br>法定諸費用は令和8年11月現在のもので、以降の改定は反映していません。エコカー減税対象車や初度登録から13年を超える車は重量税が異なります。OBD検査対象車は別途料金が必要です。ご希望の場合は引取り・納車サービスも承ります。</p>
</div>
<div class="box-grid">
  <div class="box"><h4>法定点検</h4><p>6ヶ月点検・12ヶ月法定点検を実施しています。車検と車検のあいだも、お車の状態を見ておくことができます。</p></div>
  <div class="box"><h4>タイヤ交換</h4><p>ヨコハマタイヤ・ブリヂストンの正規取扱店です。銘柄選びからご相談ください。</p></div>
</div>
<ul class="chips chips--lg" style="margin-top:20px"><li>車検</li><li>6ヶ月点検・12ヶ月法定点検</li><li>一般整備・修理</li><li>オイル交換</li><li>タイヤ交換</li><li>ドライブレコーダー取付</li><li>カスタム</li></ul>'''
    svc_page("inspection", "車検・点検・整備",
             "スズキ・ダイハツの代理店ですが、国産車は全メーカーの車検・点検・整備に対応。輸入車もお受けします。45分のニュースマイル車検、料金表を掲載。",
             content, contact_row("../", "車検の見積りを依頼する"))


def build_bodywork():
    content = '''
<h2>傷・へこみから塗装まで</h2>
<p class="lead">東京海上日動のリペアネットサービスを提供しています。なお、弊社に直接ご連絡いただくことも可能です。</p>
<p class="muted" style="margin-top:14px"><span class="todo">要記入：コーティングの施工メニュー・下地処理・保証期間</span></p>'''
    svc_page("bodywork", "板金・コーティング",
             "傷・へこみの修理から塗装まで。東京海上日動のリペアネットサービスを提供。弊社へ直接のご連絡も可能です。",
             content, contact_row("../", "傷・へこみを相談する"))


def build_insurance():
    content = '''
<h2>購入から保険まで、一つの窓口で</h2>
<p class="lead">損害保険代理店として、自動車保険をお取り扱いしています。</p>
<ul class="chips chips--lg" style="margin-top:16px"><li>東京海上日動</li><li>損保ジャパン</li></ul>'''
    svc_page("insurance", "自動車保険",
             "損害保険代理店として自動車保険をお取り扱い。東京海上日動・損保ジャパン。",
             content, contact_row("../", "保険の見直しを相談する"))


# ======================================================================
def build_company():
    root = ""
    body = page_head(root, [("index.html", "トップ"), (None, "会社概要")], "会社概要",
                     "タカヤモーター株式会社（昭和40年創立）とタカヤリース株式会社（昭和59年創立）。岡山市中区高屋で、クルマに関わる8つの業務を行っています。") + f'''
<section class="sec"><div class="wrap split">
  <div>
    {ph(root, "building", "")}
    <div class="box box--alt" style="margin-top:24px">
      <p class="muted" style="letter-spacing:.06em">経営理念</p>
      <ol style="padding-left:1.3em;font-size:14px;line-height:2;color:var(--ink-sub);margin-top:10px">
        <li>常に豊かさを追求し、優れた人材育成へ努力・研鑽しよう。</li>
        <li>お客様満足度を第一とし、質の良い物・サービスを提供しよう。</li>
        <li>価値ある仕事を通じ、公平な配分と利益をもって地域社会に貢献しよう。</li>
      </ol>
    </div>
  </div>
  <table class="dl-table"><tbody>
    <tr><th>商号</th><td>タカヤモーター株式会社<br>タカヤリース株式会社</td></tr>
    <tr><th>創立</th><td>タカヤモーター：昭和40年5月10日<br>タカヤリース：昭和59年5月（事業部発足 昭和50年10月）</td></tr>
    <tr><th>代表者</th><td>タカヤモーター 代表取締役社長 草地 賢吾<br>タカヤリース 代表取締役社長 石指 英樹</td></tr>
    <tr><th>所在地</th><td>〒703-8233 岡山市中区高屋21-1</td></tr>
    <tr><th>資本金</th><td>1,000万円</td></tr>
    <tr><th>従業員数</th><td>27名</td></tr>
    <tr><th>事業内容</th><td>タカヤモーター：自動車販売業務／自動車整備業務／自動車損害保険代理店業務<br>タカヤリース：自動車リース業務／レンタカー業務／（株）ロートピア フランチャイズ業務</td></tr>
    <tr><th>取扱メーカー</th><td>スズキ・ダイハツ代理店。新車は日本車全メーカー（トヨタ／ホンダ／日産／ダイハツ／スズキ／マツダ／三菱／スバル／いすゞ／三菱ふそう／日野）</td></tr>
    <tr><th>認証・許可</th><td>指定自動車整備事業／自動車特定整備事業<br>ISO 14001 認証取得<br><span class="todo">番号は要確認</span></td></tr>
    <tr><th>加盟団体</th><td><a href="{LOTUS_URL}" target="_blank" rel="noopener">ロータスクラブ（全日本ロータス同友会）</a> 会員</td></tr>
    <tr><th>採用</th><td><a href="recruit.html">採用情報を見る →</a></td></tr>
    <tr><th>営業時間</th><td>8:30–17:30（定休日：毎週火曜日／年末年始・GW・盆休み）</td></tr>
  </tbody></table>
</div></section>

<section class="sec sec--deep"><div class="wrap promise">
  <div>
    <span class="eyebrow">OUR PROMISE</span>
    <h2 class="sec-title">大切にしていること</h2>
    <p class="lead">きめ細かいサービスが、タカヤの売りです。</p>
  </div>
  <ul>
    <li>お客様にとって、何がベストかを優先して対応します</li>
    <li>おクルマの代替ありきの提案はしません</li>
    <li>大切なおクルマをながく乗りたい方には、どんな点検や修理が必要かを丁寧に説明します</li>
  </ul>
</div></section>'''
    page("company.html", "会社概要", "タカヤモーター株式会社・タカヤリース株式会社の会社概要。創立、代表者、所在地、資本金、従業員数、事業内容、経営理念。", body, active="company.html")


def build_access():
    root = ""
    body = page_head(root, [("index.html", "トップ"), (None, "アクセス")], "アクセス",
                     "〒703-8233 岡山市中区高屋21-1。営業時間 8:30–17:30、定休日は毎週火曜日です。") + f'''
<section class="sec"><div class="wrap">
  <div class="split split--media">
    <div class="info-list">
      <div><h4>所在地</h4><p>〒703-8233<br>岡山市中区高屋21-1</p><a class="link-more" style="margin-top:6px" href="{MAP_LINK}" target="_blank" rel="noopener">Google マップで見る →</a></div>
      <div><h4>交通</h4>
        <p>電車：JR高島駅から徒歩15分<br>お車：国道250号沿い、マルナカ高屋店の角を左折<br>バス：岡電バス「高屋」降り場から徒歩5分</p></div>
      <div><h4>営業時間</h4><p>8:30 – 17:30</p><p class="muted">定休日：毎週火曜日／年末年始・ゴールデンウィーク・盆休み</p></div>
      <div><h4>フリーダイヤル</h4>
        <p>タカヤモーター株式会社 <a href="tel:0120100152" style="font-family:var(--f-num);font-weight:700;font-size:22px;text-decoration:none;color:var(--ink)">0120-100-152</a></p>
        <p>タカヤリース株式会社 <a href="tel:0120556649" style="font-family:var(--f-num);font-weight:700;font-size:22px;text-decoration:none;color:var(--ink)">0120-556-649</a></p></div>
    </div>
    <div class="map"><iframe src="{MAP_EMBED}" title="タカヤモーター株式会社 所在地（Google マップ）" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>
  </div>
  <div class="tel-grid">
    <div><p>サービス</p><a href="tel:0862721001">086-272-1001</a></div>
    <div><p>営業（タカヤモーター）</p><a href="tel:0862721021">086-272-1021</a></div>
    <div><p>営業（タカヤリース）</p><a href="tel:0862733611">086-273-3611</a></div>
    <div><p>総務</p><a href="tel:0862723065">086-272-3065</a></div>
  </div>
</div></section>'''
    page("access.html", "アクセス", "タカヤモーター株式会社へのアクセス。〒703-8233 岡山市中区高屋21-1。営業時間・定休日・部署別電話番号。", body, active="access.html")


def build_contact():
    root = ""
    body = page_head(root, [("index.html", "トップ"), (None, "お問い合わせ")], "お問い合わせ",
                     "お見積り・ご相談は無料です。「これは直りますか」「いくらぐらいですか」だけでも構いません。お電話でもフォームでもお受けします。") + f'''
<section class="sec"><div class="wrap">
  <div class="split">
    <div class="info-list">
      <div><h4>お電話</h4>
        <p>タカヤモーター <a href="tel:0120100152" style="font-family:var(--f-num);font-weight:700;font-size:26px;text-decoration:none;color:var(--brand)">0120-100-152</a></p>
        <p>タカヤリース <a href="tel:0120556649" style="font-family:var(--f-num);font-weight:700;font-size:26px;text-decoration:none;color:var(--brand)">0120-556-649</a></p>
        <p class="muted">受付 8:30–17:30／定休日 毎週火曜日</p></div>
      <div><h4>メール</h4><p><a href="mailto:takaya-customer-service@takaya-gp.jp">takaya-customer-service@takaya-gp.jp</a></p></div>
      <div><h4>部署直通</h4><p class="muted">サービス 086-272-1001／営業（モーター）086-272-1021／営業（リース）086-273-3611／総務 086-272-3065</p></div>
    </div>
    <div>
      <h4 style="font-size:16px">お問い合わせフォーム</h4>
      <p class="muted" style="margin-top:6px">下のフォームが表示されない場合は <a href="{FORM}" target="_blank" rel="noopener">こちらから開いてください</a>。</p>
      <div class="form-embed"><iframe src="{FORM_EMBED}" title="お問い合わせフォーム" loading="lazy">読み込んでいます…</iframe></div>
      <p class="muted" style="margin-top:8px"><span class="todo">要確認：Google フォーム右上「送信」→🔗 の公開URL（/d/e/…/viewform）に差し替え</span></p>
    </div>
  </div>
</div></section>'''
    page("contact.html", "お問い合わせ", "タカヤモーターへのお問い合わせ。フリーダイヤル 0120-100-152、お問い合わせフォーム、メール。お見積り・ご相談は無料です。", body, active="contact.html")


def build_privacy():
    src = open(os.path.join(ROOT, "docs", "content", "privacy-policy.md"), encoding="utf-8").read()
    # 冒頭の管理用メモ（引用ブロック）と見出し行を除き、本文のみを HTML 化
    lines = src.split("\n")
    out, in_list = [], False
    for l in lines[1:]:
        t = l.strip()
        if t.startswith(">") or t == "---":
            continue
        if t.startswith("## "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<h2>{t[3:]}</h2>")
        elif t.startswith("- "):
            if not in_list: out.append("<ul>"); in_list = True
            out.append(f"<li>{t[2:]}</li>")
        elif t:
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<p>{t}</p>")
    if in_list: out.append("</ul>")
    body = page_head("", [("index.html", "トップ"), (None, "プライバシーポリシー")], "プライバシーポリシー",
                     "タカヤモーター株式会社／タカヤリース株式会社の個人情報の取り扱いについて。") + f'''
<section class="sec"><div class="wrap"><div class="prose">{"".join(out)}</div></div></section>'''
    page("privacy.html", "プライバシーポリシー", "タカヤモーター株式会社／タカヤリース株式会社のプライバシーポリシー。", body)


# ======================================================================
# 採用情報（文言はご本人提供 2026-09-10。Indeed・ミイダスの応募ページ URL は受領待ち）
# ======================================================================
def build_recruit():
    root = ""
    body = page_head(root, [("index.html", "トップ"), (None, "採用情報")], "採用情報",
                     "タカヤモーターでは、タカヤの理念に共感し一緒に働ける仲間を募集しています。通期を通じて新人・中途採用活動をしています。ご興味がありましたら、お気軽にお問い合わせフォームにてご連絡ください。") + f'''
<section class="sec"><div class="wrap split">
  <div>
    <span class="eyebrow">MECHANIC</span>
    <h2 class="sec-title">自動車整備士募集！</h2>
    <p class="lead">技術に自信がなくても、やる気と意欲がある方をタカヤモーターは歓迎します。年齢・経験・学歴は一切不問です。</p>
    <ul class="reasons">
      <li><strong>ベテランスタッフから、タカヤが誇る高い整備技術を学べます</strong><p>基礎技術の習熟期間を設け、ご本人のご希望やご経験に合わせて少しずつ業務をお任せします。</p></li>
      <li><strong>様々な車種を、メーカー問わず整備できます</strong><p>車検整備・一般整備・車両診断から板金・塗装まで。工程が分かれていないので、幅広く経験できます。</p></li>
      <li><strong>岡山で60年、地域密着の老舗ブランド</strong><p>転勤はありません。地域のお客様と長くお付き合いする仕事です。</p></li>
      <li><strong>若手を役員に登用するなど、組織改革を進めています</strong><p>整備のキャリアだけでなく、事業計画・組織設計・マネジメント・会計まで役員が伝えるキャリアアップ支援制度があります。</p></li>
    </ul>
    <div class="btn-row">
      <a class="btn btn--primary" href="{FORM}" target="_blank" rel="noopener">お問い合わせフォームから応募・相談する</a>
      <a class="btn btn--ghost" href="tel:0862723065">総務 086-272-3065</a>
      <span class="muted">Indeed・ミイダスにも掲載しています <span class="todo">要確認：各応募ページのURL</span></span>
    </div>
  </div>
  <div>
    {ph(root, "factory", "")}
    <div class="box box--alt" style="margin-top:20px">
      <h4>まずは職場の雰囲気を見に来てください</h4>
      <p>面接は計2回。1回目はオンラインでも可能ですが、できれば職場の雰囲気を直接見ていただきたいので対面をおすすめします。現場見学もできます。勤務開始日のご相談（3ヶ月先など）も可能です。</p>
    </div>
  </div>
</div></section>

<section class="sec sec--alt"><div class="wrap">
  <span class="eyebrow">APPEAL</span>
  <h2 class="sec-title">タカヤグループのアピールポイント</h2>
  <div class="appeal">
    <div class="appeal__item"><span class="appeal__num">1</span><h3>多種多様な仲間</h3><p>ベテランから若手まで、バランスが取れた組織構成となっています。タカヤは多様な価値観を尊重します。</p></div>
    <div class="appeal__item"><span class="appeal__num">2</span><h3>相談できる安心感</h3><p>スタッフ全員が何気ない会話ができるような雰囲気作りをとても大切にしています。</p></div>
    <div class="appeal__item"><span class="appeal__num">3</span><h3>技術を本気で学ぶ</h3><p>卓越した技術を身につけるためには自発的、かつ好奇心ある学びが不可欠。タカヤは本人のWillを応援します。</p></div>
    <div class="appeal__item"><span class="appeal__num">4</span><h3>様々なキャリアに挑戦</h3><p>整備技術を深める以外にも、営業やフロント、経営といった、幅広く学べる機会を設けています。</p></div>
  </div>
  <div class="gallery">
      {ph(root, "mechanic-engine", "")}
      {ph(root, "staff", "")}
      {ph(root, "paint-booth", "")}
      {ph(root, "mechanic-lift", "")}
      {ph(root, "president", "")}
  </div>
</div></section>

<section class="sec sec--deep"><div class="wrap">
  <span class="eyebrow">GROWTH</span>
  <h2 class="sec-title">タカヤグループは社員一人ひとりの成長を本気で応援します</h2>
  <div class="grow">
    <div><h3>相談</h3><p>上長以外にも会社役員とも気軽に相談できます。</p></div>
    <div><h3>スキルUP</h3><p>年間3,500台以上の車を取り扱うため、経験値を多く積めます。</p></div>
    <div><h3>研修</h3><p>外部研修を積極的に実施し、知見を広めるようにしています。</p></div>
    <div><h3>キャリア</h3><p>整備以外にも、本人の意欲次第で他部のスキルを学べます。</p></div>
    <div><h3>その他</h3><p>誕生日休暇など、福利厚生も充実を図っています。</p></div>
  </div>
  <p class="grow__mission">会社だけではなく個人の市場価値を高めることを、タカヤグループは“最重要”ミッションとしています。</p>
</div></section>

<section class="sec"><div class="wrap">
  <span class="eyebrow">JOB DESCRIPTION</span>
  <h2 class="sec-title">募集要項</h2>
  <div class="split" style="margin-top:24px;align-items:start">
    <table class="dl-table"><tbody>
      <tr><th>雇用形態</th><td>正社員</td></tr>
      <tr><th>仕事内容</th><td>車検整備／一般整備／車両診断／板金・塗装<br><span class="muted">基礎技術の習熟期間を設けて、高い技術を習得いただくことを会社として期待しています。</span></td></tr>
      <tr><th>必須</th><td>3級以上の自動車整備士資格</td></tr>
      <tr><th>あれば歓迎</th><td>自動車整備の実務経験／検査員の有資格者</td></tr>
      <tr><th>給与</th><td>月給 200,000円〜300,000円<br><span class="muted">勤続1年以上の方には退職金制度があります。平均所定労働時間 202時間／月</span></td></tr>
      <tr><th>試用期間</th><td>3か月（労働条件は同条件）</td></tr>
      <tr><th>勤務時間</th><td>8:30〜17:30（シフト制）</td></tr>
      <tr><th>休日・休暇</th><td>毎週火曜日／日曜日（隔週・祝日はシフト交代制）／年末年始・GW・お盆<br>特別休暇：誕生日月に誕生日休暇を1日付与</td></tr>
    </tbody></table>
    <table class="dl-table"><tbody>
      <tr><th>勤務地</th><td>〒703-8233 岡山県岡山市中区高屋21-1<br><span class="muted">JR高島駅から徒歩15分／転勤なし／喫煙所あり</span></td></tr>
      <tr><th>社会保険</th><td>雇用保険／労災保険／健康保険／厚生年金</td></tr>
      <tr><th>待遇・福利厚生</th><td>
        <ul class="dash-list" style="margin-top:0">
          <li>再雇用制度あり（65歳まで）</li>
          <li>キャリアアップ支援制度：整備のキャリアだけでなく、事業計画作成・組織設計・マネジメント・会計知識など、役員がナレッジを伝授します（役員は大手／ベンチャーIT企業など自動車業界以外の知見も持っています）</li>
          <li>社内表彰制度</li>
          <li>社内相談窓口：役員による1on1を定期的に設け、ご本人の希望実現に向けてフォローします</li>
        </ul></td></tr>
      <tr><th>選考</th><td>面接2回（1回目はオンライン可・対面推奨）／現場見学可／勤務開始日の相談OK</td></tr>
      <tr><th>応募方法</th><td><a href="{FORM}" target="_blank" rel="noopener">お問い合わせフォーム</a>、または総務 086-272-3065 へ。Indeed・ミイダスからも応募できます。</td></tr>
    </tbody></table>
  </div>
</div></section>

<section class="sec sec--alt"><div class="wrap split" style="align-items:start">
  <div>
    <span class="eyebrow">STEP</span>
    <h2 class="sec-title">採用までのステップ</h2>
    <ol class="steps">
      <li><span>1</span><div><strong>ホームページから申込み</strong><p><a href="{FORM}" target="_blank" rel="noopener">お問い合わせフォーム</a>からお申し込みください。</p></div></li>
      <li><span>2</span><div><strong>初回面談</strong><p>オンラインもしくは対面で、会社説明を交えた面談をします。</p></div></li>
      <li><span>3</span><div><strong>面接</strong><p>最低1回から2回まで、対面による面接を予定しています。</p></div></li>
    </ol>
  </div>
  <div>
    <span class="eyebrow">FAQ</span>
    <h2 class="sec-title">よくある質問</h2>
    <dl class="faq">
      <dt>採用面接では何を聞かれますか？</dt><dd>学業や将来のキャリア形成を中心とした質問をさせていただきます。</dd>
      <dt>整備技術試験はありますか？</dt><dd>基本的に技術試験は実施しないですが、場合によっては確認をさせて頂きます。</dd>
      <dt>タカヤグループの強みはなんですか？</dt><dd>整備、営業、フロントのスタッフ全員が、お客様に喜んで頂けるサービスを提供しようと本気で考え、実践しているところです。当たり前ですが徹底しています。</dd>
    </dl>
  </div>
</div></section>'''
    page("recruit.html", "採用情報｜自動車整備士募集", "タカヤモーター株式会社の採用情報。自動車整備士（正社員）募集。3級以上の整備士資格、年齢・経験・学歴不問。月給20〜30万円、火曜定休、転勤なし、岡山市中区高屋。", body, active="recruit.html")


def build_blog():
    root = "../"
    posts = [("2026.08.20", "現行ブログの記事タイトルが入ります（移行後に差し替え）"),
             ("2026.08.06", "現行ブログの記事タイトルが入ります（移行後に差し替え）"),
             ("2026.07.24", "現行ブログの記事タイトルが入ります（移行後に差し替え）")]
    items = "".join(f'<li class="post"><time>{d}</time><a href="#">{t}</a></li>' for d, t in posts)
    body = page_head(root, [("index.html", "トップ"), (None, "ブログ")], "ブログ",
                     "日々の整備のこと、お知らせ、地域の話題など。") + f'''
<section class="sec"><div class="wrap">
  <p class="muted" style="margin-bottom:18px"><span class="todo">移行作業：現行サイトの記事をこの一覧に移します（E-01〜E-06）。名称は「ブログ」で仮置き。SNS の連携先も受領後に追加</span></p>
  <ul class="post-list">{items}</ul>
</div></section>'''
    page("blog/index.html", "ブログ", "タカヤモーター株式会社のブログ・お知らせ。", body, active="blog")


if __name__ == "__main__":
    build_recruit(); build_blog()
    build_index()
    build_services_index()
    build_cars(); build_lease(); build_inspection(); build_bodywork(); build_insurance()
    build_company(); build_access(); build_contact(); build_privacy()
