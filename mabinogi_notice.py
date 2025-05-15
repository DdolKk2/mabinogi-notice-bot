from playwright.sync_api import sync_playwright
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# Discord webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1372477208156835870/T2YPeiVsobNNyCjyWwLBs8PHPxXjIhNW5OYXkGkNzqEjO1mpxBZGAgspvJY1HclhYs9p"

# Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("rpa_creds.json", scope)
client = gspread.authorize(creds)

# Open sheet
spreadsheet = client.open_by_key("1EW1exkPc8hO90_I2awNgJ12LPsUzIh143er7_6UyqHQ")
sheet = spreadsheet.worksheet("공지내역")

# Existing titles for deduplication
existing_records = sheet.get_all_values()[1:]
existing_titles = {row[0] for row in existing_records if row}

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0",
        viewport={"width": 1920, "height": 1080}
    )
    page.goto("https://mabinogimobile.nexon.com/News/Notice")
    # 공지 목록이 로드될 때까지 최대 15초 대기
    page.wait_for_selector('xpath=//*[@id="mabinogim"]/div[2]/section[2]/div/ul/li', timeout=15000)

    items = page.query_selector_all('xpath=//*[@id="mabinogim"]/div[2]/section[2]/div/ul/li')
    notices = []
    for item in items[:10]:
        notice_id = item.get_attribute("data-threadid")
        link = f"https://mabinogimobile.nexon.com/News/Notice/{notice_id}"
        title = item.query_selector('xpath=div[1]/a/span').inner_text().strip()
        date = item.query_selector('xpath=div[2]/div[2]/div[2]').inner_text().strip()
        if title not in existing_titles:
            notices.append((title, date, link))

    browser.close()

# Send new notices
for title, date, link in notices:
    msg = f"📢 **{title}**\n📅 `{date}`\n🔗 [공지 바로가기]({link})"
    requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})

    # Append to sheet
    next_row = len(sheet.get_all_values()) + 1
    sheet.update(range_name=f"A{next_row}:C{next_row}", values=[[title, date, link]])
    print(f"✅ Sent and stored: {title}")

if not notices:
    print("🔁 No new notices.")
