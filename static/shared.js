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
