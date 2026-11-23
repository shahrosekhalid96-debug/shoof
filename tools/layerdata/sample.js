/* Shoof layer-data generator (browser side). Injected into the editor by tools/layerdata/gen.py.
   window.LD_sample(seed, opts) builds one random design with Shoof's own engine and returns the flat picture plus every
   layer as an exact RGBA picture, in paint order (bottom first), with metadata (type, box, and for text: words, font,
   size, weight, alignment, colour, spacing). A drop shadow / glow is its own layer, just under the item that casts it.
   All content is Shoof's own (templates, from-scratch layouts, icons, shapes, patterns) + OFL fonts + photos passed in
   by the driver (CC0) or drawn procedurally here. Nothing is fetched from the internet. */
(function(){
const WORDS=('summer sale grand opening coffee fresh bakery studio launch event night market festival design weekly special offer limited time join team hiring now free delivery book today new menu workshop live music art gallery fitness club yoga class open house tech summit welcome home happy birthday thank you best seller flash deal season collection craft local brand story future dream create bold simple modern classic premium natural organic garden kitchen travel explore city beach mountain sunrise sunset weekend friday saturday sunday january march may july september november 2026 50% 30% $19 $49 9am 7pm call visit shop learn more sign up').split(' ');
const rng=s=>()=>{s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};
const pick=(r,a)=>a[Math.floor(r()*a.length)];
const hex=(r,dark)=>{const h=r()*360,s=40+r()*55,l=dark?10+r()*25:40+r()*50;return hsl(h,s,l);};
function hsl(h,s,l){s/=100;l/=100;const k=n=>(n+h/30)%12,a=s*Math.min(l,1-l),f=n=>l-a*Math.max(-1,Math.min(k(n)-3,9-k(n),1));return '#'+[f(0),f(8),f(4)].map(x=>Math.round(x*255).toString(16).padStart(2,'0')).join('');}
const LATIN=/^[\x00-ɏ -⁯\s]*$/;

/* a photo-like picture when no real photos were passed in: sky/ground gradient, soft blobs, grain, a few hard shapes */
function fakePhoto(r,w,h){const c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');
 const gr=g.createLinearGradient(0,0,r()*w,h);gr.addColorStop(0,hex(r));gr.addColorStop(1,hex(r,r()<.5));g.fillStyle=gr;g.fillRect(0,0,w,h);
 for(let i=0,n=3+r()*8;i<n;i++){const x=r()*w,y=r()*h,rad=(.1+r()*.5)*Math.max(w,h),rg=g.createRadialGradient(x,y,0,x,y,rad);rg.addColorStop(0,hex(r)+'cc');rg.addColorStop(1,'#00000000');g.fillStyle=rg;g.fillRect(0,0,w,h);}
 for(let i=0,n=r()*6;i<n;i++){g.fillStyle=hex(r,r()<.4);g.globalAlpha=.6+r()*.4;g.beginPath();if(r()<.5)g.ellipse(r()*w,r()*h,10+r()*w/4,10+r()*h/4,r()*3,0,7);else g.rect(r()*w,r()*h,10+r()*w/3,10+r()*h/3);g.fill();}
 g.globalAlpha=1;const im=g.getImageData(0,0,w,h),d=im.data;for(let i=0;i<d.length;i+=4){const n=(r()-.5)*24;d[i]+=n;d[i+1]+=n;d[i+2]+=n;}g.putImageData(im,0,0);
 return c.toDataURL('image/jpeg',.9);}

async function preload(src){return new Promise(res=>{const im=getImg(src,()=>res());if(im)res();setTimeout(res,4000);});}
const typeOf=e=>e.role==='bg'?'bg':e.type==='text'?'text':e.type==='image'?(e.role==='logo'?'logo':'image'):e.type==='icon'?'icon':e.type==='pattern'?'pattern':(e.type==='qr'||e.type==='chart')?'graphic':'shape';

function renderEls(els,d,S,bg){const sc=S/Math.max(d.width,d.height),W=Math.round(d.width*sc),H=Math.round(d.height*sc),div=document.createElement('div'),
 st=new Konva.Stage({container:div,width:W,height:H,scale:{x:sc,y:sc}}),l=new Konva.Layer();st.add(l);
 if(bg)l.add(new Konva.Rect({width:d.width,height:d.height,fill:bg}));els.forEach(e=>{try{l.add(buildNode(e));}catch(_){}});l.draw();
 const cv=l.getCanvas()._canvas,ctx=cv.getContext('2d'),pr=cv.width/W;let id;
 if(pr===1)id=ctx.getImageData(0,0,W,H);else{const t=document.createElement('canvas');t.width=W;t.height=H;t.getContext('2d').drawImage(cv,0,0,W,H);id=t.getContext('2d').getImageData(0,0,W,H);}
 st.destroy();return id;}
function toURL(id){const c=document.createElement('canvas');c.width=id.width;c.height=id.height;c.getContext('2d').putImageData(id,0,0);return c.toDataURL('image/png');}
function bbox(id){const {width:W,height:H,data:a}=id;let x0=W,y0=H,x1=-1,y1=-1,n=0;for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(a[(y*W+x)*4+3]>8){n++;if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y;}return n?{x:x0,y:y0,w:x1-x0+1,h:y1-y0+1,px:n}:null;}

/* pick and randomise one design */
const AR=/[\u0600-\u06ff]/;let TPL_OK=null;
async function source(r,opts){
 if(!TPL_OK)TPL_OK=Object.keys(TEMPLATES).filter(k=>{try{return !AR.test(JSON.stringify(TEMPLATES[k].make()));}catch(_){return false;}});
 if(r()<.5){const t=TEMPLATES[pick(r,TPL_OK)];let d=sanitizeDoc(JSON.parse(JSON.stringify(t.make())));if(d.pages.length>1)d.page=Math.floor(r()*d.pages.length);return {d,src:'tpl'};}
 const phrase=pick(r,['summer sale 30% off this weekend','grand opening of our coffee shop on friday','we are hiring designers join the team','yoga class every sunday 9am','tech summit 2026 speakers and workshops','fresh bakery new menu','live music night at the garden','flash deal on all shoes']);
 try{const b=dgBrief(phrase),lays=Object.keys(DG_LAYOUTS),st=pick(r,DKB.styles);const fmt=pick(r,[[1080,1080],[1080,1350],[1080,1920],[1200,630]]);
  b.format=pick(r,['ig','ig','story','li','a4','flyer','yt']);let d=await dgBuild(b,pick(r,lays),st,r()<.5?st.palette:pick(r,DKB.palettes),Math.floor(r()*1e6));if(d&&d.pages)return {d:sanitizeDoc(JSON.parse(JSON.stringify(d))),src:'dg'};}catch(_){}
 return source(()=>0.1,opts);}

window.LD_sample=async function(seed,opts={}){
 const r=rng(Math.imul(seed+1,2654435761)^0x5bd1e995),S=opts.size||512,photos=opts.photos||[];for(let i=0;i<3;i++)r();let {d,src}=await source(r,opts);d=hydrate(d);
 const pg=d.pages[d.page||0],fonts=FONTS.filter(f=>!AR_FONTS.includes(f));
 const photo=()=>photos.length&&r()<.85?pick(r,photos):fakePhoto(r,512+Math.floor(r()*512),512+Math.floor(r()*512));
 for(const e of pg.elements){
  if(e.type==='placeholder'){e.type='image';e.src=photo();e.fit='cover';}
  else if(e.type==='image'&&r()<.6&&e.role!=='logo')e.src=photo();
  if(e.type==='text'&&LATIN.test(e.text||'')){
   if(r()<.6){const L0=(e.text||'').length;let s='';for(let k=0;k<40&&s.length<L0*.85;k++)s+=(s?' ':'')+pick(r,WORDS);if(s.length>L0*1.25&&s.includes(' '))s=s.slice(0,s.lastIndexOf(' '));if(/\n/.test(e.text||'')&&s.includes(' ')){const mid=s.indexOf(' ',Math.floor(s.length/2));if(mid>0)s=s.slice(0,mid)+'\n'+s.slice(mid+1);}if((e.text||'')===(e.text||'').toUpperCase())s=s.toUpperCase();else if(r()<.3)s=s[0].toUpperCase()+s.slice(1);e.text=s;}
   if(r()<.45)e.fontFamily=pick(r,fonts);if(r()<.2)e.align=pick(r,['left','center','right']);if(r()<.15)e.bold=!e.bold;
  }
  if(e.role!=='bg'&&['text','image','icon','rect','ellipse','star','path','blob','hexagon','triangle'].includes(e.type)&&!e.shadowColor&&r()<.22){
   const glow=r()<.35;e.shadowColor=glow?hex(r):pick(r,['#000000','#1a1a2e','#3b1d00']);e.shadowBlur=Math.round(glow?8+r()*40:r()*30);
   e.shadowX=glow?0:Math.round((r()-.3)*30);e.shadowY=glow?0:Math.round(r()*30);e.shadowOpacity=glow?.9:.25+r()*.5;}
 }
 await Promise.all([...new Set(pg.elements.filter(e=>e.type==='text').map(e=>e.fontFamily))].map(f=>loadFont(f).catch(()=>{})));
 try{await document.fonts.ready;}catch(_){}
 await Promise.all(pg.elements.filter(e=>e.src).map(e=>preload(e.src)));
 const bgc=pg.background.color||'#ffffff',sc=S/Math.max(d.width,d.height),layers=[];
 const meta=e=>{const m={id:e.id,type:typeOf(e),el:e.type};if(e.type==='text')Object.assign(m,{text:e.text,font:e.fontFamily,size:Math.round(e.fontSize*sc*10)/10,bold:!!e.bold,italic:!!e.italic,align:e.align||'left',fill:e.fill||null,gradient:!!e.fillGradient,letterSpacing:e.letterSpacing||0,lineHeight:e.lineHeight||1.2,curve:e.curve||0,rotation:e.rotation||0});
  if(e.shadowColor)m.shadow={color:e.shadowColor,blur:Math.round((e.shadowBlur||0)*sc*10)/10,x:Math.round((e.shadowX||0)*sc*10)/10,y:Math.round((e.shadowY||0)*sc*10)/10,opacity:e.shadowOpacity};if(e.groupId)m.group=e.groupId;return m;};
 /* background = page colour + bg block (or the page colour alone) */
 const bgEl=pg.elements.find(e=>e.role==='bg');const bgId=renderEls(bgEl?[bgEl]:[],d,S,bgc);layers.push({png:toURL(bgId),meta:{type:'bg',fill:bgEl?(bgEl.fill||null):bgc}});
 for(const e of pg.elements){if(e===bgEl||e.hidden)continue;
  const A=renderEls([e],d,S,null);if(!bbox(A))continue;
  if(e.shadowColor){const e2=Object.assign({},e,{shadowColor:null});const B=renderEls([e2],d,S,null),sh=new ImageData(A.width,A.height),a=A.data,b=B.data,s=sh.data;
   for(let i=0;i<a.length;i+=4){const ab=b[i+3]/255,k=1-ab;s[i]=a[i];s[i+1]=a[i+1];s[i+2]=a[i+2];s[i+3]=Math.round(a[i+3]*k);}
   const sb=bbox(sh);if(sb&&sb.px>20)layers.push({png:toURL(sh),meta:{type:'shadow',of:e.id,box:sb,color:e.shadowColor}});
   const bb=bbox(B);if(bb)layers.push({png:toURL(B),meta:Object.assign(meta(e),{box:bb})});}
  else layers.push({png:toURL(A),meta:Object.assign(meta(e),{box:bbox(A)})});}
 const comp=renderEls(pg.elements.filter(e=>!e.hidden),d,S,bgc);
 return {seed,src,w:comp.width,h:comp.height,composite:toURL(comp),layers};
};
})();
