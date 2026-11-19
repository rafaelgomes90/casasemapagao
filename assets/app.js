/* Casa Sem Apagão — funções comuns: UTM, pixel e clique pro Mercado Livre */
(function(){
  var KEY='csa_utm';
  try{ var sp=new URLSearchParams(location.search), u={};
    ['utm_source','utm_medium','utm_campaign','utm_content'].forEach(function(k){ var v=sp.get(k); if(v) u[k]=v; });
    if(Object.keys(u).length) sessionStorage.setItem(KEY, JSON.stringify(u));
  }catch(e){}
  function utm(){ try{ var u=JSON.parse(sessionStorage.getItem(KEY)||'{}'), o={}; if(u.utm_campaign) o.utm_campaign=u.utm_campaign; if(u.utm_content) o.utm_content=u.utm_content; return o; }catch(e){ return {}; } }
  function merge(a,b){ a=a||{}; for(var k in b) a[k]=b[k]; return a; }
  var CSA = window.CSA = {
    track:function(ev,p){ try{ if(window.fbq) window.fbq('track',ev,merge(p,utm())); }catch(e){} },
    trackC:function(ev,p){ try{ if(window.fbq) window.fbq('trackCustom',ev,merge(p,utm())); }catch(e){} },
    brl:function(n){ return Number(n).toLocaleString('pt-BR',{maximumFractionDigits:0}); },
    esc:function(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); },
    byId:{}
  };
  (window.PRODUTOS||[]).forEach(function(p){ CSA.byId[p.id]=p; });

  // Qualquer <a data-ml="id"> (foto, nome ou botão) dispara os mesmos eventos antes de abrir o Mercado Livre
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a[data-ml]'); if(!a) return;
    var p = CSA.byId[a.getAttribute('data-ml')]; if(!p) return;
    CSA.track('InitiateCheckout',{content_name:p.nome,content_ids:[p.id],content_type:'product',content_category:p.categoria,value:p.precoAprox,currency:'BRL'});
    CSA.trackC('CliqueML',{produto:p.nome,produto_id:p.id,categoria:p.categoria,etiqueta:p.etiqueta,origem:a.getAttribute('data-origem')||'',pagina:location.pathname});
  });

  // Botão "Resgatar cupom": abre o popup com o código; "Usar cupom" copia e leva pro produto no ML
  function copiar(t){ try{ if(navigator.clipboard&&window.isSecureContext){ navigator.clipboard.writeText(t); return true; } }catch(e){}
    try{ var x=document.createElement('textarea'); x.value=t; x.style.position='fixed'; x.style.opacity='0'; document.body.appendChild(x); x.select(); document.execCommand('copy'); x.remove(); return true; }catch(e){ return false; } }
  document.addEventListener('click', function(e){
    var b = e.target.closest && e.target.closest('a[data-cupom]'); if(!b) return;
    e.preventDefault();
    var id=b.getAttribute('data-cupom'), cod=b.getAttribute('data-codigo'), p=CSA.byId[id]||{};
    hit('click',p.nome||id,'abriucupom');
    CSA.trackC('AbriuCupom',{produto:p.nome||id,produto_id:id,cupom:cod,pagina:location.pathname});
    var old=document.getElementById('cupom-modal'); if(old) old.remove();
    var m=document.createElement('div'); m.id='cupom-modal'; m.className='cm-bg'; m.setAttribute('role','dialog'); m.setAttribute('aria-modal','true');
    m.innerHTML='<div class="cm"><button class="cm-x" aria-label="Fechar">×</button>'+
      '<p class="cm-tag">CUPOM DE DESCONTO</p><h3>Use no Mercado Livre</h3>'+
      '<div class="cm-cod"><code>'+CSA.esc(cod)+'</code><button class="cm-copy">Copiar</button></div>'+
      '<p class="cm-tx">Copie o código e cole no campo <b>cupom</b> na hora de pagar no Mercado Livre. O desconto vale conforme as regras e o estoque do cupom no ML.</p>'+
      '<a class="ml cm-usar" href="'+CSA.esc(b.getAttribute('href'))+'" target="_blank" rel="noopener sponsored" data-ml="'+CSA.esc(id)+'" data-origem="cupom">Usar cupom e comprar</a></div>';
    document.body.appendChild(m);
    var fechar=function(){ m.remove(); };
    m.addEventListener('click',function(ev){ if(ev.target===m||ev.target.closest('.cm-x')) fechar(); });
    document.addEventListener('keydown',function k(ev){ if(ev.key==='Escape'){ fechar(); document.removeEventListener('keydown',k); } });
    var cp=m.querySelector('.cm-copy');
    cp.addEventListener('click',function(){ if(copiar(cod)){ cp.textContent='Copiado ✓'; cp.classList.add('ok'); } });
    m.querySelector('.cm-usar').addEventListener('click',function(){ copiar(cod); setTimeout(fechar,300); });
  });

  // Página de produto: ViewContent do produto
  var pid = document.body.getAttribute('data-produto');
  if(pid && CSA.byId[pid]){ var p=CSA.byId[pid];
    CSA.track('ViewContent',{content_name:p.nome,content_ids:[p.id],content_type:'product',content_category:p.categoria,value:p.precoAprox,currency:'BRL'});
  }

  // Contador de visitantes (painel): visita, "estou online" a cada 20s e clique pro ML
  var HIT='/api/hit', sid;
  try{ sid=sessionStorage.getItem('csa_sid'); if(!sid){ sid=Math.random().toString(36).slice(2)+Date.now().toString(36); sessionStorage.setItem('csa_sid',sid); } }catch(e){ sid='x'+Math.random().toString(36).slice(2); }
  var EU=false; try{ EU=localStorage.getItem('csa_eu')==='1'; }catch(e){}
  function hit(t,prod){ if(EU) return; try{
    var u={}; try{ u=JSON.parse(sessionStorage.getItem(KEY)||'{}'); }catch(e){}
    var body=JSON.stringify({t:t,via:arguments[2]||'',sid:sid,p:location.pathname,prod:prod||'',src:u.utm_source||(document.referrer?new URL(document.referrer).hostname:''),ad:u.utm_content||''});
    if(navigator.sendBeacon) navigator.sendBeacon(HIT,new Blob([body],{type:'application/json'}));
    else fetch(HIT,{method:'POST',body:body,headers:{'Content-Type':'application/json'},keepalive:true});
  }catch(e){} }
  hit('view');
  setInterval(function(){ if(document.visibilityState==='visible') hit('ping'); },20000);
  document.addEventListener('visibilitychange',function(){ if(document.visibilityState==='visible') hit('ping'); });
  document.addEventListener('click',function(e){ var g=e.target.closest&&e.target.closest('a[data-grupo]'); if(!g) return;
    hit('click','Grupo WhatsApp','grupo'); CSA.track('Lead',{content_name:'Grupo Oferta do Rafa',origem:g.getAttribute('data-grupo'),pagina:location.pathname}); });
  document.addEventListener('click',function(e){ var a=e.target.closest&&e.target.closest('a[data-ml]'); if(!a) return; var p=CSA.byId[a.getAttribute('data-ml')]; hit('click',p?p.nome:a.getAttribute('data-ml'),a.getAttribute('data-origem')==='cupom'?'cupom':'ml'); });

  // Barra fixa do celular: aparece depois que o primeiro CTA sai da tela
  var flut=document.getElementById('flut'), alvo=document.querySelector('[data-flut-alvo]');
  if(flut && alvo && 'IntersectionObserver' in window){
    new IntersectionObserver(function(es){ var on=!(es[0]&&es[0].isIntersecting); flut.classList.toggle('on',on); flut.setAttribute('aria-hidden',String(!on)); }).observe(alvo);
  }
})();
