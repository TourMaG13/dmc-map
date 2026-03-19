(function () {
  var container = document.getElementById('destimag-dmc-map');
  if (!container) {
    console.error('Carte DMC : element #destimag-dmc-map introuvable.');
    return;
  }

  var embedHeight = container.getAttribute('data-embed-height') || '400px';
  var fullHeight = container.getAttribute('data-full-height') || '100vh';
  var src = 'https://tourmag13.github.io/dmc-map/index.html';

  container.style.width = '100%';
  container.style.height = embedHeight;
  container.style.transition = 'height 0.3s ease';
  container.style.overflow = 'hidden';

  var iframe = document.createElement('iframe');
  iframe.src = src;
  iframe.style.cssText = 'width:100%;height:100%;border:none;display:block';
  iframe.setAttribute('allowfullscreen', 'true');
  iframe.setAttribute('title', 'Carte des DMC — DestiMaG');
  container.innerHTML = '';
  container.appendChild(iframe);

  // Ecouter les messages de la carte pour redimensionner
  window.addEventListener('message', function (e) {
    if (!e.data || !e.data.type) return;
    if (e.data.type === 'dmc-map-open') {
      container.style.height = fullHeight;
      container.style.position = 'fixed';
      container.style.inset = '0';
      container.style.zIndex = '99999';
      document.body.style.overflow = 'hidden';
    }
    if (e.data.type === 'dmc-map-close') {
      container.style.height = embedHeight;
      container.style.position = '';
      container.style.inset = '';
      container.style.zIndex = '';
      document.body.style.overflow = '';
    }
    if (e.data.type === 'dmc-map-resize' && e.data.height) {
      embedHeight = e.data.height + 'px';
      if (!container.style.position || container.style.position === '') {
        container.style.height = embedHeight;
      }
    }
  });
})();
