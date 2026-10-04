window.__play=async function(){
 const LOG=[],ERR=[];window.__log=LOG;window.__err=ERR;addEventListener('error',e=>ERR.push('onerror: '+e.message+' @'+e.lineno));
 const wait=ms=>new Promise(r=>setTimeout(r,ms));const shot=async n=>{window.__shotDone=false;console.log('SHOT:'+n);const t=Date.now();while(!window.__shotDone&&Date.now()-t<8000)await wait(30)};
 const check=(c,m)=>{if(!c)ERR.push('ASSERT: '+m);LOG.push((c?'ok  ':'FAIL ')+m)};
 try{
  localStorage.clear();S={caught:{},day:today(),newToday:0,v:1};render();await wait(200);
  check(document.querySelectorAll('.stop').length===6&&document.querySelectorAll('.stop[disabled]').length===5,'map: 6 areas, only Pallet Town open');await shot('01-map');
  document.querySelector('.stop').click();await wait(200);
  const lines=document.querySelectorAll('.line');check(lines.length>0,'Pallet Town scene shows '+lines.length+' lines');
  check(document.querySelectorAll('.w.new').length>0,'new words glow');await shot('02-scene');
  const nw=document.querySelector('.w.new');const word=nw.dataset.w;nw.click();await wait(200);
  check(!!document.querySelector('.sheet #catch'),'catch card for '+word);await shot('03-catch');
  document.querySelector('#enq').click();await wait(80);await shot('03b-catch-en');
  document.querySelector('#catch').click();await wait(300);
  const right=[...document.querySelectorAll('.opt')].find(b=>b.dataset.o===word);
  if(right){await shot('04-battle');[...document.querySelectorAll('.opt')].find(b=>b.dataset.o!==word)?.click();await wait(150);right.click();await wait(1200)}
  else LOG.push('  (no cloze line for '+word+')');
  check(caught(word)&&S.newToday===1,'caught '+word+', today 1/20');
  // tap an ordinary word for the dictionary
  const plain=document.querySelector('.line .w:not(.new)');if(plain){plain.click();await wait(150);check(!$('gloss').hidden||!$('toast').hidden,'tapping a plain word opens the dictionary: '+plain.textContent);await shot('05-gloss');
   if(!$('gloss').hidden){$('gloss').querySelector('div').click();await wait(60);check($('gloss').classList.contains('pinned'),'tapping the definition pins it');
    await wait(7500);check(!$('gloss').hidden,'a pinned definition stays open');await shot('05a-pinned');$('gloss').querySelector('.gx').click();await wait(60);check($('gloss').hidden,'× closes it')}}
  // 찾아본 말: the plain word just tapped is listed with a count; tapping it shows the English
  go('taps');await wait(150);const tp=document.querySelectorAll('.tp');check(tp.length>=1,'사전 lists '+tp.length+' looked-up word(s): '+(tp[0]?.querySelector('.tph')?.textContent||''));
  if(tp[0]){tp[0].click();await wait(60);check(!tp[0].querySelector('.tpe').hidden,'tapping it shows the English')}await shot('05b-taps');
  // review: make it due
  S.caught[word].due=Date.now()-1;save();go('wild');await wait(150);check(!!$('start'),'wild encounter waiting');await shot('06-wild');
  $('start').click();await wait(300);await shot('07-review');
  if(document.querySelector('#show')){document.querySelector('#show').click();await wait(100);await shot('07b-reveal');document.querySelector('#yes').click()}
  else{const r=[...document.querySelectorAll('.opt')].find(b=>b.dataset.o===word);r&&r.click();await wait(1200)}
  await wait(400);check(S.caught[word].b>=1,'review graded: level '+S.caught[word].b);
  dexTab=W[word].cat;go('dex');await wait(150);check(document.querySelectorAll('.tile:not(.unseen)').length>=1,'dex shows the caught word');await shot('08-dex');
  // unlock check: catch all Pallet guide words → Route 1 opens
  guide(0).forEach(w=>{S.caught[w]=S.caught[w]||{b:1,due:Date.now()+1e9,t:1}});save();go('map');await wait(150);
  check(!document.querySelectorAll('.stop')[1].disabled,'catching Pallet Town guide words opens 1번 도로');await shot('09-route1');
 }catch(e){ERR.push('flow: '+e.message+' '+e.stack)}
 window.__done=true;console.log('DONE');
};
