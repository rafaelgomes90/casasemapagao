/* Casa Sem Apagão — calculadora de autonomia */
(function(){
  var P = window.PRODUTOS || [], C = window.CSA, $ = function(id){ return document.getElementById(id); };
  var brl=C.brl, esc=C.esc, byId=C.byId;
  var ICON_EXT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>';
  function L(p, cls, inner, origem){ return '<a class="'+(cls||'')+'" href="'+esc(p.link)+'" target="_blank" rel="noopener sponsored" data-ml="'+p.id+'" data-origem="'+(origem||'')+'">'+inner+'</a>'; }
  function img(p){ return '<img src="'+esc(p.imagem)+'" alt="'+esc(p.nome)+'" loading="lazy" decoding="async">'; }
  function specs(p){ var s=[]; if(p.capacidadeWh) s.push(brl(p.capacidadeWh)+' Wh'); if(p.potenciaW) s.push(brl(p.potenciaW)+' W'); return s.join(' · '); }
  function botao(p, origem, sec){ return L(p, 'ml'+(sec?' sec2':''), (sec?'Ver no Mercado Livre':'Ver preço de hoje no Mercado Livre')+' '+ICON_EXT, origem); }

  var AP = [
    {id:'roteador',nome:'Roteador Wi‑Fi + modem',w:20,pico:20},
    {id:'celular',nome:'Celular carregando',w:15,pico:15},
    {id:'notebook',nome:'Notebook',w:60,pico:60},
    {id:'monitor',nome:'Monitor',w:30,pico:30},
    {id:'tv',nome:'TV LED 50"',w:100,pico:100},
    {id:'lampada',nome:'Lâmpada LED',w:9,pico:9},
    {id:'ventilador',nome:'Ventilador',w:60,pico:60},
    {id:'geladeira',nome:'Geladeira',w:70,pico:600,nota:'consumo médio (o motor liga e desliga)'},
    {id:'freezer',nome:'Freezer',w:60,pico:500,nota:'consumo médio (o motor liga e desliga)'},
    {id:'cpap',nome:'Aparelho CPAP',w:40,pico:40},
    {id:'bomba',nome:'Bomba d’água 1/2 cv',w:450,pico:1350},
    {id:'micro',nome:'Micro-ondas',w:1200,pico:1200}
  ];
  var qtd = {roteador:1,celular:2,geladeira:1,lampada:3}, horas = 8, mostrou=false;

  function calcular(){ var w=0, maior=null; AP.forEach(function(a){ var q=qtd[a.id]||0; if(q<=0) return; w+=a.w*q; if(!maior||a.pico>maior.pico) maior=a; });
    var pico = maior ? w - maior.w + maior.pico : 0; return {watts:w,pico:pico,wh:Math.round(w*horas/0.85)}; }
  function avaliar(r){ var ordem={ok:0,parcial:1,fraca:2};
    return P.filter(function(p){return p.categoria==='estacao'&&p.capacidadeWh;}).map(function(p){
      var ag = r.watts>0 ? p.capacidadeWh*0.85/r.watts : Infinity;
      var potOk = p.potenciaW>=r.watts && p.picoW>=r.pico;
      return {p:p, ag:ag, st: !potOk?'fraca':(ag>=horas?'ok':'parcial')};
    }).sort(function(a,b){ return ordem[a.st]-ordem[b.st] || (a.st==='ok'? a.p.precoAprox-b.p.precoAprox : b.ag-a.ag); }); }

  function renderAparelhos(){
    $('aparelhos').innerHTML = AP.map(function(a){ var q=qtd[a.id]||0;
      return '<li><div><span class="nm'+(q?'':' off')+'">'+esc(a.nome)+'</span>'+(a.nota?'<small>'+a.nota+'</small>':'')+'<small>'+a.w+' W'+(a.pico>a.w?' · pico '+a.pico+' W':'')+'</small></div>'+
        '<div class="qty"><button type="button" class="menos" data-d="-1" data-id="'+a.id+'" aria-label="Diminuir '+esc(a.nome)+'"'+(q?'':' disabled')+'>−</button><span aria-live="polite">'+q+'</span><button type="button" class="mais" data-d="1" data-id="'+a.id+'" aria-label="Aumentar '+esc(a.nome)+'">+</button></div></li>'; }).join('');
  }
  $('aparelhos').addEventListener('click', function(e){ var b=e.target.closest('button[data-id]'); if(!b) return;
    var id=b.getAttribute('data-id'); qtd[id]=Math.max(0,Math.min(20,(qtd[id]||0)+Number(b.getAttribute('data-d')))); renderAparelhos(); if(mostrou) renderResultado(); });
  $('horas').innerHTML=[4,8,12,24].map(function(h){ return '<button type="button" role="radio" data-h="'+h+'" aria-checked="'+(h===horas)+'">'+h+'h</button>'; }).join('');
  $('horas').addEventListener('click', function(e){ var b=e.target.closest('button[data-h]'); if(!b) return; horas=Number(b.getAttribute('data-h'));
    [].forEach.call($('horas').children,function(c){ c.setAttribute('aria-checked', String(Number(c.getAttribute('data-h'))===horas)); }); if(mostrou) renderResultado(); });

  function renderResultado(){
    var r=calcular(), lista=avaliar(r), rec=null; for(var i=0;i<lista.length;i++){ if(lista[i].st==='ok'){ rec=lista[i]; break; } }
    var h = '<div class="resumo"><div><small>Consumo</small><b>'+brl(r.watts)+' W</b></div><div><small>Pico estimado</small><b>'+brl(r.pico)+' W</b></div><div><small>Energia p/ '+horas+'h</small><b>'+brl(r.wh)+' Wh</b></div></div>';
    if(!rec){ var maior = P.filter(function(p){return p.categoria==='estacao';}).sort(function(a,b){return b.capacidadeWh-a.capacidadeWh;})[0], ger = byId['branco-b4t2000i'];
      h += '<div class="combo"><b>✨ Para essa necessidade, combine duas soluções</b><p style="margin:8px 0 0;font-size:14px">Nenhuma estação sozinha cobre esse consumo por '+horas+'h. O ideal é uma estação dentro de casa (liga sozinha e segura internet, luz e geladeira sem barulho) e um gerador inverter do lado de fora para recarregá-la e ligar os aparelhos mais fortes por mais tempo.</p><div class="combo-grid">'+
        [maior,ger].map(function(p){ return '<div><div style="display:flex;gap:10px;align-items:center">'+L(p,'mini',img(p),'calc-combo')+'<div><a href="/'+p.id+'/"><b>'+esc(p.nome)+'</b></a><div style="color:var(--mut-fg);font-size:12px">'+specs(p)+' · por volta de R$ '+brl(p.precoAprox)+'</div></div></div><div style="margin-top:10px">'+botao(p,'calc-combo')+'</div></div>'; }).join('')+'</div></div>';
    }
    h += '<ul class="res-list">'+lista.map(function(x){ var p=x.p, isRec = rec && rec.p.id===p.id;
      var pct = x.st==='fraca'?100:Math.min(100, x.ag/horas*100), cor = x.st==='ok'?'var(--green)':(x.st==='parcial'?'var(--amber)':'#B9C0CB');
      var txt = x.st==='fraca' ? '<span style="color:var(--mut-fg)">Potência insuficiente: não liga '+(qtd.micro?'o micro-ondas':(qtd.bomba?'a bomba':'esses aparelhos juntos'))+'.</span>'
        : 'Aguenta <b>~'+(x.ag>=100?'100+':x.ag.toFixed(1).replace('.',','))+' h</b> com esses aparelhos'+(x.st==='parcial'?' <span style="color:var(--mut-fg)">(menos que '+horas+'h)</span>':'');
      return '<li class="res'+(isRec?' rec':'')+'">'+L(p,'mini',img(p),'calculadora-foto')+'<div class="info">'+(isRec?'<span class="tag-rec">Recomendada pra você</span>':'')+
        '<div class="top"><a href="/'+p.id+'/">'+esc(p.nome)+'</a><small>'+specs(p)+'</small></div><div class="bar"><i style="width:'+pct+'%;background:'+cor+'"></i></div><p>'+txt+'</p>'+
        (isRec? '<p style="color:var(--mut-fg);font-size:13px">por volta de R$ '+brl(p.precoAprox)+'</p>'+botao(p,'calculadora-botao') : (x.st==='parcial'? botao(p,'calculadora-botao',true):'') )+'</div></li>'; }).join('')+'</ul>'+
      '<p class="nota">Cálculo estimado com consumo médio; geladeiras variam conforme modelo e temperatura.</p>';
    $('resultado').innerHTML=h; $('resultado').hidden=false;
  }
  $('ver').addEventListener('click', function(){ var r=calcular(); if(!r.watts) return; mostrou=true; renderResultado();
    C.track('Lead',{content_name:'calculadora',value:r.watts}); C.trackC('CalculadoraUsada',{watts:r.watts,horas:horas});
    setTimeout(function(){ $('resultado').scrollIntoView({behavior:'smooth',block:'start'}); },50); });
  renderAparelhos();
})();
