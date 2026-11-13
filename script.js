(function () {
  var q = document.getElementById('q');
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
