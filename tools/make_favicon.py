# ブラウザのタブに出るマーク（ファビコン）を、ロゴ画像から作り直す。
#
#   入力  assets/photos/logo.png        （赤いマーク＋「Takaya Car Group」の文字）
#   出力  assets/photos/favicon.png     タブ用。マークの外側は透過
#         assets/photos/apple-touch-icon.png  iPhone のホーム画面用。白地（iOSは透過を黒く塗るため）
#
# なぜ透過にするか
#   もとのロゴは白地のため、切り出したままだと正方形の四隅が白いまま残る。
#   Chrome のタブは背景が濃い色なので、その白が四角い枠に見えてしまう。
#   マークの輪郭（楕円）の外側を透けさせると、丸いマークだけがきれいに出る。
#
# 使い方   python3 tools/make_favicon.py
#   ロゴを差し替えたときだけ実行する。ふだんの公開作業では不要。

import asyncio, pathlib, base64

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "photos" / "logo.png"
FAVICON = ROOT / "assets" / "photos" / "favicon.png"
APPLE = ROOT / "assets" / "photos" / "apple-touch-icon.png"

SIZE = 64           # ファビコンの一辺。元のマークが44pxしかないため、拡大しすぎるとぼやける
APPLE_SIZE = 180    # iOS が使う大きさ
WORK = 256          # いったんこの大きさで作ってから、それぞれの大きさに落とす
APPLE_PAD = 0.12    # 白地の余白（一辺に対する割合）

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

JS = r"""([size, appleSize, applePad, work]) => {
  const img = document.getElementById('i');
  const sw = img.naturalWidth, sh = img.naturalHeight;
  const c0 = document.createElement('canvas');
  c0.width = sw; c0.height = sh;
  c0.getContext('2d').drawImage(img, 0, 0);
  const d = c0.getContext('2d').getImageData(0, 0, sw, sh).data;

  // 赤いマークの位置を測る（ロゴのうち赤いのはマークだけ。文字は黒）
  let minx = 1e9, miny = 1e9, maxx = -1, maxy = -1;
  for (let y = 0; y < sh; y++) for (let x = 0; x < sw; x++) {
    const i = (y*sw + x)*4;
    if (d[i+3] > 40 && d[i] > 140 && d[i+1] < 110 && d[i+2] < 110) {
      if (x < minx) minx = x; if (x > maxx) maxx = x;
      if (y < miny) miny = y; if (y > maxy) maxy = y;
    }
  }
  const mw = maxx - minx + 1, mh = maxy - miny + 1;
  const side = Math.max(mw, mh);

  // マークを正方形の中央に置いて、少しずつ拡大する（一気に拡げるとぼやけるため）
  let c = document.createElement('canvas');
  c.width = side; c.height = side;
  let g = c.getContext('2d');
  g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.drawImage(img, minx, miny, mw, mh, Math.round((side-mw)/2), Math.round((side-mh)/2), mw, mh);
  while (c.width < work) {
    const n = document.createElement('canvas');
    const nw = Math.min(work, Math.round(c.width * 1.3));
    n.width = nw; n.height = nw;
    const ng = n.getContext('2d');
    ng.imageSmoothingEnabled = true; ng.imageSmoothingQuality = 'high';
    ng.drawImage(c, 0, 0, nw, nw);
    c = n;
  }

  // マークの輪郭の外側を透過させる。輪郭は実測した縦横比の楕円
  const g2 = c.getContext('2d');
  g2.globalCompositeOperation = 'destination-in';
  g2.beginPath();
  g2.ellipse(work/2, work/2, work/2 * (mw/side), work/2 * (mh/side), 0, 0, Math.PI*2);
  g2.fill();
  g2.globalCompositeOperation = 'source-over';

  // タブ用。小さく使うものなので、ここで縮めておく
  const f = document.createElement('canvas');
  f.width = size; f.height = size;
  const gf = f.getContext('2d');
  gf.imageSmoothingEnabled = true; gf.imageSmoothingQuality = 'high';
  gf.drawImage(c, 0, 0, size, size);

  // iOS 用は白地。透過のままだと黒く塗られるため
  const a = document.createElement('canvas');
  a.width = appleSize; a.height = appleSize;
  const ga = a.getContext('2d');
  ga.fillStyle = '#ffffff';
  ga.fillRect(0, 0, appleSize, appleSize);
  const inner = Math.round(appleSize * (1 - applePad*2));
  const off = Math.round((appleSize - inner)/2);
  ga.imageSmoothingEnabled = true; ga.imageSmoothingQuality = 'high';
  ga.drawImage(c, off, off, inner, inner);

  return [f.toDataURL('image/png').split(',')[1],
          a.toDataURL('image/png').split(',')[1],
          minx, miny, mw, mh];
}"""


async def main():
    from playwright.async_api import async_playwright
    data = "data:image/png;base64," + base64.b64encode(SRC.read_bytes()).decode()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 600, "height": 400})
        await pg.set_content(f'<body style="margin:0"><img id="i" src="{data}"></body>')
        await pg.wait_for_function("document.getElementById('i').complete")
        fav, apple, x, y, w, h = await pg.evaluate(JS, [SIZE, APPLE_SIZE, APPLE_PAD, WORK])
        await b.close()
    FAVICON.write_bytes(base64.b64decode(fav))
    APPLE.write_bytes(base64.b64decode(apple))
    print(f"ロゴ内のマーク: ({x},{y}) {w}×{h}")
    print(f"ファビコン: {FAVICON.name} {SIZE}×{SIZE} 透過 ({FAVICON.stat().st_size//1024}KB)")
    print(f"iOS用:     {APPLE.name} {APPLE_SIZE}×{APPLE_SIZE} 白地 ({APPLE.stat().st_size//1024}KB)")


asyncio.run(main())
