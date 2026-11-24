(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"];
  const VIEW_LABELS = {overview:"نمای کلی",calendar:"تقویم هفته",library:"مخزن محتوا",motion:"آزمایشگاه موشن",brand:"مخزن هویت برند"};
  const state = {plan:null, reviews:{}, drafts:[], recipes:[], system:null, tokens:null, out:"/content-output/week-01", day:0, channel:"all", query:"", pillar:"all", review:"all", selectedDelivery:null, toastTimer:null, compact:false};
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const pad = n => String(n).padStart(2,"0");
  const channelLabel = id => ({instagram:"Instagram",telegram:"Telegram",website:"وب‌سایت",youtube:"YouTube"}[id] || id);
  const fmtLabel = id => ({story:"استوری",carousel:"کاروسل",main_reel:"ریلز",mini_reel:"میکرو ریلز",micro_reel:"ریلز کوتاه",animated_reel:"ریلز موشن",quote:"نقل‌قول",community_post:"پست تعاملی",single_map:"نقشهٔ تکی",single_infographic:"اینفوگرافیک",web_resource:"منبع وب",web_article:"مقالهٔ وب",telegram_file:"فایل تلگرام",telegram_guide:"راهنمای تلگرام",telegram_post:"پست تلگرام",telegram_prompt:"پرامپت",telegram_digest:"خلاصهٔ تلگرام"}[id] || id);
  const reviewState = id => state.reviews[id]?.status || "pending";
  const pillarById = id => state.system?.content_pillars?.find(p => p.id === id) || {id,title:id,fa:id,purpose_fa:"",destination:""};
  const colorFor = id => { const p=pillarById(id); return state.system?.colors?.section_accents?.[p.color_id] || state.tokens?.color?.strategic_navy?.hex || "#0A1931"; };
  const byId = id => state.plan?.content_items?.find(x => x.content_id === id);
  const deliveries = () => state.plan?.deliveries || [];
  const deliveriesFor = cid => deliveries().filter(x => x.content_id === cid);
  const pathFor = d => `${state.out}/${encodeURIComponent(d.day_name_fa)}/${d.content_id}/${d.delivery_id}`;
  const toast = msg => { const el=$("#toast"); el.textContent=msg; el.classList.add("show"); clearTimeout(state.toastTimer); state.toastTimer=setTimeout(()=>el.classList.remove("show"),2600); };
  const fetchJSON = async (url, options={}) => { const r=await fetch(url,{headers:{"Content-Type":"application/json",...(options.headers||{})},...options}); const d=await r.json().catch(()=>({error:"پاسخ سرور JSON معتبر نیست."})); if(!r.ok) throw new Error(d.error||`خطای ${r.status}`); return d; };

  function setView(name){
    $$(".view").forEach(v=>v.classList.toggle("active",v.id===`view-${name}`));
    $$(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.view===name));
    $("#currentViewName").textContent=VIEW_LABELS[name]||VIEW_LABELS.overview;
    $("#sidebar").classList.remove("open");
    if(name==="calendar") renderCalendar();
    if(name==="library") renderLibrary();
  }
  function makeDayStrip(target, selected, callback){
    const el=$(target); if(!el) return;
    el.innerHTML=`<button class="day-chip ${selected===0?"active":""}" data-day="0">همهٔ روزها<b>${deliveries().length} خروجی</b></button>`+DAYS.map((d,i)=>`<button class="day-chip ${selected===i+1?"active":""}" data-day="${i+1}">${esc(d)}<b>${deliveries().filter(x=>x.planned_day_index===i+1).length} تحویل</b></button>`).join("");
  }
  function selectMainDay(day){state.day=day; renderDayStrips();renderDeliveries();}
  function selectCalendarDay(day){state.day=day; renderDayStrips();renderCalendar();}
  function selectLibraryDay(day){state.day=day; renderDayStrips();renderLibrary();}
  function renderDayStrips(){makeDayStrip("#dayStrip",state.day,selectMainDay);makeDayStrip("#calendarDayStrip",state.day,selectCalendarDay);makeDayStrip("#libraryDayStrip",state.day,selectLibraryDay);}

  function deliverableRow(d){
    const c=byId(d.content_id)||{}; const p=pillarById(c.pillar_id); const r=reviewState(d.content_id);
    const thumb=`${pathFor(d)}/creative.png`;
    return `<article class="delivery-row" tabindex="0" role="button" data-delivery="${esc(d.delivery_id)}"><div class="delivery-main"><img class="delivery-thumb" loading="lazy" src="${thumb}" alt="پیش‌نمایش" onerror="this.style.visibility='hidden'"><div class="delivery-title"><strong>${esc(d.hook||c.topic||"بدون عنوان")}</strong><small>${esc(c.topic||"")}</small><span class="id-code">${esc(d.content_id)} · ${esc(d.delivery_id)}</span></div></div><span class="channel-badge ${esc(d.channel_id)}">${esc(channelLabel(d.channel_id))} · ${esc(fmtLabel(d.format_id))}</span><span class="pillar-badge" style="border-right:3px solid ${colorFor(c.pillar_id)}">${esc(p.fa)}</span><span class="review-badge ${r}">${r==="approved"?"تأیید مالک":r==="revise"?"نیازمند اصلاح":"در انتظار"}</span><button class="row-arrow" aria-label="جزئیات">‹</button></article>`;
  }
  function filteredDeliveries(){
    return deliveries().filter(d=>(state.day===0||d.planned_day_index===state.day)&&(state.channel==="all"||d.channel_id===state.channel));
  }
  function renderDeliveries(){
    const el=$("#deliveryList"); if(!el)return;
    const rows=filteredDeliveries().slice(0,12);
    el.innerHTML=rows.length?rows.map(deliverableRow).join(""):`<div class="empty-state">برای این فیلتر تحویلی پیدا نشد.</div>`;
    if(deliveries().length>12 && state.day===0 && state.channel==="all") el.insertAdjacentHTML("beforeend",`<button class="text-button show-all" data-view-link="calendar">مشاهدهٔ همهٔ ${deliveries().length} تحویل در تقویم ←</button>`);
  }
  function renderCalendar(){
    const el=$("#calendarBoard"); if(!el)return;
    const channel=$("#calendarChannelFilter")?.value||"all";
    const dayIndices=state.day?[state.day]:[1,2,3,4,5,6,7];
    el.innerHTML=dayIndices.map(i=>{
      const list=deliveries().filter(d=>d.planned_day_index===i&&(channel==="all"||d.channel_id===channel));
      return `<section class="calendar-day"><header class="calendar-day-head"><strong>${DAYS[i-1]}</strong><span>${pad(i)} · ${list.length}</span></header><div class="calendar-stack">${list.map(d=>{const c=byId(d.content_id)||{};return `<article class="calendar-card" tabindex="0" data-delivery="${esc(d.delivery_id)}"><span class="channel-badge ${esc(d.channel_id)}">${esc(channelLabel(d.channel_id))}</span><strong>${esc(c.topic||d.hook||"بدون عنوان")}</strong><small>${esc(fmtLabel(d.format_id))} · ${esc(d.delivery_id)}</small></article>`}).join("")||`<div class="empty-state">بدون تحویل</div>`}</div></section>`;
    }).join("");
    const total=dayIndices.reduce((n,i)=>n+deliveries().filter(d=>d.planned_day_index===i&&(channel==="all"||d.channel_id===channel)).length,0);
    $("#calendarSummary").textContent=`${total} تحویل · زمان‌بندی دستی`;
  }
  function renderLibrary(){
    const el=$("#libraryGrid"); if(!el)return;
    const q=state.query.trim().toLowerCase();
    const cards=(state.plan?.content_items||[]).filter(c=>{
      const ds=deliveriesFor(c.content_id);const hay=[c.topic,c.core_message,c.content_id,c.pillar_id,c.primary_persona_id,...ds.map(d=>d.delivery_id)].join(" ").toLowerCase();
      return (!q||hay.includes(q))&&(state.day===0||ds.some(d=>d.planned_day_index===state.day))&&(state.pillar==="all"||c.pillar_id===state.pillar)&&(state.review==="all"||reviewState(c.content_id)===state.review)&&(state.channel==="all"||ds.some(d=>d.channel_id===state.channel));
    });
    const draftCards=state.drafts.filter(d=>!q||`${d.title} ${d.id} ${d.pillar_id} ${d.persona}`.toLowerCase().includes(q)).map(d=>`<article class="content-card" data-intake="${esc(d.id)}"><div class="content-card-cover" style="background:linear-gradient(135deg,#12233e,#253954)"><span class="pillar-color" style="background:${colorFor(d.pillar_id)}"></span><div class="cover-intake">IDEA INTAKE · LOCAL</div></div><div class="content-card-body"><div class="content-card-meta"><span class="pillar-badge">${esc(pillarById(d.pillar_id).fa)}</span><span class="review-badge pending">ایدهٔ تازه</span></div><h3>${esc(d.title)}</h3><p>${esc(d.core_message)}</p><div class="content-card-footer"><span>${esc(d.persona)}</span><span>${esc(d.id)}</span></div></div></article>`);
    el.innerHTML=cards.map(c=>{
      const ds=deliveriesFor(c.content_id);const first=ds[0];const p=pillarById(c.pillar_id);const r=reviewState(c.content_id);
      return `<article class="content-card" data-content="${esc(c.content_id)}"><div class="content-card-cover"><img loading="lazy" src="${first?`${pathFor(first)}/creative.png`:""}" alt="پیش‌نمایش محتوا" onerror="this.style.display='none'"><span class="pillar-color" style="background:${colorFor(c.pillar_id)}"></span></div><div class="content-card-body"><div class="content-card-meta"><span class="pillar-badge">${esc(p.fa||p.title)}</span><span class="review-badge ${r}">${r==="approved"?"تأیید":"بازبینی"}</span></div><h3>${esc(c.topic)}</h3><p>${esc(c.core_message)}</p><div class="content-card-footer"><span>${ds.length} تحویل · ${esc(c.primary_persona_id)}</span><span>${esc(c.content_id)}</span></div></div></article>`;
    }).join("")+draftCards.join("")||`<div class="empty-filter">با این جست‌وجو نتیجه‌ای پیدا نشد.</div>`;
  }
  function renderMetrics(){
    const p=state.plan; if(!p)return;
    $("#metricContents").textContent=p.content_items.length;
    $("#metricDeliveries").textContent=p.deliveries.length;
    $("#metricAssets").textContent=p.assets.length;
    const approved=(p.content_items||[]).filter(c=>reviewState(c.content_id)==="approved").length;
    const percent=p.content_items.length?Math.round(approved/p.content_items.length*100):0;
    $("#metricApproved").textContent=`${percent}٪`;
    $("#approvalProgress").style.width=`${percent}%`;
    $("#reviewCountLabel").textContent=`${p.content_items.length-approved} پرونده منتظر تصمیم`;
    const channelList=Object.entries(p.computed_summary?.deliveries_by_channel||{}).map(([k,v])=>`${channelLabel(k)} ${v}`).join(" · ");
    $("#metricChannels").textContent=channelList;
  }
  function renderAlert(){
    const p=state.plan;const declared=p?.computed_summary||{};const sourceCounts=p?.source_delivery_counts||{};
    const sourceN=sourceCounts.total??declared.source_delivery_count??null;
    const mismatch=sourceN!==null&&Number(sourceN)!==p.deliveries.length;
    const el=$("#validationAlert");
    if(mismatch){el.hidden=false;$("#validationText").textContent=`${p.deliveries.length} تحویل در فهرست، در برابر ${sourceN} در شمارندهٔ برنامهٔ اولیه؛ اختلاف ${Math.abs(p.deliveries.length-sourceN)} مورد. تأیید یا تطبیق لازم است.`;}
    else if(p?.notes?.some(n=>n.includes("اختلاف"))){el.hidden=false;$("#validationText").textContent=p.notes.find(n=>n.includes("اختلاف"));}
  }
  function renderPillarOptions(){
    const ps=state.system?.content_pillars||[];
    $("#pillarFilter").innerHTML=`<option value="all">همهٔ ستون‌ها</option>`+ps.map(p=>`<option value="${esc(p.id)}">${esc(p.fa||p.title)}</option>`).join("");
    $("#draftPillar").innerHTML=ps.map(p=>`<option value="${esc(p.id)}">${esc(p.fa||p.title)}</option>`).join("");
  }
  function renderRecipes(){
    const recipes=state.recipes;$("#recipeCount").textContent=`${recipes.length} رسپی مستقل`;
    const icons={type:"T",transition:"↝",data:"▥",anatomy:"◈",diagram:"⌘","brand-motion":"↗",editorial:"✳",cta:"→"};
    $("#recipeGrid").innerHTML=recipes.map(r=>`<article class="recipe-card"><span class="recipe-symbol">${icons[r.category]||"✦"}</span><strong>${esc(r.label_fa)}</strong><small>${esc(r.parameters.slice(0,3).join(" · "))}</small><em>${esc(r.id)} · ${r.duration_seconds}s</em></article>`).join("");
  }
  function renderBrand(){
    const t=state.tokens;const s=state.system;const c=t?.color||{};const colors=[
      ["سرمه‌ای",c.strategic_navy?.hex||"#0A1931"],["طلایی",c.innovation_gold?.hex||"#FFB400"],["Blog",s?.colors?.section_accents?.blog||"#C05746"],["Tools",s?.colors?.section_accents?.tools||"#0F766E"],["Book",s?.colors?.section_accents?.book||"#3B5998"],["PB",s?.colors?.section_accents?.pb||"#5D5FEF"]];
    $("#brandOverview").innerHTML=`<article class="brand-card brand-lockup-large"><img src="/logo/primary/white/horizontal.svg" alt="AtoZ logo reverse"></article><article class="brand-card"><h3>نام و قاعدهٔ ثابت</h3><p>نشان مرجع AZ دست‌نخورده می‌ماند. عنوان و متن‌های محتوا قالب‌پذیرند؛ هندسهٔ لوگو، نسبت‌ها و تایپوگرافی اصلی قابل‌تغییر نیستند.</p><div class="swatch-row">${colors.map(x=>`<div class="swatch"><i style="background:${esc(x[1])}"></i><small>${esc(x[0])} · ${esc(x[1])}</small></div>`).join("")}</div></article>`;
  }
  function renderMotion(){
    const video=$("#motionFeature .motion-player");
    const src=`${state.out}/motion-lab/break-even-anatomy.mp4`;
    video.innerHTML=`<video controls playsinline preload="metadata" poster="${state.out}/motion-lab/poster.png"><source src="${src}" type="video/mp4">مرورگر شما ویدیو را پشتیبانی نمی‌کند.</video>`;
  }
  function renderAll(){renderMetrics();renderAlert();renderDayStrips();renderDeliveries();renderCalendar();renderPillarOptions();renderLibrary();renderRecipes();renderBrand();renderMotion();}

  function openDetail(deliveryId){
    const d=deliveries().find(x=>x.delivery_id===deliveryId);if(!d)return;
    state.selectedDelivery=d;
    const c=byId(d.content_id)||{};const p=pillarById(c.pillar_id);const base=pathFor(d);const r=reviewState(c.content_id);
    const isReel=["micro_reel","mini_reel","main_reel","animated_reel"].includes(d.format_id);
    const preview=isReel&&d.has_video?`<video controls playsinline preload="metadata"><source src="${base}/reel.mp4" type="video/mp4"></video>`:`<img src="${base}/creative.png" alt="${esc(c.topic)}" onerror="this.src='${base}/creative.svg'">`;
    $("#detailContent").innerHTML=`<div class="detail-layout"><div class="detail-preview">${preview}</div><div class="detail-info"><span class="eyebrow small">${esc(d.content_id)} · ${esc(d.delivery_id)}</span><h2>${esc(c.topic||d.hook)}</h2><p>${esc(c.audience_problem||"")}</p><div class="detail-meta"><span class="channel-badge ${esc(d.channel_id)}">${esc(channelLabel(d.channel_id))} · ${esc(fmtLabel(d.format_id))}</span><span class="pillar-badge" style="border-right:3px solid ${colorFor(c.pillar_id)}">${esc(p.fa)}</span><span class="review-badge ${r}">${r==="approved"?"تأیید مالک":r==="revise"?"نیازمند اصلاح":"در انتظار بازبینی"}</span></div><section class="detail-section"><h3>قلاب</h3><p>${esc(d.hook)}</p></section><section class="detail-section"><h3>کپشن</h3><p id="detailCaption">${esc(d.caption)}</p></section><section class="detail-section"><h3>پیام محوری · ${esc(c.evidence_level||"سطح شواهد ثبت نشده")}</h3><p>${esc(c.core_message)}</p></section><section class="detail-section"><h3>CTA و مقصد</h3><p>${esc(d.cta?.label||"مقصد نهایی با تأیید مالک تعیین شود")}${d.cta?.target_url?`\n${esc(d.cta.target_url)}`:"\nنشانی تأییدنشده؛ جایگزینی پیش از انتشار لازم است."}</p></section><div class="detail-actions"><button class="small-action" data-copy="caption">کپی کپشن</button><button class="small-action" data-copy="hashtags">کپی هشتگ</button><a class="small-action" href="${base}/creative.svg" download>دریافت SVG</a><a class="small-action" href="${base}/creative.png" download>دریافت PNG</a>${d.has_video?`<a class="small-action" href="${base}/reel.mp4" download>دریافت MP4</a>`:""}</div><div class="review-controls"><label>یادداشت بازبینی<textarea id="reviewNote" rows="2" placeholder="منبع، اصلاح یا شرط تأیید را بنویسید…">${esc(state.reviews[c.content_id]?.note||"")}</textarea></label><div class="review-buttons"><button class="approve-button" data-review="approved" data-content="${esc(c.content_id)}">ثبت تأیید مالک</button><button class="revise-button" data-review="revise" data-content="${esc(c.content_id)}">نیازمند اصلاح</button><button class="pending-button" data-review="pending" data-content="${esc(c.content_id)}">پاک‌کردن تصمیم</button></div></div><p class="detail-footnote">ثبت تصمیم فقط در این workspace محلی ذخیره می‌شود؛ هیچ پلتفرمی فراخوانی یا منتشر نمی‌شود.</p></div></div>`;
    $("#detailDialog").showModal();
  }
  function renderDraftPreview(d){
    const f=d.format_id==="carousel"?d.slides.map((s,i)=>`${i+1}. ${typeof s==="string"?s:`${s.title}\n${s.body}`}`).join("\n\n"):d.caption;
    $("#generatedPreview").hidden=false;
    $("#generatedPreview").textContent=`${d.title}\n\n${d.caption}\n\n${d.evidence_note}\n\n${d.format_id==="carousel"?"طرح اسلایدها:\n"+f:"قالب: "+d.format_id}`;
  }
  async function load(){
    try{
      const data=await fetchJSON("/api/bootstrap");
      state.plan=data.plan;state.reviews=data.review_state||{};state.drafts=data.intake_drafts||[];state.recipes=data.recipes||[];state.system=data.design_system;state.tokens=data.tokens;state.out=data.output_base||"/content-output/week-01";
      renderAll();
    }catch(err){$("#deliveryList").innerHTML=`<div class="empty-state">بارگذاری برنامه ناموفق بود: ${esc(err.message)}<br>مطمئن شوید تولید هفته انجام شده و سرور Content Studio اجراست.</div>`;toast(err.message);}
  }

  document.addEventListener("click",async e=>{
    const nav=e.target.closest("[data-view]");if(nav){setView(nav.dataset.view);return;}
    const viewLink=e.target.closest("[data-view-link]");if(viewLink){e.preventDefault();setView(viewLink.dataset.viewLink);return;}
    const row=e.target.closest("[data-delivery]");if(row){openDetail(row.dataset.delivery);return;}
    const card=e.target.closest("[data-content]");if(card){const d=deliveriesFor(card.dataset.content)[0];if(d)openDetail(d.delivery_id);return;}
    const copy=e.target.closest("[data-copy]");if(copy){const d=state.selectedDelivery;const text=copy.dataset.copy==="caption"?d?.caption:(d?.hashtags||[]).join(" ");try{await navigator.clipboard.writeText(text||"");toast("متن در کلیپ‌بورد کپی شد.");}catch{toast("دسترسی به کلیپ‌بورد مرورگر مجاز نیست.");}return;}
    const review=e.target.closest("[data-review]");if(review){const id=review.dataset.content;try{const result=await fetchJSON("/api/review",{method:"POST",body:JSON.stringify({content_id:id,status:review.dataset.review,note:$("#reviewNote")?.value||""})});state.reviews=result.review_state;renderAll();toast("وضعیت بازبینی محلی ذخیره شد.");openDetail(state.selectedDelivery.delivery_id);}catch(err){toast(err.message);}return;}
    const intake=e.target.closest("[data-intake]");if(intake){const d=state.drafts.find(x=>x.id===intake.dataset.intake);if(d)renderDraftPreview(d);return;}
    const refresh=e.target.closest("#refreshBtn");if(refresh){await load();toast("دادهٔ برنامه تازه شد.");}
  });
  document.addEventListener("keydown",e=>{const row=e.target.closest?.("[data-delivery]");if(row&&(e.key==="Enter"||e.key===" ")){e.preventDefault();openDetail(row.dataset.delivery);}});
  $("#channelFilter").addEventListener("change",e=>{state.channel=e.target.value;$("#calendarChannelFilter").value=state.channel;$("#libraryChannelFilter").value=state.channel;renderDeliveries();renderCalendar();renderLibrary();});
  $("#calendarChannelFilter").addEventListener("change",renderCalendar);
  $("#calendarDayStrip").addEventListener("click",e=>{const b=e.target.closest("[data-day]");if(b)selectCalendarDay(Number(b.dataset.day));});
  $("#dayStrip").addEventListener("click",e=>{const b=e.target.closest("[data-day]");if(b)selectMainDay(Number(b.dataset.day));});
  $("#libraryDayStrip").addEventListener("click",e=>{const b=e.target.closest("[data-day]");if(b)selectLibraryDay(Number(b.dataset.day));});
  $("#pillarFilter").addEventListener("change",e=>{state.pillar=e.target.value;renderLibrary();});
  $("#libraryChannelFilter").addEventListener("change",e=>{state.channel=e.target.value;$("#channelFilter").value=state.channel;renderDeliveries();renderLibrary();});
  $("#reviewFilter").addEventListener("change",e=>{state.review=e.target.value;renderLibrary();});
  $("#searchInput").addEventListener("input",e=>{state.query=e.target.value;renderLibrary();});
  $("#viewToggle").addEventListener("click",()=>{state.compact=!state.compact;$("#deliveryList").classList.toggle("compact",state.compact);toast(state.compact?"نمای فشرده فعال شد.":"نمای فهرستی فعال شد.");});
  $("#mobileMenu").addEventListener("click",()=>$("#sidebar").classList.toggle("open"));
  $("#newDraftBtn").addEventListener("click",()=>$("#draftDialog").showModal());
  $("#closeDraft").addEventListener("click",()=>$("#draftDialog").close());
  $("#previewDraft").addEventListener("click",async()=>{
    const values=Object.fromEntries(new FormData($("#draftForm")).entries());
    try{const d=await fetchJSON("/api/draft/preview",{method:"POST",body:JSON.stringify(values)});renderDraftPreview(d);}catch(err){toast(err.message);}
  });
  $("#draftForm").addEventListener("submit",async e=>{
    e.preventDefault();const values=Object.fromEntries(new FormData(e.currentTarget).entries());
    try{const d=await fetchJSON("/api/draft",{method:"POST",body:JSON.stringify(values)});state.drafts.unshift(d.draft);$("#draftDialog").close();e.currentTarget.reset();$("#generatedPreview").hidden=true;renderLibrary();setView("library");toast(`ایدهٔ ${d.draft.id} در صف محلی ذخیره شد.`);}catch(err){toast(err.message);}
  });
  $("#detailDialog").addEventListener("click",e=>{if(e.target===$("#detailDialog"))$("#detailDialog").close();});
  $("#draftDialog").addEventListener("click",e=>{if(e.target===$("#draftDialog"))$("#draftDialog").close();});
  load();
})();
