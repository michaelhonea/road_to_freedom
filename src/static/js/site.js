// Mobile menu + Lessons dropdown. No dependencies.
(function () {
  var btn = document.querySelector('.navtoggle');
  var nav = document.getElementById('mainnav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
  var dd = document.querySelector('.dd');
  if (dd) {
    var label = dd.querySelector('.ddlabel');
    // On touch/narrow screens, first tap opens the submenu; second tap follows the link.
    label.addEventListener('click', function (e) {
      if (window.matchMedia('(max-width: 900px)').matches && !dd.classList.contains('show')) {
        e.preventDefault();
        dd.classList.add('show');
      }
    });
    document.addEventListener('click', function (e) {
      if (!dd.contains(e.target)) dd.classList.remove('show');
    });
  }
})();
