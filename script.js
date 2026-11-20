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
  var budget = document.getElementById('budget');
  var tri = document.getElementById('tri');
  var grid = document.getElementById('grid');
  var mts = Array.prototype.slice.call(document.querySelectorAll('.mt'));
  var gcs = Array.prototype.slice.call(document.querySelectorAll('.gc'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var reset = document.getElementById('reset');
  function norm(s) { return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function apply() {
    var text = norm(q.value).trim(), m = mois.value, r = region.value, g = genre.value, b = budget.value, n = 0;
    cards.forEach(function (c) {
      var ok = (!text || c.dataset.name.indexOf(text) !== -1) &&
               (!m || c.dataset.mois.split(' ').indexOf(m) !== -1) &&
               (!r || c.dataset.region === r) &&
               (!g || c.dataset.genres.split('|').indexOf(g) !== -1) &&
               (!b || (b === 'free' ? c.dataset.free === '1' : (c.dataset.price !== '' && parseFloat(c.dataset.price) <= parseFloat(b))));
      c.hidden = !ok;
      if (ok) n++;
    });
    mts.forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.m === m ? 'true' : 'false'); });
    gcs.forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.g === g ? 'true' : 'false'); });
    count.textContent = n + (n > 1 ? ' festivals' : ' festival');
    empty.hidden = n !== 0;
  }
  function sortCards() {
    var k = tri.value;
    var list = cards.slice().sort(function (a, b) {
      if (k === 'date') return a.dataset.d - b.dataset.d;
      if (k === 'az') return a.querySelector('h3').textContent.localeCompare(b.querySelector('h3').textContent, 'fr');
      if (k === 'prix') {
        var pa = a.dataset.price === '' ? 1e9 : parseFloat(a.dataset.price), pb = b.dataset.price === '' ? 1e9 : parseFloat(b.dataset.price);
        if (pa !== pb) return pa - pb;
      }
      return a.dataset.i - b.dataset.i;
    });
    list.forEach(function (c) { grid.appendChild(c); });
  }
  tri.addEventListener('change', sortCards);
  mts.forEach(function (x) { x.addEventListener('click', function () { mois.value = mois.value === x.dataset.m ? '' : x.dataset.m; apply(); }); });
  gcs.forEach(function (x) { x.addEventListener('click', function () { genre.value = genre.value === x.dataset.g ? '' : x.dataset.g; apply(); }); });
  [q, mois, region, genre, budget].forEach(function (el) {
    el.addEventListener('input', apply);
    el.addEventListener('change', apply);
  });
  if (reset) reset.addEventListener('click', function () {
    q.value = ''; mois.value = ''; region.value = ''; genre.value = ''; budget.value = ''; apply();
  });
  apply();
})();

// Compte à rebours (calculé dans le navigateur, aucune donnée envoyée).
(function () {
  var day = 86400000, now = new Date(), today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  function d(s) { var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  Array.prototype.forEach.call(document.querySelectorAll('.cd[data-start]'), function (el) {
    var a = d(el.dataset.start), b = d(el.dataset.end), n = Math.round((a - today) / day);
    el.textContent = today > b ? '' : today >= a ? 'En cours' : n === 1 ? 'Demain' : 'Dans ' + n + ' jours';
  });
})();

// Bouton Partager : partage natif si disponible, sinon copie du lien.
(function () {
  var b = document.querySelector('.share-btn');
  if (!b) return;
  b.addEventListener('click', function () {
    var msg = document.querySelector('.share-msg'), url = location.href.split('#')[0];
    if (navigator.share) { navigator.share({ title: b.dataset.title, url: url }).catch(function () {}); return; }
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () { msg.textContent = 'Lien copié.'; }, function () { msg.textContent = url; });
    else msg.textContent = url;
  });
})();

// Calculateur de budget : calcul local, aucune donnée enregistrée ni envoyée.
(function () {
  var box = document.querySelector('[data-budget]');
  if (!box) return;
  var out = document.querySelector('.budget-total');
  var ids = ['b-bil', 'b-trans', 'b-loge', 'b-vie'];
  function val(id) { var v = parseFloat(document.getElementById(id).value.replace(',', '.')); return isNaN(v) || v < 0 ? 0 : v; }
  function fmt(n) { return n.toLocaleString('fr-FR', { maximumFractionDigits: 0 }) + ' €'; }
  function calc() {
    var n = Math.max(1, Math.min(20, parseInt(document.getElementById('b-pers').value, 10) || 1));
    var each = 0; ids.forEach(function (i) { each += val(i); });
    if (!each) { out.textContent = ''; return; }
    out.innerHTML = '<strong>Total : ' + fmt(each * n) + '</strong>' + (n > 1 ? ' (' + fmt(each) + ' par personne)' : '');
  }
  box.addEventListener('input', calc);
  calc();
})();
