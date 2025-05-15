from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# 📌 디스코드 Webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1372477208156835870/T2YPeiVsobNNyCjyWwLBs8PHPxXjIhNW5OYXkGkNzqEjO1mpxBZGAgspvJY1HclhYs9p"

# 📌 Google Sheets 인증 및 열기
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("rpapython-444406-625556863734.json", scope)
client = gspread.authorize(creds)

# 📌 시트 열기 (문서 ID 고정, 시트 탭 이름: 공지내역)
spreadsheet = client.open_by_key("1EW1exkPc8hO90_I2awNgJ12LPsUzIh143er7_6UyqHQ")
sheet = spreadsheet.worksheet("공지내역")

# 📌 기존 공지 제목과 링크 불러오기
existing_records = sheet.get_all_values()[1:]  # 헤더 제외
existing_titles = {row[0] for row in existing_records if len(row) > 0}  # A열 제목
existing_links = {row[2] for row in existing_records if len(row) > 2}  # C열 링크

# 📌 Selenium 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--lang=ko-KR")
options.add_argument("user-agent=Mozilla/5.0")

driver = webdriver.Chrome(options=options)
driver.get("https://mabinogimobile.nexon.com/News/Notice")
time.sleep(3)

notices = []

# 📌 공지 최대 10개 크롤링
for i in range(1, 11):
    try:
        base_xpath = f'//*[@id="mabinogim"]/div[2]/section[2]/div/ul/li[{i}]'

        # 공지 ID → URL 생성
        li_elem = driver.find_element("xpath", base_xpath)
        notice_id = li_elem.get_attribute("data-threadid")
        link = f"https://mabinogimobile.nexon.com/News/Notice/{notice_id}"

        # 제목
        title_xpath = f"{base_xpath}/div[1]/a/span"
        title_elem = driver.find_element("xpath", title_xpath)
        title = title_elem.text.strip()

        # 날짜
        date_xpath = f"{base_xpath}/div[2]/div[2]/div[2]"
        date_elem = driver.find_element("xpath", date_xpath)
        date = date_elem.text.strip()

        # 제목 중복 제거 기준으로 저장
        if title not in existing_titles:
            notices.append((title, date, link))

    except Exception as e:
        print(f"❌ {i}번째 항목 에러: {e}")

driver.quit()

# 📌 새 공지 알림 + 시트에 누적 추가
for title, date, link in notices:
    # 디스코드 전송
    message = f"📢 **{title}**\n📅 `{date}`\n🔗 [공지 바로가기]({link})"
    requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

    # 시트 마지막 행 다음 줄에 추가
    next_row = len(sheet.get_all_values()) + 1
    sheet.update(range_name=f"A{next_row}:C{next_row}", values=[[title, date, link]])
    print(f"✅ 전송 및 저장됨: {title}")

if not notices:
    print("🔁 새로운 공지 없음.")
