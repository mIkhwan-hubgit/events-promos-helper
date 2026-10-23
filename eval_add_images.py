import json
from pathlib import Path

from fetcher import RateLimited, get_banner, wants_banner

EVAL_DIR = Path("eval")

for txt in (EVAL_DIR / "pages").glob("*.txt"):
    name = txt.stem
    posts = []
    for block in txt.read_text(encoding="utf-8").split("\n\n---\n\n"):
        lines = block.split("\n")
        if len(lines) >= 3 and lines[0].startswith("Title: ") and lines[2].startswith("Link: "):
            posts.append((lines[0][len("Title: "):], lines[2][len("Link: "):], "\n".join(lines[3:])))
    if not posts:
        continue  # not a feed page (e.g. POPULAR), so no banners to fetch

    img_dir = EVAL_DIR / "pages" / f"{name}_images"
    img_dir.mkdir(exist_ok=True)
    manifest, wanted, rate_limited = [], 0, False
    for i, (title, link, body) in enumerate(posts):
        if not wants_banner(body):
            continue
        wanted += 1
        try:
            banner = get_banner(link, allow_download=not rate_limited)
        except RateLimited:
            rate_limited = True
            print("Site is rate-limiting us: stopping downloads for now. Run this again later.")
            continue
        except Exception as e:
            print(f"Couldn't get banner for '{title}': {e}")
            continue
        if banner:
            data, mime = banner
            file_name = f"{i}.img"
            (img_dir / file_name).write_bytes(data)
            manifest.append({"label": title, "file": file_name, "mime": mime})

    (img_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{name}: have {len(manifest)} of {wanted} banners needed")