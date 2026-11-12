from fetcher import fetch_text

for year in (2026, 2027):
    url = f"https://www.mpo.com.my/season-{year}"
    try:
        text, _ = fetch_text(url)
        print(f"===== {url}: {len(text)} characters =====")
        print(text[:1500])
    except Exception as e:
        print(f"===== {url} failed: {e} =====")