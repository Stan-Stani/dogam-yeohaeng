import {execFileSync} from 'node:child_process';
// Usage: node tests/play.mjs ch1   → builds, plays the chapter by keyboard in headless Chrome, saves screenshots to tests/shots/ch1/
import {spawn} from 'node:child_process';import fs from 'node:fs';import path from 'node:path';
const ch=process.argv[2]||'ch1';const root=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..');
const out=path.join(root,'tests/shots',ch);fs.rmSync(out,{recursive:true,force:true});fs.mkdirSync(out,{recursive:true});
// One Chrome at a time on this machine (7 GB RAM froze when several ran at once): take a lock, wait for it.
const LOCK='/tmp/seongsilho-play.lock';
for(let t=0;;t++){try{fs.writeFileSync(LOCK,String(process.pid),{flag:'wx'});break}catch(e){
 let stale=true;try{process.kill(+fs.readFileSync(LOCK,'utf8'),0);stale=false}catch(_){}
 if(stale){fs.rmSync(LOCK,{force:true});continue}
 if(t%30===0)console.log('waiting for another playtest to finish…');await new Promise(r=>setTimeout(r,2000))}}
const unlock=()=>{try{if(fs.readFileSync(LOCK,'utf8')===String(process.pid))fs.rmSync(LOCK)}catch(e){}};
// Killing the flatpak wrapper leaves Chrome running inside the sandbox (287 orphans once) — kill everything using this run's profile.
const reap=()=>{try{execFileSync('pkill',['-9','-f',`user-data-dir=${tmp}/prof`])}catch(e){}};
process.on('exit',()=>{reap();unlock();try{fs.rmSync(tmp,{recursive:true,force:true})}catch(e){}});for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>{unlock();process.exit(130)});
const tmp=fs.mkdtempSync('/tmp/play-');
fs.copyFileSync(path.join(root,'index.html'),path.join(tmp,'built.html'));
const html=fs.readFileSync(path.join(tmp,'built.html'),'utf8');
const driver=fs.readFileSync(path.join(root,'tests/'+(process.argv[3]||'tapcheck')+'.js'),'utf8');
const walk='';
fs.writeFileSync(path.join(tmp,'play.html'),html.replace('</body></html>',`<script>${driver}\ntry{localStorage.clear()}catch(e){}\nsetTimeout(()=>__play(),900);</script>\n</body></html>`));
const port=9300+Math.floor(Math.random()*500);
const chrome=spawn('flatpak',['run',`--filesystem=${tmp}`,'com.google.Chrome','--headless=new','--disable-gpu','--hide-scrollbars',`--remote-debugging-port=${port}`,
 '--window-size=420,860',`--user-data-dir=${tmp}/prof`,'--autoplay-policy=no-user-gesture-required',`file://${tmp}/play.html`],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws;for(let i=0;i<60&&!ws;i++){try{const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();const pg=l.find(t=>t.type==='page');if(pg)ws=pg.webSocketDebuggerUrl}catch(e){}if(!ws)await sleep(500)}
if(!ws){console.error('chrome did not start');chrome.kill();process.exit(2)}
const sock=new WebSocket(ws);let id=0;const pend={};
const send=(method,params={})=>new Promise(r=>{const i=++id;pend[i]=r;sock.send(JSON.stringify({id:i,method,params}))});
let done=false;const queue=[];
sock.onmessage=async ev=>{const m=JSON.parse(ev.data);if(m.id&&pend[m.id]){pend[m.id](m.result);delete pend[m.id];return}
 if(m.method==='Runtime.consoleAPICalled'){const t=(m.params.args[0]||{}).value||'';
  if(typeof t==='string'&&t.startsWith('SHOT:'))queue.push(t.slice(5));if(t==='DONE')done=true}};
await new Promise(r=>sock.onopen=r);await send('Runtime.enable');await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride',{width:400,height:820,deviceScaleFactor:1,mobile:true});
const t0=Date.now();
while(!done&&Date.now()-t0<600000){
 while(queue.length){const name=queue.shift();await sleep(300);const s=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(s.data,'base64'));await send('Runtime.evaluate',{expression:'window.__shotDone=true'})}
 await sleep(100);
}
const res=await send('Runtime.evaluate',{expression:'JSON.stringify({err:window.__err||["no run"],log:window.__log||[]})',returnByValue:true});
const {err,log}=JSON.parse(res.result.value);
const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,'99-end.png'),Buffer.from(shot.data,'base64'));
fs.writeFileSync(path.join(out,'log.txt'),'ERRORS:\n'+(err.join('\n')||'none')+'\n\nLOG:\n'+log.join('\n'));
sock.close();chrome.kill();reap();
console.log((done?'':'TIMEOUT\n')+'ERRORS: '+(err.length?'\n'+err.join('\n'):'none'));console.log('shots:',fs.readdirSync(out).filter(f=>f.endsWith('.png')).length,'→',out);
process.exit(err.length||!done?1:0);
