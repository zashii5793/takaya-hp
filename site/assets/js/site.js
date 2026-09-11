// ハンバーガーメニュー（スマホ）とナビの現在地表示
(function () {
  var toggle = document.querySelector('.nav-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.querySelectorAll('.nav a').forEach(function (a) {
      a.addEventListener('click', function () {
        document.body.classList.remove('nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }
})();

// 計測：主要なクリックを GA4 イベントとして送る（GA4 未設定なら何もしない）
// イベント名: tel_click / form_open / sns_click / map_click / service_click / blog_click / recruit_click
// パラメータ: area（header / hero / news / cta / footer / sp_bar / body）, link_url, link_text
(function () {
  function send(name, params) {
    if (typeof window.gtag === 'function') { window.gtag('event', name, params); }
  }
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href]');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var areaEl = a.closest('[data-area]');
    var params = { area: areaEl ? areaEl.getAttribute('data-area') : 'body',
                   link_url: href, link_text: (a.textContent || '').trim().slice(0, 60) };
    var name = null;
    if (href.indexOf('tel:') === 0) { name = 'tel_click'; params.tel = href.slice(4); }
    else if (/docs\.google\.com\/forms|contact\.html/.test(href)) { name = 'form_open'; }
    else if (/instagram\.com|x\.com|twitter\.com|facebook\.com|line\.me/.test(href)) { name = 'sns_click'; }
    else if (/google\.[a-z.]+\/maps|maps\.google/.test(href)) { name = 'map_click'; }
    else if (/services\//.test(href)) { name = 'service_click'; }
    else if (/blog\//.test(href)) { name = 'blog_click'; }
    else if (/miidas\.jp|indeed\.com/.test(href)) { name = 'apply_click'; }
    else if (/recruit\.html/.test(href)) { name = 'recruit_click'; }
    if (name) send(name, params);
  }, { passive: true });
})();
