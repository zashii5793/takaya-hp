/* Googleブログ（Blogger）の記事を、お知らせ欄に並べる。
 *
 * Blogger は JSONP（alt=json-in-script）に対応しているので、
 * サーバー側の用意は要らない。さくらのような静的なサーバーでもそのまま動く。
 *
 * 置き場所のきまり
 *   <ul data-blog-feed data-max="2"> … </ul>
 *     data-max    取得件数
 *     data-detail あると、日付・題名に加えて書き出しと写真も出す（お知らせ一覧用）
 *   読み込めなかったときは、中に書いてある内容をそのまま残す。
 *   （ブログへのリンクを書いておけば、失敗してもお客様は行き先を失わない）
 */
(function () {
  'use strict';

  var BLOG_ID = '2118329274297060498';
  var TIMEOUT = 8000;

  var lists = document.querySelectorAll('[data-blog-feed]');
  if (!lists.length) return;

  var max = 0;
  for (var i = 0; i < lists.length; i++) {
    max = Math.max(max, parseInt(lists[i].getAttribute('data-max'), 10) || 5);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function ymd(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    return d.getFullYear() + '.' +
      ('0' + (d.getMonth() + 1)).slice(-2) + '.' +
      ('0' + d.getDate()).slice(-2);
  }

  /* 記事本文からタグを除いて、書き出しだけを取り出す */
  function excerpt(html, n) {
    var t = String(html || '')
      .replace(/<[^>]*>/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/\s+/g, ' ')
      .trim();
    return t.length > n ? t.slice(0, n) + '…' : t;
  }

  function permalink(links) {
    for (var i = 0; i < (links || []).length; i++) {
      if (links[i].rel === 'alternate' && links[i].type === 'text/html') return links[i].href;
    }
    return '';
  }

  function render(list, entries) {
    var detail = list.hasAttribute('data-detail');
    var n = parseInt(list.getAttribute('data-max'), 10) || 5;
    var html = '';

    for (var i = 0; i < Math.min(entries.length, n); i++) {
      var e = entries[i];
      var url = permalink(e.link);
      if (!url) continue;
      var date = ymd(e.published && e.published.$t);
      var title = esc((e.title && e.title.$t) || '（無題）');
      var a = '<a href="' + esc(url) + '" target="_blank" rel="noopener">' + title + '</a>';

      if (!detail) {
        html += '<li><time>' + date + '</time>' + a + '</li>';
        continue;
      }

      var body = (e.content && e.content.$t) || (e.summary && e.summary.$t) || '';
      var cat = (e.category && e.category.length)
        ? '<span class="post__cat">' + esc(e.category[0].term) + '</span>' : '';
      html += '<li class="post"><time>' + date + '</time>'
        + '<div>' + a + cat
        + '<p class="post__excerpt">' + esc(excerpt(body, 90)) + '</p></div></li>';
    }

    /* 1件も作れなかったときは、いま出ているものを残す */
    if (html) list.innerHTML = html;
  }

  /* 読み込めなかったときの表示。「読み込んでいます」のまま止めない */
  function giveUp() {
    for (var i = 0; i < lists.length; i++) {
      var el = lists[i].querySelector('[data-blog-loading]');
      if (el) el.textContent = 'お知らせは準備中です。';
    }
  }

  /* ブログ本体へのリンクは、取得した公開アドレスを入れてから見せる */
  function showBlogLink(href) {
    if (!href) return;
    var as = document.querySelectorAll('[data-blog-link]');
    for (var i = 0; i < as.length; i++) {
      as[i].setAttribute('href', href);
      as[i].hidden = false;
    }
  }

  var done = false;

  window.takayaBlogFeed = function (json) {
    if (done) return;
    done = true;
    try {
      var feed = json && json.feed;
      var entries = (feed && feed.entry) || [];
      showBlogLink(permalink(feed && feed.link));
      if (!entries.length) { giveUp(); return; }
      for (var i = 0; i < lists.length; i++) render(lists[i], entries);
    } catch (err) {
      giveUp();
    }
  };

  var s = document.createElement('script');
  s.src = 'https://www.blogger.com/feeds/' + BLOG_ID +
    '/posts/default?alt=json-in-script&max-results=' + max + '&callback=takayaBlogFeed';
  s.async = true;
  s.onerror = function () { if (!done) { done = true; giveUp(); } };
  document.head.appendChild(s);

  /* 応答が来ないまま固まらないようにする */
  setTimeout(function () { if (!done) { done = true; giveUp(); } }, TIMEOUT);
})();
