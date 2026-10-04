#!/usr/bin/env python3
"""SNS用の30秒の縦動画をつくる（文字だけ・1080×1920）。

作り方
  1. 5枚の画面を HTML で組み、Chromium で画像に書き出す
  2. ffmpeg で1枚6秒ずつつないで mp4 にする（30秒）

なぜ HTML で作るか
  日本語の折り返しと字間を、サイトと同じ考え方できれいに出せるため。
  ffmpeg の文字描画では折り返しを自分で計算することになり、崩れやすい。

音について
  Instagram のリールは音声トラックが無いと弾かれることがあるため、
  無音のトラックを足している。
"""
import asyncio
import os
import pathlib
import shutil
import subprocess

W, H = 1080, 1920
SEC = 6                     # 1枚あたりの秒数（5枚 × 6秒 = 30秒）
BRAND = "#E60012"
INK = "#1C1B1A"

CHROME = os.environ.get("CHROME_PATH", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;overflow:hidden;
  font-family:"Noto Sans JP","Noto Sans CJK JP","IPAexGothic",sans-serif;
  -webkit-font-smoothing:antialiased}}
.slide{{width:{W}px;height:{H}px;display:flex;flex-direction:column;
  justify-content:center;padding:120px 96px;position:relative}}
.slide--brand{{background:{BRAND};color:#fff}}
.slide--plain{{background:#fff;color:{INK}}}
.eyebrow{{font-size:40px;font-weight:700;letter-spacing:.18em;opacity:.85;
  margin-bottom:40px}}
.title{{font-size:104px;font-weight:700;line-height:1.35;letter-spacing:.01em}}
.num{{font-size:150px;font-weight:700;color:{BRAND};line-height:1;
  margin-bottom:48px;font-family:"Barlow Semi Condensed",sans-serif}}
.point{{font-size:84px;font-weight:700;line-height:1.5}}
.bar{{width:160px;height:12px;background:{BRAND};margin-bottom:56px}}
.slide--brand .bar{{background:#fff}}
.foot{{position:absolute;left:96px;right:96px;bottom:110px;
  font-size:38px;font-weight:700;letter-spacing:.04em;opacity:.9}}
.closing{{font-size:96px;font-weight:700;line-height:1.4}}
.url{{margin-top:56px;font-size:46px;font-weight:700;letter-spacing:.04em;opacity:.9}}
"""


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def slides_html(title, points, closing, site_label):
    """5枚ぶんの HTML。1枚 = 1つの .slide"""
    out = [f'''<div class="slide slide--brand">
      <p class="eyebrow">TAKAYA MOTOR</p>
      <div class="bar"></div>
      <h1 class="title">{_esc(title)}</h1>
      <p class="foot">岡山市中区高屋 ／ 車検・整備・販売</p>
    </div>''']
    for i, p in enumerate(points, 1):
        if not str(p).strip():
            continue
        out.append(f'''<div class="slide slide--plain">
      <p class="num">{i:02d}</p>
      <p class="point">{_esc(p)}</p>
      <p class="foot" style="color:#6B655F">タカヤモーター株式会社</p>
    </div>''')
    out.append(f'''<div class="slide slide--brand">
      <div class="bar"></div>
      <p class="closing">{_esc(closing)}</p>
      <p class="url">{_esc(site_label)}</p>
      <p class="foot">タカヤモーター株式会社 ／ 0120-100-152</p>
    </div>''')
    return out


async def _shoot(html_slides, outdir):
    from playwright.async_api import async_playwright
    paths = []
    async with async_playwright() as p:
        kw = {"args": ["--no-sandbox", "--font-render-hinting=none"]}
        if os.path.isfile(CHROME):
            kw["executable_path"] = CHROME
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(html_slides):
            await pg.set_content(f"<style>{CSS}</style>{s}")
            await pg.wait_for_timeout(120)
            fp = outdir / f"slide{i:02d}.png"
            await pg.screenshot(path=str(fp))
            paths.append(fp)
        await b.close()
    return paths


def build(title, points, closing, dest, site_label="takayagroup.co.jp", workdir=None):
    """30秒の mp4 を dest に書き出す。作れたら True"""
    if not shutil.which("ffmpeg"):
        print("  ffmpeg が無いので動画は作りません")
        return False
    dest = pathlib.Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(workdir or (dest.parent / "_work"))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    try:
        pngs = asyncio.run(_shoot(slides_html(title, points, closing, site_label), work))
    except Exception as e:
        print(f"  画面の書き出しに失敗しました（{type(e).__name__}: {e}）")
        return False

    # concat で使う一覧。最後の1枚はもう一度書く（concat の仕様で末尾が切れるため）
    lst = work / "list.txt"
    with open(lst, "w", encoding="utf-8") as f:
        for p in pngs:
            f.write(f"file '{p.name}'\nduration {SEC}\n")
        f.write(f"file '{pngs[-1].name}'\n")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", "list.txt",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", f"fps=30,scale={W}:{H},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "96k", "-shortest",
        "-movflags", "+faststart",
        str(dest.resolve()),
    ]
    r = subprocess.run(cmd, cwd=work, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ffmpeg が失敗しました: {r.stderr[:400]}")
        return False
    shutil.rmtree(work, ignore_errors=True)
    mb = dest.stat().st_size / 1024 / 1024
    print(f"  動画: {dest.name} {W}×{H} {SEC * len(pngs)}秒 ({mb:.1f}MB)")
    return True
