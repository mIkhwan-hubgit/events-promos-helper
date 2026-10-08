import requests
from bs4 import BeautifulSoup

URL = "https://www.popular.com.my/ongoing-promotions/"
HEADERS = {
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
   }

response = requests.get(URL, headers=HEADERS, timeout=20)
print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
print("Page title:", soup.title.string if soup.title else "(none)")

text = soup.get_text(separator="\n", strip=True)
print("Text length:", len(text))
print(text[:1500])