#!/usr/bin/env python3
"""依 _tv_models.json（官方規格，B 2026-10-11 核對）產生品牌機型的 AR 模型：ar/brand/<slug>.usdz

壁掛情境：只用「不含底座」的機身寬×高×深；螢幕可視區依可視對角線（無資料時用標稱吋數）以 16:9 計算、置中。
不使用品牌照片與 logo。另輸出 brand/index.json 給頁面的品牌選單用。
"""
import json, math, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _build_tv_usdz import usda_box

BASE = Path(__file__).resolve().parent
OUT = BASE / "brand"
K = math.sqrt(337)


def slug(x):
    return re.sub(r"[^a-z0-9]+", "-", (x["brand"] + "-" + x["series"].split("(")[0] + "-" + str(x["inch"])).lower()).strip("-")


def main():
    data = json.load(open(BASE / "_tv_models.json", encoding="utf-8"))
    data = data if isinstance(data, list) else data.get("models", data)
    OUT.mkdir(exist_ok=True)
    index, fail = [], []
    for x in sorted(data, key=lambda x: (x["brand"], x["inch"])):
        w_mm, h_mm, d_mm = x["body_mm"]
        diag_in = x.get("screen_diag_in") or x["inch"]
        sw = diag_in * 0.0254 / (K / 16)
        sh = sw * 9 / 16
        bw, bh, bd = w_mm / 1000, h_mm / 1000, d_mm / 1000
        if sw > bw or sh > bh:   # 規格異常保護：可視區不得大於機身
            sw, sh = bw - 0.006, (bw - 0.006) * 9 / 16
        name = slug(x)
        src = OUT / f"_{name}.usda"
        out = OUT / f"{name}.usdz"
        src.write_text(usda_box(bw, bh, bd, sw, sh), encoding="utf-8")
        p = subprocess.run(["usdzip", out.name, src.name], capture_output=True, text=True, cwd=str(OUT))
        src.unlink(missing_ok=True)   # 中間檔不留
        if p.returncode != 0 or not out.exists():
            fail.append((name, p.stderr[:120])); continue
        index.append({"brand": x["brand"], "series": x["series"], "model": x["model"], "inch": x["inch"],
                      "body_mm": [w_mm, h_mm, d_mm], "file": f"ar/brand/{out.name}", "src": x.get("src", "")})
        print(f"  {out.name:40s} 機身 {w_mm/10:.1f} × {h_mm/10:.1f} × {d_mm/10:.1f} cm")
    json.dump(index, open(OUT / "index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if fail:
        print("FAIL", fail); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
