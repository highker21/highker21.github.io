#!/usr/bin/env python3
"""產生各常見吋數的電視 usdz（給 iOS AR Quick Look 用）。

用法：python3 _build_tv_usdz.py
產出：tv-32.usdz … tv-85.usdz（與本檔同目錄）

⚠️ 為什麼用系統內建的 usdzip 而不是 pip 裝 USD：
macOS 內建 /usr/bin/usdcat 與 /usr/bin/usdzip（Apple 的 USD 工具鏈），
本機實測可用；pip 的 pxr 套件在這台機器沒有。

⚠️ usdz 就是「未壓縮(stored)的 zip」，不可用一般 zip 壓縮，
所以一律走 usdzip，不要自己組 zipfile。

⚠️ 刻意「不」寫 preliminary:anchoring（垂直面自動吸附）：
那是 AR Quick Look 的擴充語法，支援度不穩，寫錯會讓整個檔案打不開。
AR Quick Look 本來就允許使用者把物件拖到牆面，寧可少一個功能也不要開不起來。
"""
import math
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
SIZES = [32, 43, 50, 55, 65, 75, 85]

CM = 0.0254          # 1 吋 = 0.0254 公尺
K = math.sqrt(337)   # 16:9 的 寬:高:對角線 = 16:9:√337
DEPTH = 0.055        # 機身厚度 5.5 cm（現代平板電視的常見值）
BEZEL = 0.008        # 邊框 0.8 cm


def usda(inch: float) -> str:
    """產生一台電視的 USDA：外框(深灰) + 螢幕面(黑，稍微往前浮出)。"""
    diag = inch * CM
    w = diag / (K / 16)      # 螢幕可視區寬
    h = w * 9 / 16           # 螢幕可視區高
    # 機身比可視區大一圈（含邊框）
    bw, bh = w / 2 + BEZEL, h / 2 + BEZEL
    sw, sh = w / 2, h / 2
    d = DEPTH / 2
    sz = d + 0.0005          # 螢幕面浮出 0.5mm，避免與機身共面閃爍(z-fighting)

    return f'''#usda 1.0
(
    defaultPrim = "TV"
    metersPerUnit = 1
    upAxis = "Y"
)

def Xform "TV" (
    kind = "component"
)
{{
    def Mesh "Body"
    {{
        float3[] extent = [({-bw}, {-bh}, {-d}), ({bw}, {bh}, {d})]
        int[] faceVertexCounts = [4, 4, 4, 4, 4, 4]
        int[] faceVertexIndices = [0,1,2,3, 4,7,6,5, 0,4,5,1, 1,5,6,2, 2,6,7,3, 3,7,4,0]
        point3f[] points = [
            ({-bw}, {-bh}, {d}), ({bw}, {-bh}, {d}), ({bw}, {bh}, {d}), ({-bw}, {bh}, {d}),
            ({-bw}, {-bh}, {-d}), ({bw}, {-bh}, {-d}), ({bw}, {bh}, {-d}), ({-bw}, {bh}, {-d})
        ]
        uniform token subdivisionScheme = "none"
        rel material:binding = </TV/BodyMat>
    }}

    def Mesh "Screen"
    {{
        float3[] extent = [({-sw}, {-sh}, {sz}), ({sw}, {sh}, {sz})]
        int[] faceVertexCounts = [4]
        int[] faceVertexIndices = [0, 1, 2, 3]
        point3f[] points = [
            ({-sw}, {-sh}, {sz}), ({sw}, {-sh}, {sz}), ({sw}, {sh}, {sz}), ({-sw}, {sh}, {sz})
        ]
        uniform token subdivisionScheme = "none"
        rel material:binding = </TV/ScreenMat>
    }}

    def Material "BodyMat"
    {{
        token outputs:surface.connect = </TV/BodyMat/S.outputs:surface>
        def Shader "S"
        {{
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor = (0.14, 0.14, 0.15)
            float inputs:roughness = 0.45
            float inputs:metallic = 0.3
            token outputs:surface
        }}
    }}

    def Material "ScreenMat"
    {{
        token outputs:surface.connect = </TV/ScreenMat/S.outputs:surface>
        def Shader "S"
        {{
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor = (0.02, 0.02, 0.03)
            float inputs:roughness = 0.12
            float inputs:metallic = 0.0
            token outputs:surface
        }}
    }}
}}
'''


def main() -> int:
    ok, fail = [], []
    for inch in SIZES:
        src = BASE / f"_tv-{inch}.usda"
        out = BASE / f"tv-{inch}.usdz"
        src.write_text(usda(inch), encoding="utf-8")

        # 先驗 USDA 本身解析得過，再打包——省得包出一個壞檔還以為成功
        p = subprocess.run(["usdcat", str(src)], capture_output=True, text=True)
        if p.returncode != 0:
            fail.append((inch, "usdcat 解析失敗: " + p.stderr.strip()[:120]))
            continue

        out.unlink(missing_ok=True)
        p = subprocess.run(["usdzip", str(out), str(src)], capture_output=True, text=True)
        if p.returncode != 0 or not out.exists():
            fail.append((inch, "usdzip 失敗: " + (p.stderr or p.stdout).strip()[:120]))
            continue

        # 打包完再讀回來一次，確認 usdz 內容真的解析得動
        p = subprocess.run(["usdcat", str(out)], capture_output=True, text=True)
        if p.returncode != 0:
            fail.append((inch, "usdz 讀回失敗: " + p.stderr.strip()[:120]))
            continue

        diag = inch * CM
        w = diag / (K / 16)
        ok.append((inch, out.stat().st_size, w * 100, w * 9 / 16 * 100))
        src.unlink(missing_ok=True)

    print(f"=== 產出 {len(ok)}/{len(SIZES)} 個 usdz ===")
    for inch, size, wcm, hcm in ok:
        print(f"  tv-{inch}.usdz  {size:>6} bytes   螢幕 {wcm:6.1f} × {hcm:5.1f} cm")
    if fail:
        print(f"\n❌ 失敗 {len(fail)} 個：")
        for inch, why in fail:
            print(f"  {inch} 吋 → {why}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
