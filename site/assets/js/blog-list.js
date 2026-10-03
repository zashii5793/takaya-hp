/* お知らせ一覧の絞り込み（分類ボタンとキーワード検索）。
 *
 * 記事は全件がページに書いてあり、ここでは見せる・隠すを切り替えるだけ。
 * キーワードは、まず題名・書き出し・分類で探し、本文の索引（search.json）が
 * 読めたら本文も含めて探し直す。索引は重いので、検索欄を使ったときに初めて読む。
 */
(function () {
  'use strict';

  var box = document.querySelector('[data-blog-list]');
  if (!box) return;

  var input = box.querySelector('input[type="search"]');
  var chips = box.querySelectorAll('.blog-chip');
  var count = box.querySelector('.blog-count');
  var scroller = document.querySelector('.post-scroll');
  var empty = document.querySelector('.blog-empty');
  var cards = document.querySelectorAll('.post-cards .post-card');
  var total = cards.length;
  var DEFAULT_MSG = count ? count.textContent : '';

  var cat = '';
  var bodies = null;      // slug → 本文の文字
  var loading = false;

  /* 全角・半角や大文字・小文字の違いで見落とさないようにそろえる */
  function norm(s) {
    s = String(s || '');
    if (s.normalize) s = s.normalize('NFKC');
    return s.toLowerCase().replace(/\s+/g, ' ');
  }

  var heads = [];
  for (var i = 0; i < cards.length; i++) heads.push(norm(cards[i].textContent));

  function loadBodies() {
    if (bodies || loading || !window.fetch) return;
    loading = true;
    fetch('search.json')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        bodies = {};
        if (!d) { apply(); return; }
        for (var k in d) if (Object.prototype.hasOwnProperty.call(d, k)) bodies[k] = norm(d[k]);
        apply();
      })
      .catch(function () { bodies = {}; apply(); });   /* 読めなければ題名と書き出しだけで探す */
  }

  function apply() {
    var words = norm(input ? input.value : '').trim().split(' ').filter(Boolean);
    var shown = 0;
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      var ok = !cat || c.getAttribute('data-cat') === cat;
      if (ok && words.length) {
        var hay = heads[i];
        if (bodies) hay += ' ' + (bodies[c.getAttribute('data-slug')] || '');
        for (var w = 0; w < words.length; w++) {
          if (hay.indexOf(words[w]) < 0) { ok = false; break; }
        }
      }
      c.hidden = !ok;
      if (ok) shown++;
    }
    if (empty) empty.hidden = shown > 0;
    if (count) {
      if (!cat && !words.length) count.textContent = DEFAULT_MSG;
      else {
        var what = [];
        if (cat) what.push('分類「' + cat + '」');
        if (words.length) what.push('「' + input.value.trim() + '」');
        count.textContent = what.join('・') + 'で ' + shown + '件 見つかりました（全' + total + '件中）'
          + (words.length && !bodies ? '。本文も含めて探しています…' : '');
      }
    }
    if (scroller) scroller.scrollTop = 0;
  }

  for (var j = 0; j < chips.length; j++) {
    chips[j].addEventListener('click', function () {
      cat = this.getAttribute('data-cat') || '';
      for (var k = 0; k < chips.length; k++) {
        chips[k].setAttribute('aria-pressed', chips[k] === this ? 'true' : 'false');
      }
      apply();
    });
  }

  if (input) {
    var timer = null;
    input.addEventListener('focus', loadBodies);
    input.addEventListener('input', function () {
      loadBodies();
      clearTimeout(timer);
      timer = setTimeout(apply, 120);
    });
  }
})();
