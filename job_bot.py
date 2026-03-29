import sys
import os
import requests
import time
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# සිංහල අකුරු පෙන්වීමට
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
PAGE_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")
HASHTAGS = "\n\n#jobsearch #JobOpportunity #SriLankaJobs #srilanka #jobs"
DB_FILE = "seen_jobs.txt"

def load_seen_jobs():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return [line.strip() for line in f.read().splitlines() if line.strip()]
    except: return []

def save_new_job(job_id):
    with open(DB_FILE, "a", encoding='utf-8') as f:
        f.write(job_id + "\n")

# --- POSTING ---
def post_to_facebook(message, image_url=None):
    if image_url:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
        payload = {'url': image_url, 'caption': message, 'access_token': PAGE_ACCESS_TOKEN}
    else:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"
        payload = {'message': message, 'access_token': PAGE_ACCESS_TOKEN}
    try:
        r = requests.post(url, data=payload)
        return r.status_code == 200
    except: return False

# --- SCRAPERS ---
def scrape_site(driver, url, name, seen_jobs):
    print(f"\n🔍 {name} පරීක්ෂා කරයි...")
    try:
        driver.get(url)
        time.sleep(10)
        links = driver.find_elements(By.TAG_NAME, "a")
        found_jobs = []

        for link in links:
            href = str(link.get_attribute("href"))
            title = link.text.strip()
            
            # 🦾 Validation එක තවත් ලිහිල් කළා අලුත් ජොබ් අල්ලගන්න
            is_valid = False
            if any(x in href for x in ["/view/", "/ad/", "vacancy", "/job/", "jobs", ".html", "/2026/"]):
                is_valid = True

            if is_valid and len(title) > 10 and href not in seen_jobs:
                if href not in [j['link'] for j in found_jobs]:
                    found_jobs.append({'title': title, 'link': href})

        if found_jobs:
            for job in found_jobs[:2]:
                fb_msg = f"📢 අලුත්ම රැකියා අවස්ථාවක්! \n\n📌 තනතුර: {job['title']}\n🔗 වැඩි විස්තර: {job['link']}{HASHTAGS}"
                if post_to_facebook(fb_msg):
                    print(f"🎯 FB පෝස්ට් එක සාර්ථකයි: {job['title']}")
                    save_new_job(job['link'])
                    seen_jobs.append(job['link'])
                time.sleep(15)
        else: print(f"😴 {name} හි අලුත් ජොබ් නැත.")
    except Exception as e: print(f"❌ {name} Error: {str(e)}")

def scrape_whatsapp_channel(driver, channel_url, seen_jobs):
    print(f"\n🔍 WhatsApp Channel පරීක්ෂා කරයි (Hybrid Mode)...")
    try:
        driver.get(channel_url)
        time.sleep(20)
        # 🦾 අලුත්ම XPath එක (වැඩිපුර පෝස්ට් අල්ලගන්න)
        cards = driver.find_elements(By.XPATH, "//div[@role='row'] | //div[contains(@class, 'copyable-text')]")
        
        found_count = 0
        for card in cards[-10:]:
            try:
                text = ""
                try: text = card.find_element(By.CSS_SELECTOR, "span[dir='ltr']").text.strip()
                except: pass
                
                img_url = None
                try: img_url = card.find_element(By.TAG_NAME, "img").get_attribute("src")
                except: pass

                if not text and not img_url: continue
                msg_id = hashlib.md5((text + str(img_url)).encode()).hexdigest()

                if msg_id not in seen_jobs:
                    print(f"📢 WhatsApp අලුත් පෝස්ට් එකක් හමු වුණා!")
                    fb_msg = f"📢 WhatsApp හරහා ලැබුණු රැකියා පුවතක්! \n\n{text}{HASHTAGS}" if text else HASHTAGS
                    if post_to_facebook(fb_msg, img_url):
                        save_new_job(msg_id)
                        seen_jobs.append(msg_id)
                        found_count += 1
                    time.sleep(15)
            except: continue
        if found_count == 0: print("😴 WhatsApp හි අලුත් පෝස්ට් නැත.")
    except Exception as e: print(f"⚠️ WhatsApp Error: {str(e)}")

# --- MAIN ---
if __name__ == "__main__":
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    seen_jobs = load_seen_jobs()
    sites = [
        ("JobHunder", "https://www.jobhunder.com/"),
        ("XpressJobs", "https://xpress.jobs/jobs"),
        ("Ikman", "https://ikman.lk/en/ads/sri-lanka/jobs"),
        ("TopJobs", "http://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=ALL"),
        ("JobEnvoy", "https://jobenvoy.com/"),
        ("PlusInfoGov", "https://www.plusinfo.lk/search/label/Government%20Jobs"),
        ("RajayeJobs", "https://www.rajayejobs.com/search/label/Government%20Jobs")
    ]
    
    try:
        for name, url in sites: scrape_site(driver, url, name, seen_jobs)
        scrape_whatsapp_channel(driver, "https://whatsapp.com/channel/0029Va9Xpxx8PgsOtsAbFn45", seen_jobs)
    finally:
        driver.quit()
        print("\n🏁 සියලුම පරීක්ෂාවන් අවසන්! ä