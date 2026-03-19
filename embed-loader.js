(function () {
  var BASE_URL = 'https://tourmag13.github.io/dmc-map/';
  var CARTE_URL = BASE_URL + 'index.html';
  var container = document.getElementById('destimag-dmc-map');

  if (!container) {
    console.error('Carte DMC : element #destimag-dmc-map introuvable.');
    return;
  }

  var height = container.getAttribute('data-height') || '80vh';
  container.style.width = '100%';
  container.style.height = height;
  container.style.margin = '0 auto';
  container.style.position = 'relative';
  container.style.overflow = 'hidden';

  container.innerHTML = '<p style="text-align:center;padding-top:20%;color:#888;">Chargement de la carte des DMC…</p>';

  fetch(CARTE_URL)
    .then(function (response) {
      if (!response.ok) throw new Error('Erreur HTTP ' + response.status);
      return response.text();
    })
    .then(function (html) {
      var parser = new DOMParser();
      var doc = parser.parseFromString(html, 'text/html');

      container.innerHTML = '';

      // 1) Injecter les <style> et <link> du <head>
      var styles = doc.querySelectorAll('head style, head link[rel="stylesheet"]');
      styles.forEach(function (el) {
        var clone = document.importNode(el, true);
        container.appendChild(clone);
      });

      // 2) Collecter les scripts externes du <head>
      var headScripts = doc.querySelectorAll('head script[src]');
      var scriptsToLoad = [];

      headScripts.forEach(function (el) {
        var src = el.getAttribute('src');
        if (src && !src.startsWith('http') && !src.startsWith('//')) {
          src = BASE_URL + src;
        }
        scriptsToLoad.push({ src: src, content: null });
      });

      // 3) Injecter le contenu du <body>
      var bodyContent = doc.body ? doc.body.innerHTML : doc.documentElement.innerHTML;
      var wrapper = document.createElement('div');
      wrapper.className = 'destimag-dmc-wrapper';
      wrapper.style.width = '100%';
      wrapper.style.height = '100%';
      wrapper.innerHTML = bodyContent;
      container.appendChild(wrapper);

      // 4) Collecter les scripts inline et body scripts
      var bodyScripts = doc.querySelectorAll('body script');
      bodyScripts.forEach(function (el) {
        var src = el.getAttribute('src');
        if (src) {
          if (!src.startsWith('http') && !src.startsWith('//')) {
            src = BASE_URL + src;
          }
          scriptsToLoad.push({ src: src, content: null });
        } else if (el.textContent.trim()) {
          scriptsToLoad.push({ src: null, content: el.textContent });
        }
      });

      // Scripts inline du head
      var headInlineScripts = doc.querySelectorAll('head script:not([src])');
      headInlineScripts.forEach(function (el) {
        if (el.textContent.trim()) {
          scriptsToLoad.push({ src: null, content: el.textContent });
        }
      });

      // 5) Charger les scripts sequentiellement
      function loadNextScript(index) {
        if (index >= scriptsToLoad.length) return;
        var scriptInfo = scriptsToLoad[index];
        var script = document.createElement('script');

        if (scriptInfo.src) {
          script.src = scriptInfo.src;
          script.onload = function () {
            loadNextScript(index + 1);
          };
          script.onerror = function () {
            console.warn('Carte DMC : impossible de charger ' + scriptInfo.src);
            loadNextScript(index + 1);
          };
        } else {
          script.textContent = scriptInfo.content;
        }

        document.body.appendChild(script);

        if (!scriptInfo.src) {
          loadNextScript(index + 1);
        }
      }

      // Retirer les <script> du wrapper (deja geres)
      var injectedScripts = wrapper.querySelectorAll('script');
      injectedScripts.forEach(function (el) {
        el.remove();
      });

      loadNextScript(0);
    })
    .catch(function (err) {
      container.innerHTML = '<p style="text-align:center;padding-top:20%;color:red;">Erreur de chargement de la carte des DMC.</p>';
      console.error('Carte DMC :', err);
    });
})();
