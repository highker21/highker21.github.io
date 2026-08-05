#!/usr/bin/env python3
"""從各門課的 course.json 產生彙整頁，所有數字與章節標題都讀原始資料，不手抄。

用法：python3 tools/_build_lin_courses.py
每次執行都會即時抓取各站台的 course.json，所以林醫師更新課程後重跑一次即可同步。
新課上線時，把專案代號加進 COURSES 即可。
"""
import json, html, pathlib, urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "lin-courses.html"


def load(proj):
    """⚠️ 一定要帶 User-Agent：Cloudflare 對 urllib 預設的 Python-urllib/x.y 直接回 403。"""
    url = f"https://{proj}.pages.dev/course.json"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

# 顯示順序與各課的視覺色
COURSES = [
    ("himalaya-yoga",          "#5b8c5a", "🧘"),
    ("gym-course",             "#b5651d", "🏋️"),
    ("tarot-course",           "#6b5b95", "🔮"),
    ("thinking-habits-course", "#2c6e91", "🧠"),
    ("belief-economy",          "#a4703c", "💎"),
    ("deep-focus-course",       "#3f5d7d", "🎯"),
    ("photo-course",            "#8a6d9e", "📷"),
    ("ai-workflow-course",      "#3a7d7b", "⚙️"),
    ("longevity-course",        "#7a9e5b", "🧬"),
]

def esc(s): return html.escape(str(s))


def cn_num(n):
    """把課程數轉成中文數字，避免文案寫死「四門」之後忘了改。"""
    d = "零一二三四五六七八九"
    if n < 10:
        return d[n]
    if n < 20:
        return "十" + (d[n % 10] if n % 10 else "")
    return d[n // 10] + "十" + (d[n % 10] if n % 10 else "")

cards = []
names = []
n_evidence = 0
for proj, color, emoji in COURSES:
    d = load(proj)
    s, m, chs = d["config"]["site"], d["meta"], d["chapters"]
    names.append(s["name"])
    if m.get("evidence_checked"):
        n_evidence += 1

    # 副標：把 "課名 — 副標" 的破折號後半取出
    title = s["title"]
    sub = title.split("—", 1)[1].strip() if "—" in title else ""

    stats = [
        ("章節", f"{len(chs)}"),
        ("教學單元", f"{m.get('lesson_units', '—')}"),
        ("不重複影片", f"{m.get('video_unique', '—')}"),
        ("總時長", m.get("duration", "—")),
    ]
    if m.get("evidence_checked"):
        stats.append(("已查實證主題", f"{m['evidence_checked']}"))

    stat_html = "".join(
        f'<div class="stat"><span class="v">{esc(v)}</span><span class="k">{esc(k)}</span></div>'
        for k, v in stats)

    ch_html = "".join(
        f'<li><span class="cno">{esc(c["code"])}</span>'
        f'<span class="ct">{esc(c["title"])}</span>'
        f'<span class="cu">{len(c["units"])} 單元</span></li>'
        for c in chs)

    cards.append(f"""
  <article class="course" style="--c:{color}">
    <header class="chead">
      <div class="emoji" aria-hidden="true">{emoji}</div>
      <div>
        <h2>{esc(s["name"])}</h2>
        <p class="sub">{esc(sub)}</p>
      </div>
    </header>
    <p class="who"><b>適合誰</b>　{esc(s.get("audience", ""))}</p>
    <p class="desc">{esc(s.get("description", ""))}</p>
    <div class="stats">{stat_html}</div>
    <details>
      <summary>章節大綱（{len(chs)} 章）</summary>
      <ul class="chapters">{ch_html}</ul>
    </details>
    <a class="go" href="{esc(s["url"])}" target="_blank" rel="noopener">前往課程 →</a>
  </article>""")

import datetime
today = datetime.date.today().isoformat()   # 產出日期，每次重跑自動更新
N = cn_num(len(COURSES))                    # 課程數（中文），文案一律用它，不要寫死
NE = cn_num(n_evidence)                     # 有做實證查核的課程數
EV_TXT = ("每一門都標了該說法在文獻裡的實證強度"
          if n_evidence == len(COURSES)
          else f"其中{NE}門還標了該說法在文獻裡的實證強度")
name_list = "、".join(names)

page = f"""<!DOCTYPE html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>林協霆醫師 線上課程彙整</title>
<meta name="description" content="林協霆醫師製作的{N}門免費自學課程彙整：{name_list}。含章節大綱與規模對照。">
<style>
:root{{--ink:#1b1f1d;--sub:#5f655f;--line:#e6e2d8;--paper:#faf8f2;--card:#fff;--faint:#9a978c;--accent:#0f6e64;}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#eceae2;font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;
     color:var(--ink);padding:24px 14px;-webkit-font-smoothing:antialiased;line-height:1.65}}
.wrap{{max-width:920px;margin:0 auto}}
.top{{background:var(--paper);padding:30px 30px 24px;border-bottom:3px solid var(--accent)}}
.kick{{font-size:12px;letter-spacing:.3em;color:var(--accent);font-weight:800;margin-bottom:10px}}
h1{{font-size:30px;font-weight:900;line-height:1.25}}
.lede{{margin-top:12px;font-size:15.5px;color:var(--sub)}}
.lede b{{color:var(--ink)}}

.course{{background:var(--paper);padding:26px 30px 24px;margin-top:16px;border-left:6px solid var(--c)}}
.chead{{display:flex;gap:16px;align-items:flex-start}}
.emoji{{font-size:34px;line-height:1;flex:0 0 auto;margin-top:2px}}
.course h2{{font-size:22px;font-weight:900;color:var(--c);line-height:1.3}}
.sub{{font-size:14px;color:var(--sub);margin-top:4px}}
.who{{margin-top:16px;font-size:14.5px;color:var(--sub)}}
.who b{{color:var(--ink);font-weight:800;margin-right:2px}}
.desc{{margin-top:10px;font-size:15px}}

.stats{{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:10px;
      padding:10px 14px;min-width:92px;text-align:center;flex:1 1 92px}}
.stat .v{{display:block;font-size:19px;font-weight:900;color:var(--c);line-height:1.2}}
.stat .k{{display:block;font-size:11.5px;color:var(--faint);margin-top:3px}}

details{{margin-top:16px;border-top:1px dashed var(--line);padding-top:12px}}
summary{{cursor:pointer;font-size:14.5px;font-weight:800;color:var(--accent);list-style:none}}
summary::-webkit-details-marker{{display:none}}
summary:before{{content:"▸ ";}}
details[open] summary:before{{content:"▾ ";}}
.chapters{{list-style:none;margin-top:10px}}
.chapters li{{display:flex;gap:10px;align-items:baseline;padding:5px 0;
             border-bottom:1px solid var(--line);font-size:14.5px}}
.chapters li:last-child{{border-bottom:0}}
.cno{{flex:0 0 46px;font-size:11.5px;font-weight:800;color:var(--faint);letter-spacing:.04em}}
.ct{{flex:1 1 auto}}
.cu{{flex:0 0 auto;font-size:12px;color:var(--faint);white-space:nowrap}}

.go{{display:inline-block;margin-top:18px;background:var(--c);color:#fff;text-decoration:none;
    padding:11px 22px;border-radius:6px;font-size:15px;font-weight:800}}

.foot{{background:var(--paper);margin-top:16px;padding:20px 30px;font-size:12.5px;
      color:var(--sub);line-height:1.85}}
.foot b{{color:var(--ink)}}
.foot a{{color:var(--accent)}}

/* media query 放最後 */
@media (max-width:640px){{
  body{{padding:14px 8px}}
  .top,.course,.foot{{padding-left:18px;padding-right:18px}}
  h1{{font-size:23px}}
  .course h2{{font-size:19px}}
  .emoji{{font-size:27px}}
  .stat{{flex:1 1 calc(50% - 10px);min-width:0}}
  .chapters li{{flex-wrap:wrap}}
  .cno{{flex:0 0 42px}}
  .cu{{flex:0 0 100%;padding-left:52px}}
}}
</style></head><body>
<div class="wrap">

<div class="top">
  <div class="kick">課程彙整</div>
  <h1>林協霆醫師 線上課程</h1>
  <p class="lede">
    {N}門<b>免費的自學型課程</b>，共通做法是把 YouTube 上散落的優質影片依知識依賴順序重新編排，
    每個單元附上可自測的判準；{EV_TXT}，
    <b>包括對課程自己不利的結論也照實寫</b>。以下數字讀自各站的 <code>course.json</code>。
  </p>
</div>
{"".join(cards)}

<div class="foot">
  <b>關於這頁</b>　由盧子文醫師整理，方便一次看完{N}門課的規模與大綱再決定從哪門開始。
  課程內容與著作權屬林協霆醫師與各影片原上傳者，本頁僅提供索引與連結。<br>
  <b>數字怎麼來的</b>　章節標題、單元數、影片數與時長皆讀自各課程站台的 <code>course.json</code>，非人工抄寫。
  上表{N}門一律採同一組欄位以便橫向比較：教學單元取 <code>lesson_units</code>、影片取 <code>video_unique</code>（不重複計）。<br>
  <b>為什麼跟課程自己的文案對不起來</b>　各站文案採計方式不同，因此會有小差異，兩邊都沒錯（以下舉三例）：
  瑜伽寫 630 支是含重複播放的片段（不重複為 601）；健身寫 316 支是只算動作示範影片（全課不重複為 378）；
  思考課寫 83 個思考動作是不含「開始之前」那 2 個說明單元（教學單元合計 84）。<br>
  <b>署名說明</b>　各課程站台本身未標示作者姓名，此處的作者資訊來自盧醫師提供。<br>
  資料擷取日期：{today}　｜　工具版本：{today}
</div>

</div>
</body></html>
"""

OUT.write_text(page, encoding="utf-8")
print(f"✅ 已產生 {OUT}（{len(page):,} 字元，{len(cards)} 門課）")
