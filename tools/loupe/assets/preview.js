'use strict';
const $ = id => document.getElementById(id);
const node = (tag, text, cls) => {const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const original=$('original'), rendered=$('rendered');
let snapshot, selected='', busy=false, loading=false, mediaReady=false, refreshPending=false;
let looping=false, scrubbing=false, resumeAfterSeek=false, sentencePlayback=false;
const icons={
  check:'<path d="m5 12 4 4L19 6"/>',
  spinner:'<path d="M20 12a8 8 0 1 1-8-8"/>',
  play:'<path d="m9 5 11 7-11 7Z" fill="currentColor" stroke="none"/>',
  pause:'<path d="M8 5v14M16 5v14" stroke-width="4"/>',
  restart:'<path d="M4 10a8 8 0 1 1 1 7M4 4v6h6"/>',
  frameBack:'<path d="M5 5v14m14-14-9 7 9 7Z"/>',
  frameForward:'<path d="M19 5v14M5 5l9 7-9 7Z"/>',
  previous:'<path d="m15 5-7 7 7 7"/>',next:'<path d="m9 5 7 7-7 7"/>',
  fullscreen:'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/>',
  exitFullscreen:'<path d="M3 8h5V3m13 5h-5V3M8 21v-5H3m13 5v-5h5"/>',
  pair:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/>',
  stack:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 12h18"/>',
  wipe:'<path d="M12 2v20M8 5H3v14h5m8-14h5v14h-5"/>',
  search:'<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
  loop:'<path d="m17 2 4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4m14-1v2a3 3 0 0 1-3 3H3"/>'
};
function icon(element,name){element.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${icons[name]}</svg>`;}
for(const element of document.querySelectorAll('[data-icon]'))icon(element,element.dataset.icon);
const tooltip=node('div',undefined,'control-tooltip');tooltip.id='controlTooltip';tooltip.role='tooltip';tooltip.hidden=true;
let tooltipTarget;
function hideTooltip(){tooltip.hidden=true;tooltipTarget?.removeAttribute('aria-describedby');tooltipTarget=undefined;}
function showTooltip(target){
  if(!target)return;
  hideTooltip();tooltipTarget=target;tooltip.textContent=target.dataset.tooltip;
  (document.fullscreenElement||document.body).append(tooltip);tooltip.hidden=false;
  target.setAttribute('aria-describedby',tooltip.id);
  const rect=target.getBoundingClientRect(),box=tooltip.getBoundingClientRect();
  tooltip.style.left=Math.max(8,Math.min(innerWidth-box.width-8,rect.left+(rect.width-box.width)/2))+'px';
  tooltip.style.top=(rect.top>=box.height+12?rect.top-box.height-8:rect.bottom+8)+'px';
}
document.addEventListener('pointerover',e=>{if(e.pointerType!=='touch'){const target=e.target.closest('[data-tooltip]');if(target!==tooltipTarget)showTooltip(target);}});
document.addEventListener('pointerout',e=>{if(tooltipTarget&&!tooltipTarget.contains(e.relatedTarget))hideTooltip();});
document.addEventListener('focusin',e=>showTooltip(e.target.closest('[data-tooltip]')));
document.addEventListener('focusout',hideTooltip);
document.addEventListener('pointerdown',hideTooltip);
document.addEventListener('keydown',e=>{if(e.key==='Escape')hideTooltip();});
document.addEventListener('scroll',hideTooltip,true);window.addEventListener('resize',hideTooltip);
function controlHint(id,label,shortcut=''){const control=$(id);control.setAttribute('aria-label',label);control.dataset.tooltip=label+shortcut;if(tooltipTarget===control)showTooltip(control);}
function playState(){const playing=!original.paused;icon($('play'),playing?'pause':'play');controlHint('play',playing?'暂停':'播放','（空格 / K）');}
function loopState(value){looping=value;$('loop').setAttribute('aria-pressed',String(value));controlHint('loop',value?'取消循环此句':'循环此句');}
function formatTime(seconds){const value=Math.max(0,Math.floor(seconds)),hours=Math.floor(value/3600),minutes=Math.floor(value/60)%60;return (hours?hours+':':'')+String(minutes).padStart(2,'0')+':'+String(value%60).padStart(2,'0');}
function webURL(value){try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)?url.href:undefined;}catch{return undefined;}}
function drawVideoMetadata(next){
  const video=next.content.video||{},media=next.media.original,cards=[];
  function card(label,value,detail,url){
    if(!value)return;
    const item=node('div',undefined,'video-meta-card'),content=node('dd');
    const link=webURL(url);
    if(link){const a=node('a',value);a.href=link;a.target='_blank';a.rel='noopener noreferrer';content.append(a);}else content.append(node('span',value));
    if(detail)content.append(node('small',detail));
    item.append(node('dt',label),content);cards.push(item);
  }
  card('作者',video.channel,undefined,video.channel_url);
  card('发布日期',video.published);
  card('时长',formatTime(Math.round(media.duration)));
  card('原片画质',`${media.width} × ${media.height}`,`${Number(media.fps.toFixed(3))} fps · 平均帧率`);
  card('原视频',video.url?'观看原片 ↗':undefined,undefined,video.url);
  $('videoMetadata').replaceChildren(...cards);
  const thumbnail=webURL(video.thumbnail),cover=$('videoCoverLink');
  cover.hidden=!thumbnail;
  if(thumbnail){$('videoCover').style.aspectRatio=media.display_ratio;$('videoCover').src=thumbnail;$('videoCover').alt=`${next.title} · 原视频封面`;cover.href=webURL(video.url)||thumbnail;}else{$('videoCover').removeAttribute('src');cover.removeAttribute('href');}
  $('videoDescription').hidden=!video.description;
  $('videoDescription').querySelector('p').textContent=video.description||'';
}
function playerAvailable(available){mediaReady=available;for(const id of ['play','back','forward','seek'])$(id).disabled=!available;}
playerAvailable(false);
const labels=()=>({original:'原片',rendered:'当前版',source_text:'原文',text:'译文',...snapshot?.labels});
const selectedEvent=()=>snapshot?.timeline.find(e=>e.id===selected);
const duration=()=>Math.min(snapshot.media.original.duration,snapshot.media.rendered.duration);
async function json(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error(`读取失败 (${r.status})`);return r.json();}
function playerStatus(message='',pending=false){$('playerStatus').textContent=message;$('playerStatus').hidden=!message;$('playerStatus').classList.toggle('loading-status',pending);}
function pause(){sentencePlayback=false;original.pause();rendered.pause();playState();}
function seek(t){if(!snapshot)return;t=Math.max(0,Math.min(t,duration()));original.currentTime=t;rendered.currentTime=t;updateTime();}
function updateTime(){if(!snapshot)return;const time=original.currentTime,total=duration();$('seek').value=time;$('seek').style.setProperty('--progress',`${total?time/total*100:0}%`);$('seek').setAttribute('aria-valuetext',`${formatTime(time)} / ${formatTime(total)}`);$('time').textContent=`${formatTime(time)} / ${formatTime(total)}`;$('time').title=`${time.toFixed(3)} / ${total.toFixed(3)} 秒`;}
async function play(){if(!snapshot||loading||!mediaReady)return;try{await Promise.all([original.play(),rendered.play()]);playState();playerStatus();}catch(error){pause();playerStatus('播放失败：'+error.message);}}
function jump(id){
  const e=snapshot?.timeline.find(row=>row.id===id);if(!e||loading||!mediaReady)return;
  selected=id;pause();seek(e.start);detail();drawNavigation();if(looping)replay();
}
function replay(){const e=selectedEvent();if(!e||loading||!mediaReady)return;pause();seek(e.start);sentencePlayback=true;play();}
function drawNavigation(events=filtered()){
  const index=events.findIndex(e=>e.id===selected),options=events.map(e=>{const text=Array.from((e.text||e.source_text||'').replace(/\s+/g,' ').trim());return new Option(text.slice(0,18).join('')+(text.length>18?'…':''),e.id);});
  if(index<0){const placeholder=new Option(events.length?'选择结果':'没有匹配字幕','');placeholder.disabled=true;options.unshift(placeholder);}
  $('event').replaceChildren(...options);$('event').value=index<0?'':selected;$('event').disabled=!events.length||!mediaReady;
  $('previous').disabled=!mediaReady||index<=0;$('next').disabled=!mediaReady||!events.length||index===events.length-1;
  $('replay').disabled=$('loop').disabled=!mediaReady||!selectedEvent();
}
function detail(){
  const e=selectedEvent(),l=labels();$('current').replaceChildren();
  if(!e){$('current').append(node('p','没有匹配的字幕','muted'));return;}
  const meta=node('div',undefined,'caption-meta');meta.append(node('span','所选字幕'),node('strong',e.id),node('span',`${e.start.toFixed(3)} — ${e.end.toFixed(3)} s`));
  const text=node('div',undefined,'caption-text');
  for(const [label,value] of [[l.source_text,e.source_text],[l.text,e.text]]){const row=node('div',undefined,'caption-row');row.append(node('span',label,'caption-language'),node('p',value));text.append(row);}
  $('current').append(meta,text);
}
function filtered(){const q=$('search').value.trim().toLowerCase(),role=$('role').value,focus=new Set(snapshot.content.focus_ids||[]);return snapshot.timeline.filter(e=>(!q||[e.id,e.text,e.source_text,e.style.font_role].join(' ').toLowerCase().includes(q))&&(!role||e.style.font_role===role)&&(!$('focus').checked||focus.has(e.id)));}
function preciseTime(seconds){const ms=Math.max(0,Math.round(seconds*1000));return `${formatTime(Math.floor(ms/1000))}.${String(ms%1000).padStart(3,'0')}`;}
function openImage(url,description){const img=$('imageDialog').querySelector('img');img.src=url;img.alt=description;$('imageDialog').showModal();}
function proofFigure(event,frame,side){
  const l=labels(),source=side==='original',figure=node('figure',undefined,'proof-side');
  const heading=node('div',l[side],'proof-side-heading');
  if(frame?.[side]){
    const zoom=node('button',undefined,'proof-image'),img=node('img');
    zoom.type='button';zoom.setAttribute('aria-label',`放大${l[side]}画面 · ${event.id}`);
    img.src=frame[side];img.alt=`${l[side]} · ${event.id} · 取帧 ${preciseTime(frame.time)}`;img.loading='lazy';
    img.width=480;img.height=Math.round(480/snapshot.media[side].display_ratio);img.style.aspectRatio=snapshot.media[side].display_ratio;
    zoom.onclick=()=>openImage(img.src,img.alt);zoom.append(img);figure.append(heading,zoom);
  }else figure.append(heading,node('p','暂无对照画面','proof-unavailable'));
  const caption=node('figcaption',undefined,'proof-caption');
  caption.append(node('span',source?l.source_text:l.text,'proof-language'),node('p',source?event.source_text:event.text));
  figure.append(caption);return figure;
}
function proofCard(event,frame){
  const card=node('article',undefined,'proof'),head=node('header',undefined,'proof-header');
  const identity=node('div',undefined,'proof-identity'),title=node('h3',event.id),timing=node('div',undefined,'proof-timing');
  timing.append(node('span',`字幕 ${preciseTime(event.start)} — ${preciseTime(event.end)}`));
  if(frame)timing.append(node('span',`取帧 ${preciseTime(frame.time)}`));
  identity.append(title,timing);
  const locate=node('button','定位到字幕','proof-locate');locate.type='button';
  locate.setAttribute('aria-label',`定位到字幕 ${event.id}`);
  locate.onclick=()=>{jump(event.id);$('videoPanel').scrollIntoView({behavior:'smooth'});};
  head.append(identity,locate);
  const columns=node('div',undefined,'columns');
  columns.append(proofFigure(event,frame,'original'),proofFigure(event,frame,'rendered'));
  card.append(head,columns);
  if(frame){
    const active=snapshot.timeline.filter(e=>e.id!==event.id&&e.start<=frame.time&&frame.time<e.end);
    if(active.length){
      const overlap=node('div',undefined,'proof-overlap'),list=node('ul',undefined,'proof-active');
      overlap.append(node('h4','同屏其他字幕'));
      for(const item of active){const row=node('li');row.append(node('code',item.id),node('span',item.text));list.append(row);}
      overlap.append(list);card.append(overlap);
    }
  }
  const details=node('details',undefined,'proof-details');
  details.append(node('summary','查看样式参数'),node('pre',JSON.stringify(event.style,null,2)));
  card.append(details);return card;
}
function draw(preservePosition=false){
  const previous=Array.from($('frames').children),expanded=new Set(previous.filter(card=>card.querySelector('details')?.open).map(card=>card.dataset.eventId));
  const anchor=preservePosition?previous.find(card=>{const r=card.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight;}):null;
  const anchorTop=anchor?.getBoundingClientRect().top;
  const events=filtered();drawNavigation();
  $('count').textContent=`${events.length} / ${snapshot.timeline.length}`;$('empty').hidden=!!events.length;
  const frames=new Map(snapshot.frames.map(f=>[f.id,f]));
  const cards=events.map(event=>{const card=proofCard(event,frames.get(event.id));card.dataset.eventId=event.id;if(expanded.has(event.id))card.querySelector('details').open=true;return card;});
  $('frames').replaceChildren(...cards);
  if(anchor){const replacement=cards.find(card=>card.dataset.eventId===anchor.dataset.eventId);if(replacement)window.scrollBy(0,replacement.getBoundingClientRect().top-anchorTop);}
}
function loadVideo(video,url){return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{cleanup();reject(Error('视频载入超时'));},30000);
  const cleanup=()=>{clearTimeout(timer);video.removeEventListener('loadedmetadata',ok);video.removeEventListener('error',bad);};
  const ok=()=>{cleanup();resolve();},bad=()=>{cleanup();reject(Error('视频加载失败'));};
  video.addEventListener('loadedmetadata',ok);video.addEventListener('error',bad);video.src=url;video.load();
});}
async function apply(next){
  const t=original.currentTime,playing=!original.paused;pause();loading=true;playerAvailable(false);playerStatus('正在载入视频…',true);
  try{
    // Reserve each display ratio before assigning sources or waiting for metadata.
    for(const [side,video] of [['original',original],['rendered',rendered]])video.style.setProperty('--video-aspect',next.media[side].display_ratio);
    $('compare').style.setProperty('--aspect',next.media.original.display_ratio);
    const l={...labels(),...next.labels};document.title=next.title;$('title').textContent=next.title;
    drawVideoMetadata(next);
    $('originalLabel').textContent=l.original;$('renderedLabel').textContent=l.rendered;
    $('mediaInfo').textContent=`${next.media.rendered.source} · ${next.media.rendered.width} × ${next.media.rendered.height}`;
    $('mediaInfo').title=`快照 ${new Date(next.generated_at).toLocaleString()} · ${next.timeline.length} 条字幕 · ${next.media.rendered.frame_rate} fps`;
    snapshot=next;window.PREVIEW_SNAPSHOT=next; // Read-only diagnostic state for browser checks.
    $('seek').max=duration();
    const role=$('role').value;$('role').replaceChildren(new Option('全部',''),...[...new Set(next.timeline.map(e=>e.style.font_role).filter(Boolean))].map(r=>new Option(next.content.role_labels?.[r]||r,r)));if([...$('role').options].some(o=>o.value===role))$('role').value=role;
    if(!next.timeline.some(e=>e.id===selected))selected=next.timeline[0]?.id||'';
    detail();draw(true);
    await Promise.all([loadVideo(original,next.media.original.url),loadVideo(rendered,next.media.rendered.url)]);
    playerAvailable(true);drawNavigation();seek(t);original.playbackRate=rendered.playbackRate=+$('rate').value;
    loading=false;playerStatus();if(playing)await play();
  }catch(error){playerStatus('视频载入失败：'+error.message);throw error;}finally{loading=false;}
}
function syncState(state,message=''){
  if(refreshPending)state='building';
  const checking=state==='checking',pending=checking||state==='building',button=$('refresh');
  button.dataset.state=state;button.disabled=pending;
  button.setAttribute('aria-busy',String(pending));
  const indicator=button.querySelector('[data-icon]'),symbol=pending?'spinner':state==='ready'?'check':'restart';
  if(indicator.dataset.icon!==symbol){icon(indicator,symbol);indicator.dataset.icon=symbol;}
  $('syncStatus').textContent=checking?'检查中':pending?'同步中':state==='ready'?'已同步':'重试同步';
  controlHint('refresh',checking?'正在检查输入':pending?'正在同步':state==='ready'?'已同步，重新检查输入':'同步失败，点击重试');
  $('syncMessage').hidden=pending||!message;$('syncMessage').textContent=message;
}
async function sync(){
  if(busy||refreshPending)return;busy=true;
  try{
    const state=await json('status.json');
    if(!snapshot||!mediaReady||state.state==='ready'&&state.revision!==snapshot.revision)await apply(await json('snapshot.json'));
    syncState(state.state,state.state==='ready'||state.state==='building'?'':'同步失败：'+state.message+(snapshot?'。当前显示已有快照。':'。尚未载入可用快照。'));
  }catch(error){syncState('error','同步不可用：'+error.message+(snapshot?'。已有画面可能过期。':'。尚未载入可用快照。'));}
  finally{busy=false;}
}
function togglePlay(){original.paused?play():pause();}
$('play').onclick=togglePlay;
$('replay').onclick=replay;$('event').onchange=()=>jump($('event').value);
$('loop').onclick=()=>{if(!selectedEvent()||loading)return;loopState(!looping);if(looping)replay();};
for(const [id,step] of [['previous',-1],['next',1]])$(id).onclick=()=>{if(!snapshot)return;const rows=filtered(),i=rows.findIndex(e=>e.id===selected);if(rows.length)jump(rows[Math.max(0,Math.min(rows.length-1,i+step))].id);};
for(const [id,step] of [['back',-1],['forward',1]])$(id).onclick=()=>{pause();if(snapshot)seek(original.currentTime+step/snapshot.media.rendered.fps);};
function beginScrub(){if(!scrubbing){resumeAfterSeek=!original.paused;scrubbing=true;}}
function endScrub(){if(!scrubbing)return;scrubbing=false;if(resumeAfterSeek)play();resumeAfterSeek=false;}
$('seek').onpointerdown=beginScrub;
$('seek').onkeydown=e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End','PageUp','PageDown'].includes(e.key))beginScrub();};
$('seek').oninput=()=>{pause();seek(+$('seek').value);};$('seek').onchange=endScrub;
document.addEventListener('pointerup',endScrub);$('seek').onkeyup=endScrub;
$('seek').onpointercancel=endScrub;$('seek').onblur=endScrub;
$('rate').onchange=()=>original.playbackRate=rendered.playbackRate=+$('rate').value;
for(const button of $('layout').querySelectorAll('[data-layout]'))button.onclick=()=>{
  const layout=button.dataset.layout;$('compare').className='compare '+layout;$('playerShell').dataset.layout=layout;$('wipeControl').hidden=layout!=='wipe';
  for(const item of $('layout').querySelectorAll('button'))item.setAttribute('aria-pressed',String(item===button));
};
$('wipe').oninput=()=>$('compare').style.setProperty('--wipe',$('wipe').value+'%');
async function fullscreen(){try{if(document.fullscreenElement=== $('playerShell'))await document.exitFullscreen();else if($('playerShell').requestFullscreen)await $('playerShell').requestFullscreen();else throw Error('当前浏览器不支持全屏');}catch(error){playerStatus('无法切换全屏：'+error.message);}}
$('fullscreen').onclick=fullscreen;
document.addEventListener('fullscreenchange',()=>{hideTooltip();const active=document.fullscreenElement===$('playerShell');icon($('fullscreen'),active?'exitFullscreen':'fullscreen');controlHint('fullscreen',active?'退出全屏':'进入全屏','（F）');});
$('compare').onclick=()=>{togglePlay();$('playerShell').focus({preventScroll:true});};
$('playerShell').addEventListener('keydown',e=>{
  if(e.target.matches('input,select,textarea')||e.target.isContentEditable||e.altKey||e.ctrlKey||e.metaKey)return;
  if(e.target.closest('button')&&(e.key===' '||e.key==='Enter'))return;
  const key=e.key.toLowerCase();
  if(![' ','k','arrowleft','arrowright',',','.','f'].includes(key))return;
  e.preventDefault();
  if(key===' '||key==='k')togglePlay();else if(key==='f')fullscreen();
  else if(snapshot&&!loading){if(key===','||key==='.')$(key===','?'back':'forward').click();else {sentencePlayback=false;seek(original.currentTime+(key==='arrowleft'?-5:5));}}
});
for(const id of ['search','role','focus'])$(id).addEventListener('input',()=>{if(snapshot)draw();});
$('closeImage').onclick=()=>$('imageDialog').close();$('imageDialog').onclick=e=>{if(e.target===$('imageDialog'))$('imageDialog').close();};
$('refresh').onclick=async()=>{
  if(refreshPending)return;
  pause();refreshPending=true;syncState('building');
  try{
    const r=await fetch('/api/rebuild',{method:'POST',headers:{'X-Preview-Rebuild':'1'}}),data=await r.json();
    if(!r.ok)throw Error(data.message);
    refreshPending=false;await sync();
  }catch(error){refreshPending=false;syncState('error','同步失败：'+error.message);}
};
original.addEventListener('ended',pause);rendered.addEventListener('ended',pause);
for(const video of [original,rendered])video.addEventListener('error',()=>{playerStatus('视频加载失败，请检查服务和配置输入。');});
function tick(){
  if(snapshot&&!loading){
    if(!original.paused){const e=selectedEvent();if(looping&&e&&original.currentTime>=e.end)seek(e.start);else if(sentencePlayback&&e&&original.currentTime>=e.end){pause();seek(e.end);}else if(!rendered.seeking&&Math.abs(original.currentTime-rendered.currentTime)>.075)rendered.currentTime=original.currentTime;if(!original.paused&&rendered.paused&&!rendered.ended)rendered.play().catch(()=>{});}
    updateTime();
  }requestAnimationFrame(tick);
}
async function initialize(){
  const embedded=JSON.parse($('initialSnapshot').textContent);
  if(embedded){
    busy=true;
    try{await apply(embedded);}catch(error){syncState('error','视频载入失败：'+error.message);}finally{busy=false;}
  }
  await sync();
}
initialize();setInterval(sync,5000);requestAnimationFrame(tick);document.addEventListener('visibilitychange',()=>{if(!document.hidden)sync();});
