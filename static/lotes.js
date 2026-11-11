let currentBatch=null,editing=false,pending=false;
const modal=$('batch-modal');
function action(text,handler,cls){const b=el('button',text,cls);b.type='button';b.onclick=handler;return b}
function closeModal(){if(pending)return;if(editing&&!confirm('Descartar as alterações não salvas?'))return;modal.close()}
$('close-modal').onclick=closeModal;
modal.addEventListener('cancel',e=>{e.preventDefault();closeModal()});
modal.addEventListener('close',()=>{document.body.classList.remove('modal-open');editing=false;window.history.replaceState(null,'','/lotes')});
function presentBatch(batch){
 currentBatch=batch;editing=false;const area=$('batch-detail');area.replaceChildren();$('modal-status').textContent='';
 area.append(el('h2',batch.name),el('p','Gerado em '+dateLabel(batch.created_at)+' (horário de Brasília)'));
 if(batch.updated_at)area.append(el('p','Última edição: '+dateLabel(batch.updated_at)));
 const actions=el('div',undefined,'batch-actions report-actions');actions.append(action('Editar lote',editBatch,'secondary'),action('Excluir lote',removeBatch,'danger'),action('Imprimir / Salvar PDF',()=>window.print()));area.append(actions);
 for(const order of batch.orders){const a=el('article');a.append(el('h3','Pedido '+order.order+' • '+order.customer));const t=el('table'),head=el('tr');['Cor','Tamanho','Quantidade'].forEach(x=>head.append(el('th',x)));t.append(head);for(const i of order.items){const tr=el('tr');[i.color,i.size,i.quantity].forEach(x=>tr.append(el('td',x)));t.append(tr)}a.append(t,el('p','Total do pedido: '+order.items.reduce((n,i)=>n+i.quantity,0)+' camisetas'));area.append(a)}
 area.append(el('h3','Resumo geral do lote'));const scroll=el('div',undefined,'scroll');scroll.append(summaryTable(batch.orders));area.append(scroll);modal.scrollTop=0;
}
async function showBatch(id){try{const batch=await api('/api/batches/'+encodeURIComponent(id));presentBatch(batch);if(!modal.open)modal.showModal();document.body.classList.add('modal-open');window.history.replaceState(null,'','/lotes?lote='+encodeURIComponent(batch.id))}catch(e){$('history-status').textContent=e.message}}
async function removeBatch(){if(pending||!confirm('Excluir definitivamente o lote “'+currentBatch.name+'”? Esta ação não pode ser desfeita.'))return;pending=true;lockActions(true);try{const r=await fetch('/api/batches/'+encodeURIComponent(currentBatch.id),{method:'DELETE'});if(!r.ok)throw Error('Não foi possível excluir o lote. Atualize a página e tente novamente.');pending=false;editing=false;modal.close();await loadHistory();$('history-status').textContent='Lote excluído.'}catch(e){$('modal-status').textContent=e.message}finally{pending=false;lockActions(false)}}
function lockActions(disabled){modal.querySelectorAll('button').forEach(b=>b.disabled=disabled)}
function inputField(label,value,maxLength,type='text'){const wrap=el('label',label),input=el('input');input.type=type;input.value=value;input.required=true;input.setAttribute('aria-label',label);if(maxLength)input.maxLength=maxLength;if(type==='number'){input.min='1';input.max='1000000';input.step='1'}wrap.append(input);return [wrap,input]}
function editBatch(){
 editing=true;const draft=structuredClone(currentBatch),area=$('batch-detail');area.replaceChildren();$('modal-status').textContent='';
 const form=el('form');form.append(el('h2','Editar lote'));const [nameWrap,name]=inputField('Nome do lote',draft.name,200);form.append(nameWrap);
 for(const order of draft.orders){const a=el('article'),fields=el('div',undefined,'batch-actions');for(const [key,label,max] of [['order','Número do pedido',100],['customer','Nome do cliente',300]]){const [wrap,input]=inputField(label,order[key],max);input.oninput=()=>order[key]=input.value;fields.append(wrap)}a.append(fields);
 const scroll=el('div',undefined,'scroll'),table=el('table'),head=el('tr');['Cor','Tamanho','Quantidade'].forEach(x=>head.append(el('th',x)));table.append(head);
 for(const item of order.items){const tr=el('tr'),[cw,color]=inputField('Cor',item.color,100),[qw,qty]=inputField('Quantidade',item.quantity,null,'number'),select=el('select');select.setAttribute('aria-label','Tamanho');sizes.forEach(s=>{const o=el('option',s);o.value=s;select.append(o)});select.value=item.size;color.oninput=()=>item.color=color.value;qty.oninput=()=>item.quantity=Number(qty.value);select.onchange=()=>item.size=select.value;
 for(const input of [color,select,qty]){const td=el('td');td.append(input);tr.append(td)}table.append(tr)}scroll.append(table);a.append(scroll);form.append(a)}
 const actions=el('div',undefined,'batch-actions'),save=el('button','Salvar alterações');save.type='submit';actions.append(save,action('Cancelar edição',()=>{if(confirm('Descartar as alterações não salvas?'))presentBatch(currentBatch)},'secondary'));form.append(actions);area.append(form);name.focus();modal.scrollTop=0;
 form.onsubmit=async e=>{e.preventDefault();if(pending)return;draft.name=name.value;pending=true;lockActions(true);try{const saved=await api('/api/batches/'+encodeURIComponent(draft.id),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:draft.name,orders:draft.orders})});presentBatch(saved);$('modal-status').textContent='Alterações salvas. O resumo geral foi atualizado.';await loadHistory()}catch(err){$('modal-status').textContent=err.message}finally{pending=false;lockActions(false)}};
}
async function loadHistory(){const list=$('history-list');try{const batches=await api('/api/batches');list.replaceChildren();if(!batches.length)list.append(el('p','Nenhum lote salvo ainda.','muted'));for(const b of batches){const row=el('article'),button=action('Abrir lote',()=>showBatch(b.id));row.append(el('h3',b.name),el('p',dateLabel(b.created_at)+' • '+b.order_count+' pedidos • '+b.quantity+' camisetas'),button);list.append(row)}}catch(e){list.textContent='Não foi possível carregar o histórico. '+e.message}}
$('refresh-history').onclick=loadHistory;loadHistory();const batchId=new URLSearchParams(location.search).get('lote');if(batchId)showBatch(batchId);
