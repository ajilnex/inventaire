/* INVENTAIRE — comportements. Zéro dépendance. */
(function () {
  "use strict";

  // barre de progression de lecture
  var bar = document.getElementById("bar");
  if (bar) {
    var onScroll = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (100 * h.scrollTop / max) : 0) + "%";
    };
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // navigation clavier : flèches ou j / k entre modules
  var prev = document.querySelector('nav.pied a[rel="prev"]');
  var next = document.querySelector('nav.pied a[rel="next"]');
  addEventListener("keydown", function (e) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.metaKey || e.ctrlKey || e.altKey) return;
    if ((e.key === "ArrowLeft" || e.key === "k") && prev) location.href = prev.getAttribute("href");
    if ((e.key === "ArrowRight" || e.key === "j") && next) location.href = next.getAttribute("href");
  });

  // apparition douce des figures et sections
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("on"); io.unobserve(en.target); }
      });
    }, { threshold: 0.15 });
    // le bloc audio n'est jamais animé : c'est la première offre de la page,
    // il doit être visible même si ce script ne s'exécute pas.
    document.querySelectorAll("figure.diagram").forEach(function (el) {
      el.classList.add("rise");
      io.observe(el);
    });
  }

  // horodatage du pied de page (culture terminal)
  var t = document.getElementById("epoch");
  if (t) t.textContent = "epoch " + Math.floor(Date.now() / 1000);
})();
