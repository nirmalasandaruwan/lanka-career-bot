import sys, os, requests, time, hashlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

# --- FB POSTING ---
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

# --- IMAGE SCRAPER ---
def get_job_flyer(driver, job_link):
    try:
        driver.get(job_link)
        time.sleep(7)
        imgs = driver.find_elements(By.TAG_NAME, "img")
        best_img, max_w = None, 0
        
        bad_keywords = ["logo", "banner", "whatsapp", "ad", "ads", "sponsored", "footer", "header", "icon", "avatar"]
        
        for img in imgs:
            src = img.get_attribute("src")
            if not src: continue
            
            src_lower = src.lower()
            if any(bad_word in src_lower for bad_word in bad_keywords): 
                continue
                
            try:
                w = int(img.get_attribute("naturalWidth") or 0)
                h = int(img.get_attribute("naturalHeight") or 0)
                if w > 350 and h > 300: 
                    if w > max_w: 
                        max_w, best_img = w, src
            except: continue
            
        return best_img
    except: return None

# --- SITE SCRAPER ---
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
            
            valid = False
            if "xpress.jobs" in url and "/view/" in href: valid = True
            elif "ikman.lk" in url and "/ad/" in href: valid = True
            elif "topjobs.lk" in url and "vacancy" in href: valid = True
            elif "jobenvoy.com" in url and "/job/" in href: valid = True
            elif "rooster.jobs" in url and "jobs" in href: valid = True
            elif any(x in url for x in ["rajayejobs.com", "colombojobs.lk", "plusinfo.lk", "jobhunder.com", "blogspot.com"]):
                if (href.endswith(".html") or "/2026/" in href) and len(title) > 20: valid = True

            if valid and len(title) > 15 and href not in seen_jobs:
                if href not in [j['link'] for j in found_jobs]:
                    found_jobs.append({'title': title, 'link': href})

        for job in found_jobs[:2]:
            flyer = get_job_flyer(driver, job['link'])
            msg = f"📢 අලුත්ම රැකියා අවස්ථාවක්! \n\n📌 තනතුර: {job['title']}\n🔗 වැඩි විස්තර: {job['link']}{HASHTAGS}"
            if post_to_facebook(msg, flyer):
                print(f"🎯 FB පෝස්ට් එක සාර්ථකයි: {job['title']}")
                save_new_job(job['link'])
                seen_jobs.append(job['link'])
            time.sleep(15)
    except Exception as e: print(f"❌ {name} Error: {str(e)}")

# --- WHATSAPP SCRAPER (100% ISOLATED) ---
def scrape_whatsapp_channel(driver, channel_url, seen_jobs):
    print(f"\n🔍 WhatsApp Channel පරීක්ෂා කරයි (Stealth Mode)...")
    try:
        driver.get(channel_url)
        time.sleep(20) 
        
        # පිටුවේ මොනවද තියෙන්නේ කියලා බලලා Meta බ්ලොක් කරලද කියලා චෙක් කරනවා
        page_source = driver.page_source.lower()
        if "update your browser" in page_source or "javascript" in page_source:
            print("⚠️ Meta සමාගම විසින් බොට්ව හඳුනාගෙන ඇත. අද දිනට WhatsApp පරීක්ෂාව නතර කෙරේ.")
            return

        # Layout ගැන හිතන්නේ නැතුව ලොකු අකුරු ගොඩවල් හොයනවා
        elements = driver.find_elements(By.XPATH, "//*[string-length(normalize-space(text())) > 50]")
        
        valid_messages = []
        for el in elements[-15:]: 
            try:
                text = el.text.strip()
                if len(text) > 40 and "WhatsApp" not in text and text not in [m['text'] for m in valid_messages]:
                    img_url = None
                    try:
                        imgs = el.find_elements(By.XPATH, ".//img | ./ancestor::*[position()<=3]//img")
                        for img in imgs:
                            src = img.get_attribute("src")
                            if src and "emoji" not in src and "avatar" not in src:
                                img_url = src
                                break
                    except: pass
                    valid_messages.append({'text': text, 'img': img_url})
            except: continue

        found_count = 0
        for msg in valid_messages[-3:]:
            text = msg['text']
            img_url = msg['img']
            msg_id = hashlib.md5((text[:100] + str(img_url)).encode('utf-8')).hexdigest()

            if msg_id not in seen_jobs:
                fb_msg = f"📢 WhatsApp හරහා ලැබුණු රැකියා පුවතක්! \n\n{text}\n{HASHTAGS}"
                if post_to_facebook(fb_msg, img_url):
                    print(f"🎯 WhatsApp පෝස්ට් එක සාර්ථකයි! (ID: {msg_id[:6]})")
                    save_new_job(msg_id)
                    seen_jobs.append(msg_id)
                    found_count += 1
                time.sleep(15)

        if found_count == 0:
            print("⚠️ අලුත් පෝස්ට් කිසිවක් WhatsApp එකේ තිබුණේ නැත.")

    except Exception as e:
        # WhatsApp එකේ මොන අවුල ගියත් බොට් නතර වෙන්නේ නෑ!
        print(f"❌ WhatsApp Scraper Error: {str(e)}")

if __name__ == "__main__":
    options = Options()
    # මේ අලුත් 'headless=new' එක Meta ලට අඳුරගන්න අමාරුයි
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # --- Anti-Bot Stealth කෑලි ටික ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # බ්‍රවුසරේ "bot" කියන ලේබල් එක මකලා දානවා
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    seen_jobs = load_seen_jobs()
    
    sites = [
        ("JobHunder", "https://www.jobhunder.com/"),
        ("XpressJobs", "https://xpress.jobs/jobs"),
        ("Ikman", "https://ikman.lk/en/ads/sri-lanka/jobs"),
        ("TopJobs", "http://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=ALL"),
        ("JobEnvoy", "https://jobenvoy.com/"),
        ("RoosterJobs", "https://rooster.jobs/"),
        ("PlusInfoGov", "https://www.plusinfo.lk/search/label/Government%20Jobs"),
        ("RajayeJobs", "https://www.rajayejobs.com/search/label/Government%20Jobs"),
        ("ColomboJobs", "https://www.colombojobs.lk/")
    ]
    
    try:
        # පියවර 1: මුලින්ම සයිට් 9ම පරීක්ෂා කරනවා (100% ආරක්ෂිතයි)
        for name, url in sites: 
            scrape_site(driver, url, name, seen_jobs)
            
        # පියවර 2: සයිට් 9ම ඉවර වුණාට පස්සේ අන්තිමටම WhatsApp එකට යනවා
        scrape_whatsapp_channel(driver, "https://whatsapp.com/channel/0029Va9Xpxx8PgsOtsAbFn45", seen_jobs)
        
    finally:
        driver.quit()
        print("\n🏁 සියලුම පරීක්ෂාවන් අවසන්! 🦾🔥")