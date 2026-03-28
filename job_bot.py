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

# සිංහල අකුරු ටර්මිනල් එකේ පෙන්වීමට අවශ්‍ය සැකසුම
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION (SECURE VERSION) ---
# 🛡️ GitHub Secrets වලින් යතුරු ලබාගැනීම
PAGE_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")
HASHTAGS = "\n\n#jobsearch #JobOpportunity #SriLankaJobs #srilanka #jobopportunities #jobseekers #jobvacancy #jobs"

DB_FILE = "seen_jobs.txt"

def load_seen_jobs():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return f.read().splitlines()
    except: return []

def save_new_job(job_id):
    with open(DB_FILE, "a", encoding='utf-8') as f:
        f.write(job_id + "\n")

# --- UTILS ---

def download_image(image_url, name="tiktok_ready.jpg"):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(name, 'wb') as f:
                f.write(response.content)
            return name
    except: return None
    return None

# --- FB POSTING LOGIC ---

def post_to_facebook(job_title, job_url, image_url=None):
    """ වෙබ් සයිට් ජොබ් පෝස්ට් කිරීම """
    post_message = f"📢 අලුත්ම රැකියා අවස්ථාවක්! \n\n📌 තනතුර: {job_title}\n🔗 වැඩි විස්තර: {job_url}{HASHTAGS}"
    
    if image_url:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
        payload = {'url': image_url, 'caption': post_message, 'access_token': PAGE_ACCESS_TOKEN}
    else:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"
        payload = {'message': post_message, 'link': job_url, 'access_token': PAGE_ACCESS_TOKEN}
    
    try:
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except: return False

def post_whatsapp_to_facebook(message, image_url=None):
    """ WhatsApp පෝස්ට් (Image + Text) FB එකට යැවීම """
    # 🦾 මචං මෙතන වෙනම Title එකක් නැහැ, පෝස්ට් එකේ ටෙක්ස්ට් එකයි Hashtags ටිකයි විතරයි වැටෙන්නේ
    fb_msg = f"📢 WhatsApp හරහා ලැබුණු රැකියා පුවතක්! \n\n{message}"
    
    if image_url:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
        payload = {'url': image_url, 'caption': fb_msg, 'access_token': PAGE_ACCESS_TOKEN}
    else:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"
        payload = {'message': fb_msg, 'access_token': PAGE_ACCESS_TOKEN}
    
    try:
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except: return False

# --- WEB SCRAPING ---

def get_job_flyer(driver, job_link):
    try:
        driver.get(job_link)
        time.sleep(6)
        img_elements = driver.find_elements(By.TAG_NAME, "img")
        best_image, max_width = None, 0
        for img in img_elements:
            src = img.get_attribute("src")
            if not src: continue
            try:
                width = int(img.get_attribute("naturalWidth") or 0)
                height = int(img.get_attribute("naturalHeight") or 0)
                if width > 400 and height > 400:
                    if width > max_width:
                        max_width, best_image = width, src
            except: continue
        return best_image
    except: return None

def scrape_site(driver, url, name, seen_jobs):
    print(f"\n🔍 {name} පරීක්ෂා කරයි...")
    try:
        driver.get(url)
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        found_jobs, links = [], driver.find_elements(By.TAG_NAME, "a")

        for link in links:
            href = str(link.get_attribute("href"))
            title = link.text.strip()
            valid = False
            
            if "xpress.jobs" in url and "/view/" in href: valid = True
            elif "ikman.lk" in url and "/ad/" in href: valid = True
            elif "topjobs.lk" in url and "vacancy" in href: valid = True
            elif "jobenvoy.com" in url and "/job/" in href: valid = True
            elif "rooster.jobs" in url and len(title) > 15 and "jobs" in href: valid = True
            elif any(x in url for x in ["rajayejobs.com", "colombojobs.lk", "plusinfo.lk", "jobhunder.com", "blogspot.com"]):
                if (href.endswith(".html") or "/2026/" in href) and len(title) > 20: valid = True

            if valid and len(title) > 15:
                if href not in seen_jobs and href not in [j['link'] for j in found_jobs]:
                    found_jobs.append({'title': title, 'link': href})

        if found_jobs:
            for job in found_jobs[:2]:
                flyer_url = get_job_flyer(driver, job['link'])
                if post_to_facebook(job['title'], job['link'], flyer_url):
                    print(f"🎯 FB පෝස්ට් එක සාර්ථකයි: {job['title']}")
                    save_new_job(job['link'])
                    seen_jobs.append(job['link'])
                    if flyer_url: download_image(flyer_url)
                time.sleep(15) 
        else: print(f"😴 {name} හි අලුත් ජොබ් නැත.")
    except Exception as e: print(f"❌ {name} Scraper Error: {str(e)}")

# --- WHATSAPP HYBRID SCRAPING ---

def scrape_whatsapp_channel(driver, channel_url, seen_jobs):
    print(f"\n🔍 WhatsApp Channel පරීක්ෂා කරයි (Hybrid Mode)...")
    try:
        driver.get(channel_url)
        time.sleep(20) # පෝස්ට් ලෝඩ් වෙන්න හොඳට වෙලාව දෙමු 🦾

        cards = driver.find_elements(By.CSS_SELECTOR, "div[role='row']") 

        found_count = 0
        for card in cards[-5:]: # අන්තිම පෝස්ට් 5 බලමු
            try:
                # 1. පෝස්ට් එකේ ටෙක්ස්ට් එක සොයමු
                full_text = ""
                try:
                    text_element = card.find_element(By.CSS_SELECTOR, "span[dir='ltr']")
                    full_text = text_element.text.strip()
                except: pass

                # 2. පෝස්ට් එකේ පින්තූරය සොයමු
                img_url = None
                try:
                    img_element = card.find_element(By.TAG_NAME, "img")
                    img_url = img_element.get_attribute("src")
                except: pass

                # 3. හිස් පෝස්ට් නම් skip කරමු
                if not full_text and not img_url: continue

                # 4. Unique ID එකක් හදමු (Text තිබ්බොත් ඒකෙන්, නැත්නම් Image URL එකෙන්)
                if full_text:
                    msg_id = hashlib.md5(full_text.encode()).hexdigest()
                else:
                    msg_id = hashlib.md5(img_url.encode()).hexdigest()

                if msg_id not in seen_jobs:
                    print(f"📢 WhatsApp අලුත් පෝස්ට් එකක් හමු වුණා! (Image: {'ඔව්' if img_url else 'නැත'})")
                    
                    # 5. කැප්ෂන් එක හදමු (ටෙක්ස්ට් එකයි හෑෂ්ටැග් ටිකයි) 🦾
                    # ටෙක්ස්ට් එක නැත්නම් හෑෂ්ටැග් ටික විතරක් වැටෙයි
                    fb_caption = f"{full_text}{HASHTAGS}" if full_text else HASHTAGS
                    
                    if post_whatsapp_to_facebook(fb_caption, img_url):
                        print(f"🎯 WhatsApp පෝස්ට් එක FB එකට දැම්මා.")
                        save_new_job(msg_id)
                        seen_jobs.append(msg_id)
                        found_count += 1
                        if img_url: download_image(img_url)
                    time.sleep(15)
            except: continue

        if found_count == 0: print("😴 WhatsApp හි අලුත් පෝස්ට් නැත.")
    except Exception as e: print(f"⚠️ WhatsApp Scraper Error: {str(e)}")

# --- MAIN RUNNER ---

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

if __name__ == "__main__":
    print("🤖 Lanka Career Hub Bot පණ ගැන්වෙයි (Sites 9 + WhatsApp Hybrid)...")
    seen_jobs, driver = load_seen_jobs(), get_driver()
    
    # 🦾 මචං මෙන්න සයිට් 9ම! කිසිවක් අතහැරියේ නැත.
    sites = [
        ("JobHunder", "https://www.jobhunder.com/"),
        ("XpressJobs", "https://xpress.jobs/jobs"),
        ("Ikman", "https://ikman.lk/en/ads/sri-lanka/jobs"),
        ("TopJobs", "http://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=ALL"),
        ("JobEnvoy", "https://jobenvoy.com/"),
        ("RoosterJobs", "https://rooster.jobs/"),
        ("PlusInfoGov", "https://www.plusinfo.lk/search/label/Government%20Jobs"),
        ("RajayeJobs", "https://www.rajayejobs.com/search/label/Government%20Jobs?max-results=7"),
        ("ColomboJobs", "https://www.colombojobs.lk/")
    ]
    
    try:
        # 1. සයිට් පරීක්ෂාව
        for name, url in sites:
            scrape_site(driver, url, name, seen_jobs)
            
        # 2. WhatsApp පරීක්ෂාව 🦾
        whatsapp_url = "https://whatsapp.com/channel/0029Va9Xpxx8PgsOtsAbFn45"
        scrape_whatsapp_channel(driver, whatsapp_url, seen_jobs)
        
    finally:
        driver.quit()
        print("\n🏁 සියලුම පරීක්ෂාවන් අවසන්! සුබ රාත්‍රියක් මචං නිර්මල! 🦾🔥")