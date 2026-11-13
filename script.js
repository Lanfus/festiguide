// Cartes : rien n'est demandé à Google tant que le visiteur n'a pas cliqué.
(function () {
  var wrap = document.querySelector('.map-wrap');
  if (!wrap) return;
  var btn = wrap.querySelector('.map-btn');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var src = wrap.getAttribute('data-map-src');
    if (!src) return;
    var frame = document.createElement('iframe');
    frame.className = 'map';
    frame.setAttribute('title', wrap.getAttribute('data-map-title') || 'Carte');
    frame.setAttribute('loading', 'lazy');
    frame.setAttribute('referrerpolicy', 'no-referrer');
    frame.setAttribute('src', src);
    wrap.innerHTML = '';
    wrap.appendChild(frame);
  });
})();

(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var mois = document.getElementById('mois');
  var region = document.getElementById('region');
  var genre = document.getElementById('genre');
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var reset = document.getElementById('reset');
  function norm(s) { return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function apply() {
    var text = norm(q.value).trim(), m = mois.value, r = region.value, g = genre.value, n = 0;
    cards.forEach(function (c) {
      var ok = (!text || c.dataset.name.indexOf(text) !== -1) &&
               (!m || c.dataset.mois.split(' ').indexOf(m) !== -1) &&
               (!r || c.dataset.region === r) &&
               (!g || c.dataset.genres.split('|').indexOf(g) !== -1);
      c.hidden = !ok;
      if (ok) n++;
    });
    count.textContent = n + (n > 1 ? ' festivals' : ' festival');
    empty.hidden = n !== 0;
  }
  [q, mois, region, genre].forEach(function (el) {
    el.addEventListener('input', apply);
    el.addEventListener('change', apply);
  });
  if (reset) reset.addEventListener('click', function () {
    q.value = ''; mois.value = ''; region.value = ''; genre.value = ''; apply();
  });
  apply();
})();
