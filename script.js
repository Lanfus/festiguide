(function () {
  var q = document.getElementById('q');
  var m = document.getElementById('mois');
  var p = document.getElementById('pays');
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  function norm(s) { return (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
  function apply() {
    var text = norm(q.value), mois = m.value, pays = p.value, n = 0;
    cards.forEach(function (c) {
      var ok = (!text || norm(c.dataset.name).indexOf(text) !== -1) &&
               (!mois || c.dataset.mois.split(' ').indexOf(mois) !== -1) &&
               (!pays || c.dataset.pays === pays);
      c.hidden = !ok;
      if (ok) n++;
    });
    count.textContent = n + (n > 1 ? ' festivals' : ' festival');
    empty.hidden = n !== 0;
  }
  [q, m, p].forEach(function (el) { el.addEventListener('input', apply); });
  apply();
})();
