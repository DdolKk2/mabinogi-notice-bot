import requests
from bs4 import BeautifulSoup

URL = "https://mabinogimobile.nexon.com/News/Notice"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

response = requests.get(URL, headers=headers)
html = response.text

# 페이지 일부 확인
print(html[:2000])
