const q=document.querySelector('#question'), ask=document.querySelector('#ask'), result=document.querySelector('#result'), answer=document.querySelector('#answer'), support=document.querySelector('#support');
document.querySelectorAll('[data-q]').forEach(b=>b.addEventListener('click',()=>{q.value=b.dataset.q;q.focus()}));
function money(n){return '₹'+Number(n||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2})}
function box(label,value){return `<div class="data-box"><small>${label}</small><strong>${value}</strong></div>`}
function render(data){
 answer.textContent=data.answer; const d=data.supporting_data||{}; let html='<div class="data-grid">';
 if(d.formula) html+=box('CALCULATION',d.formula)+box('ELIGIBLE TRANSACTIONS',d.eligible_transactions)+box('UNITS SOLD',d.units_sold);
 if(d.top_product) {html+=box('TOP PRODUCT',d.top_product.product)+box('PRODUCT REVENUE',money(d.top_product.revenue))+box('UNITS',d.top_product.units);html+='<div class="data-box" style="grid-column:1/-1"><small>PRODUCT REVENUE RANKING</small><ul>'+d.ranking.map(x=>`<li><span>${x.product}</span><b>${money(x.revenue)}</b></li>`).join('')+'</ul></div>'}
 if(d.monthly_revenue){html+='<div class="data-box" style="grid-column:1/-1"><small>MONTHLY NET REVENUE</small><ul>'+d.monthly_revenue.map(x=>`<li><span>${x.month}</span><b>${money(x.revenue)}</b></li>`).join('')+'</ul></div>'}
 if(d.top_region){html+=box('TOP REGION',d.top_region.region)+box('REGION REVENUE',money(d.top_region.revenue));html+='<div class="data-box" style="grid-column:1/-1"><small>REGIONAL BREAKDOWN</small><ul>'+d.regional_breakdown.map(x=>`<li><span>${x.region}</span><b>${money(x.revenue)}</b></li>`).join('')+'</ul></div>'}
 if(d.from_month){html+=box(d.from_month,money(d.from_revenue))+box(d.to_month,money(d.to_revenue))+box('ABSOLUTE CHANGE',money(d.absolute_change))+box('PERCENTAGE CHANGE',d.percentage_change===null?'N/A':d.percentage_change+'%')}
 html+='</div>';support.innerHTML=html;result.classList.remove('hidden');result.scrollIntoView({behavior:'smooth',block:'nearest'});
}
ask.addEventListener('click',async()=>{if(q.value.trim().length<2){result.classList.remove('hidden');answer.innerHTML='<div class="error">Please enter a question with at least two characters.</div>';support.innerHTML='';return}
 ask.disabled=true;ask.textContent='Analyzing…';result.classList.remove('hidden');answer.textContent='Running a validated database query…';support.innerHTML='';
 try{const res=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q.value.trim()})});const data=await res.json();if(!res.ok)throw new Error(data.detail||'Request failed');render(data)}
 catch(e){answer.innerHTML=`<div class="error">${e.message}</div>`;support.innerHTML=''}
 finally{ask.disabled=false;ask.innerHTML='Analyze question <b>→</b>'}
});
q.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter')ask.click()});
