(function(){
  var c=document.getElementById('destimag-dmc-map');
  if(!c){console.warn('[DestiMaG] #destimag-dmc-map introuvable');return}
  var h=c.getAttribute('data-height')||'700px';
  var scripts=document.getElementsByTagName('script');
  var base='https://tourmag13.github.io/dmc-map/';
  for(var i=0;i<scripts.length;i++){
    if(scripts[i].src&&scripts[i].src.indexOf('embed-loader')!==-1){
      base=scripts[i].src.replace(/embed-loader\.js.*$/,'');
      break;
    }
  }
  var f=document.createElement('iframe');
  f.src=base+'index.html';
  f.style.cssText='width:100%;height:'+h+';border:none;border-radius:8px;display:block';
  f.setAttribute('allowfullscreen','true');
  f.setAttribute('loading','lazy');
  f.setAttribute('title','Carte des DMC — DestiMaG');
  c.innerHTML='';
  c.appendChild(f);
})();
