"""把 content.txt 生成为单页 HTML 学习讲义（../index.html）。

用法：python3 build.py
"""
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "content.txt"
OUT = HERE.parent / "index.html"

PARTS = {
    0: ("开场", "Opening"),
    1: ("第一部分 · 临床背景", "Genetics & Rare Disease"),
    2: ("第二部分 · 编码区变异", "AlphaMissense"),
    3: ("第三部分 · 非编码基因组", "AlphaGenome"),
    4: ("第四部分 · 全基因组图谱", "AlphaGenome Atlas & AVI"),
    5: ("结束", "Closing"),
}

DNA = ('<code class="dna">gtatata<span class="win">tcatgatatg<b class="snv">t</b>'
       'atacgcatagat</span>catgagctca</code>')


def parse(text):
    slides, cur = [], None
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("=== "):
            num, part, rest = line[4:].split(" | ", 2)
            en, zh = rest.split(" || ")
            cur = {"n": int(num), "part": int(part), "en": en.strip(),
                   "zh": zh.strip(), "rows": [], "notes": []}
            slides.append(cur)
            continue
        kind, _, body = line.partition(" ")
        orig, _, trans = body.partition(" || ")
        if kind == "n":
            cur["notes"].append((orig.strip(), trans.strip()))
        else:
            cur["rows"].append((kind, orig.strip(), trans.strip()))
    return slides


GLOSSARY = {}


def record(word, gloss, n):
    plain = re.sub(r"<[^>]+>", "", word).strip()
    key = plain.lower()
    disp = plain
    if disp.isupper() and (" " in disp or disp in {"WEIGHTS", "ATLAS"}):
        disp = disp.capitalize()
    if key not in GLOSSARY:
        GLOSSARY[key] = {"en": disp, "zh": gloss, "pages": [n]}
    else:
        g = GLOSSARY[key]
        if n not in g["pages"]:
            g["pages"].append(n)
        if g["en"].isupper() and not disp.isupper():
            g["en"] = disp


def inline(s, n=None, collect=False):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]",
               lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)

    def term(m):
        w, g = m.group(1), m.group(2)
        if collect:
            record(w, g, n)
        return (f'<span class="t" title="{g}"><span class="w">{w}</span>'
                f'<span class="g">{g}</span></span>')

    s = re.sub(r"\{\{([^|{}]+)\|([^{}]+)\}\}", term, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"%%(.+?)%%", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", s)
    s = s.replace("@@DNA@@", DNA)
    return s


def render_slide(sl):
    n = sl["n"]
    pid = f"p{n}"
    part_zh, part_en = PARTS[sl["part"]]
    out = [f'<section class="slide" id="{pid}" aria-labelledby="{pid}-t">']
    out.append('<header class="sh">'
               f'<span class="pg">P.{n:02d}</span>'
               f'<span class="part">{part_zh}</span>'
               f'<h2 id="{pid}-t">{html.escape(sl["zh"])}</h2></header>')
    out.append(f'<figure class="shot"><button type="button" class="zoom" data-src="slides/s-{n:02d}.jpg" '
               f'aria-label="放大查看第 {n} 页幻灯片"><img src="slides/s-{n:02d}.jpg" width="1440" height="810" '
               f'loading="{"eager" if n <= 2 else "lazy"}" decoding="async" alt="第 {n} 页幻灯片原图"></button>'
               f'<figcaption>第 {n} 页原图 · 点击放大</figcaption></figure>')
    rows = sl["rows"]
    if rows:
        out.append('<div class="rows">')
        out.append('<div class="row k-head" aria-hidden="true"><div>原文 · 重点词附中文释义</div><div>译文</div></div>')
        for kind, orig, trans in rows:
            if kind == "fh":
                label = inline(orig, n, True) if orig else ""
                out.append(f'<div class="row k-fh"><span class="fh-tag">图中文字</span>'
                           f'<span class="fh-l">{label}</span></div>')
                continue
            if kind == "d":
                out.append(f'<div class="row k-d">{inline(orig)}</div>')
                continue
            out.append(f'<div class="row k-{kind}"><div class="en" lang="en">{inline(orig, n, True)}</div>'
                       f'<div class="zh" lang="zh-CN">{inline(trans)}</div></div>')
        out.append("</div>")
    if sl["notes"]:
        out.append('<aside class="notes" aria-label="讲解"><h3>讲解</h3><dl>')
        for t, b in sl["notes"]:
            out.append(f"<div><dt>{inline(t)}</dt><dd>{inline(b)}</dd></div>")
        out.append("</dl></aside>")
    out.append("</section>")
    return "\n".join(out)


def render_toc(slides):
    out, last = [], None
    for sl in slides:
        if sl["part"] != last:
            if last is not None:
                out.append("</ol>")
            zh, en = PARTS[sl["part"]]
            out.append(f'<p class="toc-part">{zh}<span>{en}</span></p><ol>')
            last = sl["part"]
        out.append(f'<li><a href="#p{sl["n"]}"><span class="tn">{sl["n"]:02d}</span>'
                   f'<span class="tt">{html.escape(sl["zh"])}</span></a></li>')
    out.append("</ol>")
    return "\n".join(out)


def render_jump(slides):
    opts = ['<option value="">跳到某一页…</option>']
    for sl in slides:
        opts.append(f'<option value="p{sl["n"]}">{sl["n"]:02d} · {html.escape(sl["zh"])}</option>')
    opts.append('<option value="glossary">词汇表</option>')
    return "".join(opts)


def render_glossary():
    items = sorted(GLOSSARY.values(), key=lambda g: re.sub(r"^[^0-9a-z]+", "", g["en"].lower()))
    out = []
    for g in items:
        pages = " ".join(f'<a href="#p{p}">{p}</a>' for p in g["pages"])
        search = html.escape(f'{g["en"]} {g["zh"]}'.lower(), quote=True)
        out.append(f'<tr data-s="{search}"><th scope="row" lang="en">{g["en"]}</th>'
                   f'<td>{g["zh"]}</td><td class="gp">{pages}</td></tr>')
    return "\n".join(out), len(items)


CSS = r"""
/* 版式：左侧固定目录 + 右侧逐页卡片；每页内“原文 | 译文”两栏逐行对照，窄屏改为上下堆叠 */
:root{
  --bg:#F2F5F4; --surface:#FFFFFF; --ink:#14232A; --muted:#566870; --line:#D6DFDF;
  --accent:#08707A; --accent-ink:#FFFFFF; --soft:#E1EFEE; --gloss:#0A6A73; --gloss-bg:#E4F1F0;
  --note:#EBF0F4; --note-line:#CBD7DE; --snv:#C0392B; --win:#FBE2CC; --code-bg:#EAF0EF;
  --font-en:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
  --font-zh:"Noto Sans SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --font-zhs:"Noto Serif SC","Songti SC","STSong","SimSun",serif;
  --font-mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0D1517; --surface:#131E21; --ink:#E1EAEC; --muted:#93A5AA; --line:#24363A;
  --accent:#4DBCC4; --accent-ink:#06282B; --soft:#15302F; --gloss:#7FD2D7; --gloss-bg:#163538;
  --note:#16232A; --note-line:#2A3D45; --snv:#FF7B6C; --win:#4A2F1D; --code-bg:#1A2A2D; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0D1517; --surface:#131E21; --ink:#E1EAEC; --muted:#93A5AA; --line:#24363A;
  --accent:#4DBCC4; --accent-ink:#06282B; --soft:#15302F; --gloss:#7FD2D7; --gloss-bg:#163538;
  --note:#16232A; --note-line:#2A3D45; --snv:#FF7B6C; --win:#4A2F1D; --code-bg:#1A2A2D; color-scheme:dark}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:calc(64px + env(safe-area-inset-top,0px))}
@media (prefers-reduced-motion: reduce){html{scroll-behavior:auto}}
body{background:var(--bg);color:var(--ink);font-family:var(--font-en),var(--font-zh);font-size:16px;line-height:1.65;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}
a{color:var(--accent)}
a:focus-visible,button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
code{font-family:var(--font-mono);font-size:.9em;background:var(--code-bg);padding:.05em .35em;border-radius:3px;overflow-wrap:anywhere}
.layout{max-width:1360px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1fr);gap:0 40px}
@media (min-width:1120px){.layout{grid-template-columns:250px minmax(0,1fr)}}

/* 页首 */
.top{padding-block:40px 24px;border-bottom:1px solid var(--line);margin-bottom:8px}
.eyebrow{font-family:var(--font-mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}
.top h1{font-family:var(--font-zhs);font-weight:700;font-size:clamp(28px,4.4vw,44px);line-height:1.2;margin:0 0 8px;text-wrap:balance}
.top .sub{font-size:17px;color:var(--muted);margin:0 0 20px;max-width:62ch}
.dna{display:inline-block;background:none;padding:0;font-size:clamp(13px,1.9vw,17px);letter-spacing:.04em;color:var(--muted)}
.dna .win{background:var(--win);color:var(--ink);padding:.1em 0}
.dna .snv{color:var(--snv);font-weight:700}
.howto{margin-top:20px;display:grid;gap:8px;font-family:var(--font-zh);font-size:14.5px;color:var(--muted);max-width:78ch}
.howto p{margin:0}
.howto strong{color:var(--ink);font-weight:500}

/* 工具栏 */
.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding-block:10px;border-bottom:1px solid var(--line)}
.bar .lab{font-family:var(--font-zh);font-size:13px;color:var(--muted);margin-right:2px}
.tg{font:500 13.5px/1 var(--font-zh);padding:8px 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--ink);cursor:pointer}
.tg[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.tg .dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;background:currentColor;opacity:.35;vertical-align:1px}
.tg[aria-pressed="true"] .dot{opacity:1}
#jump{margin-left:auto;font:14px var(--font-zh);padding:7px 8px;border-radius:6px;border:1px solid var(--line);background:var(--surface);color:var(--ink);max-width:100%}
@media (min-width:1120px){#jump{display:none}}

/* 目录 */
.toc{display:none}
@media (min-width:1120px){.toc{display:block;position:sticky;top:calc(env(safe-area-inset-top,0px) + 16px);align-self:start;max-height:calc(100vh - 32px);overflow:auto;padding:24px 4px 40px 0;font-family:var(--font-zh);font-size:13.5px}}
.toc-part{margin:18px 0 6px;font-weight:700;font-size:12.5px;letter-spacing:.04em;color:var(--ink)}
.toc-part span{display:block;font-family:var(--font-en);font-weight:400;font-size:11.5px;color:var(--muted);letter-spacing:0}
.toc ol{list-style:none;margin:0;padding:0}
.toc a{display:flex;gap:8px;padding:4px 8px;border-radius:5px;color:var(--muted);text-decoration:none;line-height:1.4}
.toc a:hover{background:var(--soft);color:var(--ink)}
.toc a[aria-current="true"]{background:var(--soft);color:var(--accent);font-weight:500}
.toc .tn{font-family:var(--font-mono);font-size:12px;flex:none;padding-top:1px}
.toc .gl{margin-top:18px;display:block;font-weight:700;color:var(--ink)}

/* 每页 */
main{min-width:0}
.slide{padding-block:40px 8px;border-bottom:1px solid var(--line)}
.sh{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 14px;margin-bottom:16px}
.pg{font-family:var(--font-mono);font-weight:500;font-size:14px;color:var(--accent);letter-spacing:.04em}
.part{font-family:var(--font-zh);font-size:12.5px;color:var(--muted);letter-spacing:.04em}
.sh h2{flex-basis:100%;margin:0;font-family:var(--font-zhs);font-weight:600;font-size:clamp(21px,2.6vw,27px);line-height:1.35;text-wrap:balance}
.shot{margin:0 0 20px;max-width:720px}
.zoom{display:block;padding:0;border:1px solid var(--line);border-radius:6px;overflow:hidden;background:#fff;cursor:zoom-in;width:100%}
.zoom img{display:block;width:100%;height:auto;max-width:100%}
.shot figcaption{font-family:var(--font-zh);font-size:12.5px;color:var(--muted);margin-top:6px}

.rows{border-top:1px solid var(--line)}
.row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:4px 32px;padding-block:11px;border-bottom:1px solid var(--line)}
.row>div{min-width:0}
.en{font-family:var(--font-en);font-size:16px;line-height:1.7}
.zh{font-family:var(--font-zhs);font-size:16px;line-height:1.8;color:var(--ink)}
.k-head{padding-block:8px;font-family:var(--font-zh);font-size:12px;letter-spacing:.06em;color:var(--muted)}
.k-h .en{font-weight:600;font-size:19px;line-height:1.5}
.k-h .zh{font-weight:600;font-size:19px;line-height:1.6}
.k-li .en,.k-li .zh{position:relative;padding-left:18px}
.k-li .en::before,.k-li .zh::before{content:"";position:absolute;left:2px;top:.72em;width:6px;height:6px;border-radius:50%;background:var(--accent)}
.k-l2 .en,.k-l2 .zh{position:relative;padding-left:38px}
.k-l2 .en::before,.k-l2 .zh::before{content:"";position:absolute;left:22px;top:.85em;width:8px;height:1.5px;background:var(--muted)}
.k-fh{display:flex;gap:10px;align-items:baseline;grid-template-columns:none;padding-block:14px 8px;border-bottom:none}
.fh-tag{font-family:var(--font-zh);font-size:11.5px;letter-spacing:.08em;color:var(--accent);border:1px solid var(--accent);padding:1px 7px;border-radius:3px;flex:none}
.fh-l{font-family:var(--font-zh);font-size:13.5px;color:var(--muted);font-weight:500}
.k-f .en{font-size:14.5px;color:var(--ink)}
.k-f .zh{font-size:14.5px}
.k-f{background:var(--surface);padding-inline:12px;border-bottom:1px solid var(--line)}
.k-c .en,.k-c .zh{font-size:13.5px;color:var(--muted)}
.k-d{display:block;grid-template-columns:none;font-family:var(--font-zh);font-size:14px;color:var(--muted)}

/* 重点词 */
.t{border-bottom:1.5px dotted var(--accent);padding-bottom:1px}
.t .g{font-family:var(--font-zh);font-size:.74em;font-weight:500;font-style:normal;color:var(--gloss);background:var(--gloss-bg);border-radius:3px;padding:.05em .35em;margin-left:.3em;white-space:nowrap;letter-spacing:0;vertical-align:.08em}
.k-h .t .g{font-weight:500}
.hide-gl .t .g{display:none}
.hide-gl .t{cursor:help}

/* 隐藏译文自测 */
.hide-tr .row .zh{filter:blur(5px);cursor:pointer;user-select:none;transition:filter .15s}
.hide-tr .row .zh.rev{filter:none;user-select:auto}
.hide-tr .k-head div:last-child::after{content:"（点击模糊处显示）"}
@media (prefers-reduced-motion: reduce){.hide-tr .row .zh{transition:none}}
.hide-nt .notes{display:none}
.hide-im .shot{display:none}

/* 讲解 */
.notes{margin:22px 0 32px;background:var(--note);border:1px solid var(--note-line);border-radius:8px;padding:16px 20px 6px;font-family:var(--font-zh);max-width:80ch}
.notes h3{margin:0 0 10px;font-size:13px;letter-spacing:.12em;color:var(--accent);font-weight:700}
.notes dl{margin:0;display:grid;gap:12px;padding-bottom:12px}
.notes dt{font-weight:700;font-size:15px;color:var(--ink)}
.notes dd{margin:2px 0 0;font-size:15px;line-height:1.85;color:var(--ink)}

/* 词汇表 */
.gloss{padding-block:44px 60px}
.gloss h2{font-family:var(--font-zhs);font-weight:600;font-size:clamp(22px,2.8vw,28px);margin:0 0 6px}
.gloss .meta{font-family:var(--font-zh);color:var(--muted);font-size:14px;margin:0 0 14px}
#gq{width:100%;max-width:420px;font:15px var(--font-en),var(--font-zh);padding:9px 12px;border-radius:6px;border:1px solid var(--line);background:var(--surface);color:var(--ink);margin-bottom:14px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;min-width:520px}
th,td{text-align:left;padding:8px 14px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14.5px}
thead th{font-family:var(--font-zh);font-size:12px;letter-spacing:.06em;color:var(--muted);font-weight:500;background:var(--bg)}
tbody th{font-family:var(--font-en);font-weight:500}
tbody td{font-family:var(--font-zh)}
.gp{font-family:var(--font-mono);font-size:12.5px;white-space:nowrap;width:1%}
tbody th{width:40%}
.gp a{margin-right:6px;text-decoration:none}
#gempty{font-family:var(--font-zh);color:var(--muted)}
.foot{font-family:var(--font-zh);font-size:13px;color:var(--muted);padding-block:0 48px}

/* 放大图 */
#lb{border:none;padding:0;background:transparent;max-width:min(96vw,1440px);width:100%}
#lb::backdrop{background:rgba(5,12,14,.82)}
#lb img{display:block;width:100%;height:auto;border-radius:6px;background:#fff}
#lb button{position:absolute;top:8px;right:8px;font:600 14px var(--font-zh);padding:6px 12px;border-radius:999px;border:none;background:rgba(0,0,0,.6);color:#fff;cursor:pointer}

/* 窄屏：上下堆叠 */
@media (max-width:760px){
  body{font-size:15.5px}
  .row{grid-template-columns:minmax(0,1fr);gap:4px}
  .k-head{display:none}
  .row .zh{color:var(--muted);font-size:15px}
  .k-li .zh::before,.k-l2 .zh::before{display:none}
  .k-h .zh{font-size:17px;color:var(--ink)}
  .k-h .en{font-size:18px}
  .k-f{padding-inline:10px}
  .notes{padding:14px 14px 4px}
  .slide{padding-block:32px 4px}
  .bar .lab{display:none}
}
"""

JS = r"""
(function(){
  var root=document.documentElement, KEY='vep-reader-prefs-v1';
  var prefs={};
  try{prefs=JSON.parse(localStorage.getItem(KEY)||'{}')||{}}catch(e){prefs={}}
  var map={gl:'hide-gl',tr:'hide-tr',nt:'hide-nt',im:'hide-im'};
  function apply(){
    Object.keys(map).forEach(function(k){
      var on=prefs[k]!==false;
      document.body.classList.toggle(map[k],!on);
      var b=document.querySelector('[data-tg="'+k+'"]');
      if(b)b.setAttribute('aria-pressed',on?'true':'false');
    });
  }
  document.querySelectorAll('[data-tg]').forEach(function(b){
    b.addEventListener('click',function(){
      var k=b.getAttribute('data-tg');
      prefs[k]=(prefs[k]===false);
      if(k==='tr')document.querySelectorAll('.zh.rev').forEach(function(z){z.classList.remove('rev')});
      try{localStorage.setItem(KEY,JSON.stringify(prefs))}catch(e){}
      apply();
    });
  });
  apply();
  document.addEventListener('click',function(e){
    if(!document.body.classList.contains('hide-tr'))return;
    var z=e.target.closest&&e.target.closest('.row .zh');
    if(z&&!e.target.closest('a'))z.classList.toggle('rev');
  });
  var jump=document.getElementById('jump');
  jump.addEventListener('change',function(){
    if(!jump.value)return;
    var el=document.getElementById(jump.value);
    if(el){el.scrollIntoView();history.replaceState(null,'','#'+jump.value)}
    jump.value='';
  });
  var lb=document.getElementById('lb'), lbi=lb.querySelector('img');
  document.querySelectorAll('.zoom').forEach(function(b){
    b.addEventListener('click',function(){
      lbi.src=b.getAttribute('data-src');lbi.alt=b.querySelector('img').alt;
      if(lb.showModal){lb.showModal()}else{lb.setAttribute('open','')}
    });
  });
  lb.addEventListener('click',function(){lb.close?lb.close():lb.removeAttribute('open')});
  var q=document.getElementById('gq'), rows=[].slice.call(document.querySelectorAll('#gbody tr')), empty=document.getElementById('gempty');
  q.addEventListener('input',function(){
    var v=q.value.trim().toLowerCase(), n=0;
    rows.forEach(function(r){var hit=!v||r.getAttribute('data-s').indexOf(v)>-1;r.hidden=!hit;if(hit)n++});
    empty.hidden=n>0;
  });
  var links={};
  document.querySelectorAll('.toc a[href^="#p"]').forEach(function(a){links[a.getAttribute('href').slice(1)]=a});
  if('IntersectionObserver' in window){
    var cur=null;
    var io=new IntersectionObserver(function(es){
      es.forEach(function(en){
        if(en.isIntersecting){
          if(cur)cur.removeAttribute('aria-current');
          cur=links[en.target.id];
          if(cur){cur.setAttribute('aria-current','true');}
        }
      });
    },{rootMargin:'-20% 0px -70% 0px'});
    document.querySelectorAll('.slide').forEach(function(s){io.observe(s)});
  }
})();
"""


def main():
    slides = parse(SRC.read_text(encoding="utf-8"))
    body = "\n".join(render_slide(s) for s in slides)
    gloss_rows, gloss_n = render_glossary()
    page = f"""<title>变异效应预测讲义精读</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="Accurate genome-wide variant effect prediction（Imperial College London 2026）逐页双语精读：原文、重点词中文释义、译文与难点讲解。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@400;600;700&display=swap">
<style>{CSS}</style>
<div class="layout">
<nav class="toc" aria-label="目录">
{render_toc(slides)}
<a class="gl" href="#glossary">词汇表（{gloss_n} 条）</a>
</nav>
<main>
<header class="top">
<p class="eyebrow">Imperial College London · 2026 · Jun Cheng, Google DeepMind</p>
<h1>变异效应预测讲义精读</h1>
<p class="sub">Accurate genome-wide variant effect prediction —— 37 页逐页对照：原文、重点词中文释义、译文，以及难点讲解。</p>
{DNA}
<div class="howto">
<p><strong>怎么读：</strong>每页左栏是原文，右栏是译文，逐行对齐。原文中<span class="t"><span class="w">带点线的词</span><span class="g">重点词</span></span>后面紧跟中文释义。</p>
<p><strong>图中文字：</strong>幻灯片图片里的标签、坐标轴和截图文字也整理成了对照行（只整理了主要文字，没有逐字收录）。</p>
<p><strong>讲解：</strong>每页末尾的灰色框解释难懂的概念、图该怎么看，以及背景知识。</p>
<p><strong>自测：</strong>用下方按钮可以隐藏释义、译文、讲解或原图；隐藏译文后，点击模糊的译文可逐行显示。</p>
</div>
</header>
<div class="bar" role="toolbar" aria-label="显示选项">
<span class="lab">显示：</span>
<button type="button" class="tg" data-tg="gl" aria-pressed="true"><span class="dot"></span>释义</button>
<button type="button" class="tg" data-tg="tr" aria-pressed="true"><span class="dot"></span>译文</button>
<button type="button" class="tg" data-tg="nt" aria-pressed="true"><span class="dot"></span>讲解</button>
<button type="button" class="tg" data-tg="im" aria-pressed="true"><span class="dot"></span>原图</button>
<select id="jump" aria-label="跳到某一页">{render_jump(slides)}</select>
</div>
{body}
<section class="gloss" id="glossary" aria-labelledby="glossary-t">
<h2 id="glossary-t">词汇表</h2>
<p class="meta">全文标注过的 {gloss_n} 个重点词，按英文字母排序；右列数字是出现的页码，可点击跳转。</p>
<label for="gq" class="meta" style="display:block;margin-bottom:6px">搜索英文或中文</label>
<input id="gq" type="search" placeholder="例如 splice、致病、QTL" autocomplete="off">
<div class="tablewrap"><table>
<thead><tr><th scope="col">English</th><th scope="col">中文释义</th><th scope="col">页码</th></tr></thead>
<tbody id="gbody">
{gloss_rows}
</tbody></table></div>
<p id="gempty" hidden>没有找到匹配的词。</p>
</section>
<p class="foot">译文与讲解为学习辅助，专业结论请以原讲义和相关论文为准。第 35 页对比图的解读是根据图形做的推断。</p>
</main>
</div>
<dialog id="lb" aria-label="幻灯片大图"><button type="button">关闭</button><img alt=""></dialog>
<script>{JS}</script>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} ({len(page)//1024} KB), {len(slides)} slides, {gloss_n} glossary terms")


if __name__ == "__main__":
    main()
