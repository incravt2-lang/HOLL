'use strict';
const app=window.Telegram?.WebApp, el=id=>document.getElementById(id);
const input=el('body'), send=el('send'), log=el('log'), statusLine=el('status');
let visit=null, enabled=false, busy=false, last='', pending=null;
function controls(){input.disabled=!enabled;send.disabled=!enabled||busy||!input.value.trim();}
function paint(data){
  const moved=visit!==null&&visit!==data.visit;
  if(moved){input.value='';pending=null;}
  visit=data.visit;enabled=data.enabled;el('title').textContent=data.title;
  const stamp=JSON.stringify([visit,data.messages]);
  if(stamp!==last){
    const bottom=moved||!last||log.scrollHeight-log.scrollTop-log.clientHeight<50;
    const nodes=data.messages.map(([,nick,body,sec,mine])=>{
      const item=document.createElement('article'),by=document.createElement('div'),who=document.createElement('strong'),time=document.createElement('time'),p=document.createElement('p');
      by.className='by';if(mine)item.className='mine';who.textContent=nick;
      time.textContent=new Date(sec*1000).toLocaleTimeString('ru',{hour:'2-digit',minute:'2-digit'});
      p.textContent=body;by.append(who,time);item.append(by,p);return item;
    });
    log.replaceChildren(...nodes);if(bottom)log.scrollTop=log.scrollHeight;last=stamp;
  }
  statusLine.textContent=!enabled?'Здесь чат недоступен.':moved?'Ты перешёл в другую локацию.':!data.messages.length?'Пока тихо. Здесь появятся реплики с момента твоего прихода.':'';
}
async function refresh(post=false){
  if(busy||!app?.initData)return;
  busy=true;controls();const draft=input.value;
  try{
    let payload={auth:app.initData};
    if(post){
      if(!pending||pending.body!==draft||pending.visit!==visit)pending={nonce:crypto.randomUUID(),visit,body:draft};
      Object.assign(payload,pending);
    }
    const response=await fetch(post?'/send':'/history',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:typeof AbortSignal.timeout==='function'?AbortSignal.timeout(10000):undefined});
    const data=await response.json();
    if(!response.ok){
      if([401,403,409].includes(response.status)){enabled=false;log.replaceChildren();last='';if(response.status===409){input.value='';pending=null;}}
      throw Error(data.error);
    }
    if(post){if(input.value===draft)input.value='';pending=null;}
    paint(data);
  }catch(e){statusLine.textContent=e.message?.match(/[А-Яа-я]/)?e.message:'Связь прервалась. Попробуй ещё раз.';}
  finally{busy=false;controls();}
}
input.addEventListener('input',controls);
document.querySelector('form').onsubmit=e=>{e.preventDefault();if(!send.disabled)refresh(true);};
el('close').onclick=()=>app?.close();
if(app?.initData){app.ready();app.expand();refresh();setInterval(()=>{if(!document.hidden)refresh();},3000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});}
else statusLine.textContent='Открой чат кнопкой в игровой карточке Telegram.';
