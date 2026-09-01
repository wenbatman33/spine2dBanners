#!/usr/bin/env python3
"""Export each banner as one relocatable static HTML folder."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "assets/banners/champions-league-2026"
EXPORT_ROOT = ROOT / "banners"
SHARED_VENDOR = PROJECT / "player/vendor"

BANNERS = [
    ("01-champions-night", "欧冠巅峰之夜", PROJECT / "spine-3.8/runtime", "champions-league-2026"),
    ("02-star-summit", "群星巅峰夜", PROJECT / "series/02-star-summit/spine-3.8/runtime", "banner"),
    ("03-rivalry", "豪门生死战", PROJECT / "series/03-rivalry/spine-3.8/runtime", "banner"),
    ("04-champion-road", "冠军之路", PROJECT / "series/04-champion-road/spine-3.8/runtime", "banner"),
    ("05-striker-storm", "锋线风暴", PROJECT / "series/05-striker-storm/spine-3.8/runtime", "banner"),
    ("06-gift-goddess", "女神生日限定", PROJECT / "series/06-gift-goddess/spine-3.8/runtime", "banner"),
    ("07-lucky-tiger", "福运小虎", PROJECT / "series/07-lucky-tiger/spine-3.8/runtime", "banner"),
    ("08-forward-dribble", "一路带球向前冲", PROJECT / "series/08-forward-dribble/spine-3.8/runtime", "banner"),
    ("09-treasure-chest", "开箱暴击", PROJECT / "series/09-treasure-chest/spine-3.8/runtime", "banner"),
    ("10-operative-idle", "王牌特勤", PROJECT / "series/10-operative-idle/spine-3.8/runtime", "banner"),
    ("11-beauty-wink", "心动奖金眨眼挑战", PROJECT / "series/11-beauty-wink/spine-3.8/runtime", "banner"),
]

HTML = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title} · Spine Banner</title>
    <link rel="stylesheet" href="./vendor/spine-player-3.8.css" />
    <style>
      html, body {{ width:100%; min-height:100%; margin:0; background:#020812; }}
      body {{ display:grid; place-items:center; }}
      #player {{ width:min(100vw,1240px); aspect-ratio:620/272; overflow:hidden; background:#020812; }}
    </style>
  </head>
  <body>
    <div id="player" aria-label="{title}"></div>
    <script src="./vendor/spine-player-3.8.js"></script>
    <script>
      new spine.SpinePlayer("player", {{
        jsonUrl:"./spine/{asset_id}/banner.json",
        atlasUrl:"./spine/{asset_id}/banner.atlas",
        animation:"animation",
        loop:true,
        alpha:true,
        premultipliedAlpha:false,
        showControls:false,
        backgroundColor:"#020812",
        viewport:{{x:-310,y:-136,width:620,height:272,padLeft:"0%",padRight:"0%",padTop:"0%",padBottom:"0%"}}
      }});
    </script>
  </body>
</html>
"""

EMBED = """<iframe src="./banners/{slug}/index.html" title="{title}" width="620" height="272" style="border:0;display:block;max-width:100%;aspect-ratio:620/272" loading="lazy" allow="autoplay"></iframe>
"""


def export_banner(slug: str, title: str, source: Path, basename: str) -> str:
    target = EXPORT_ROOT / slug
    source_json = source / f"{basename}.json"
    source_atlas = source / f"{basename}.atlas"
    source_png = source / f"{basename}.png"
    digest = hashlib.sha256(
        source_json.read_bytes() + source_atlas.read_bytes() + source_png.read_bytes()
    ).hexdigest()[:12]
    if target.exists():
        shutil.rmtree(target)
    spine_dir = target / "spine" / digest
    vendor_dir = target / "vendor"
    spine_dir.mkdir(parents=True, exist_ok=True)
    vendor_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_json, spine_dir / "banner.json")
    shutil.copy2(source_png, spine_dir / "banner.png")
    atlas_lines = source_atlas.read_text(encoding="utf-8").splitlines()
    atlas_lines[0] = "banner.png"
    (spine_dir / "banner.atlas").write_text("\n".join(atlas_lines) + "\n", encoding="utf-8")

    shutil.copy2(SHARED_VENDOR / "spine-player-3.8.css", vendor_dir / "spine-player-3.8.css")
    shutil.copy2(SHARED_VENDOR / "spine-player-3.8.js", vendor_dir / "spine-player-3.8.js")
    (target / "index.html").write_text(
        HTML.format(title=title, asset_id=digest), encoding="utf-8"
    )
    (target / "embed-code.txt").write_text(
        EMBED.format(slug=slug, title=title), encoding="utf-8"
    )
    return digest


def main() -> None:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    versions: dict[str, str] = {}
    for item in BANNERS:
        versions[item[0]] = export_banner(*item)
    (ROOT / "vendor").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SHARED_VENDOR / "spine-player-3.8.css", ROOT / "vendor/spine-player-3.8.css")
    shutil.copy2(SHARED_VENDOR / "spine-player-3.8.js", ROOT / "vendor/spine-player-3.8.js")
    root_index = ROOT / "index.html"
    html = root_index.read_text(encoding="utf-8")
    marker = "      const assetVersions = "
    start = html.index(marker)
    end = html.index(";", start) + 1
    version_line = marker + json.dumps(versions, ensure_ascii=False, separators=(",", ":")) + ";"
    html = html[:start] + version_line + html[end:]
    root_index.write_text(html, encoding="utf-8")

    for destination, base_href in (
        (ROOT / "gallery/index.html", "../"),
        (PROJECT / "index.html", "../../../"),
        (PROJECT / "gallery/index.html", "../../../../"),
    ):
        page = html.replace(
            '    <meta name="viewport" content="width=device-width, initial-scale=1" />',
            '    <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
            f'    <base href="{base_href}" />',
            1,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
    print(json.dumps({"exported":len(BANNERS),"versions":versions},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
