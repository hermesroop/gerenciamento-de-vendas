const sizes=['P','M','G','GG','G1','G2','G3'];
const $=id=>document.getElementById(id);
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e}
const dateLabel=value=>new Date(value).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'});
function summaryTable(orders){
 const map=new Map(),totals=Array(7).fill(0),table=el('table'),head=el('tr');
 ['Cor',...sizes,'Total'].forEach(x=>head.append(el('th',x)));table.append(head);
 for(const o of orders)for(const i of o.items){if(!map.has(i.color))map.set(i.color,Array(7).fill(0));map.get(i.color)[sizes.indexOf(i.size)]+=i.quantity}
 for(const [color,ns] of [...map].sort(([a],[b])=>a.localeCompare(b,'pt-BR'))){const tr=el('tr');[color,...ns,ns.reduce((a,b)=>a+b,0)].forEach(x=>tr.append(el('td',x)));ns.forEach((n,i)=>totals[i]+=n);table.append(tr)}
 const foot=el('tfoot'),tr=el('tr');['Total',...totals,totals.reduce((a,b)=>a+b,0)].forEach(x=>tr.append(el('td',x)));foot.append(tr);table.append(foot);return table;
}
async function api(url,options){const r=await fetch(url,options);if(!r.ok){let body;try{body=await r.json()}catch{}throw Error(typeof body?.detail==='string'?body.detail:'Não foi possível concluir. Confira os dados e tente novamente.')}return r.json()}

let confirmationQueue=Promise.resolve();
function confirmAction(message){
 const request=confirmationQueue.then(()=>new Promise(resolve=>{
  const dialog=el('dialog',undefined,'app-confirm'),title=el('h2','Confirmar ação'),body=el('p',message),actions=el('div',undefined,'batch-actions');
  title.id='confirmation-title';body.id='confirmation-description';dialog.setAttribute('aria-labelledby',title.id);dialog.setAttribute('aria-describedby',body.id);
  const cancel=el('button','Cancelar','secondary'),accept=el('button','Confirmar');cancel.type=accept.type='button';
  let result=false;cancel.onclick=()=>dialog.close();accept.onclick=()=>{result=true;dialog.close()};
  dialog.addEventListener('cancel',e=>{e.preventDefault();dialog.close()});
  dialog.addEventListener('close',()=>{dialog.remove();resolve(result)},{once:true});
  actions.append(cancel,accept);dialog.append(title,body,actions);document.body.append(dialog);dialog.showModal();cancel.focus();
 }));
 confirmationQueue=request.catch(()=>false);return request;
}
function notify(message){
 if(!message)return;document.querySelectorAll('.app-notice').forEach(n=>n.remove());
 const notice=el('div',undefined,'app-notice'),text=el('span',message),close=el('button','×','notice-close');
 notice.setAttribute('role','status');notice.setAttribute('aria-live','polite');close.type='button';close.setAttribute('aria-label','Fechar aviso');close.onclick=()=>notice.remove();notice.append(text,close);
 const dialogs=[...document.querySelectorAll('dialog[open]')];(dialogs.at(-1)||document.body).append(notice);
 setTimeout(()=>notice.remove(),10000);
}
// Retain messages next to their controls and also show a dismissible in-app notice.
for(const id of ['status','batch-status','modal-status','history-status','text-order-status']){
 const target=$(id);if(!target)continue;let last='';new MutationObserver(()=>{const message=target.textContent.trim();if(message&&message!==last)notify(message);last=message}).observe(target,{childList:true,subtree:true,characterData:true});
}
