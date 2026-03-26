import sys
import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# සිංහල අකුරු ටර්මිනල් එකේ පෙන්වීමට අවශ්‍ය සැකසුම
sys.stdout.reconfigure(encoding='utf-8')

# --- FACEBOOK CONFIGURATION ---
PAGE_ACCESS_TOKEN = "EAAVNuLDLZCaEBRA6qH9qRIFwYMgL8XSZBevJi8qANZCnLGVxmtqmbmKpfAtZBq4UQQ2vZA24VeaaqctojtgT9BAJMYX2szm4gyWDZBA6eB4fygZBUpSEkOEvZCoyrMiXhMT7WkSqZCz3ZBjCjuCFbVPJj2bEhwREOwUR60R4HCYZAFTk1nEAbCu6YVdBUAijzTmtNZAXDtaNUP9iGbOCxhNxCmjZC"
PAGE_ID = "1071332246054096"
HASHTAGS = "\n\n#jobsearch #JobOpportunity #SriLankaJobs #srilanka #jobopportunities #jobseekers #jobvacancy #jobs"

# පෝස්ට් කරපු ජොබ් ලින්ක් මතක තබා ගන්නා ෆයිල් එක
DB_FILE = "seen_jobs.txt"

def load_seen_jobs():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return f.read().splitlines()
    except: return []

def save_new_job(link):
    with open(DB_FILE, "a", encoding='utf-8') as f:
        f.write(link + "\n")

def post_to_facebook(job_title, job_url, image_url=None):
    """ Facebook පේජ් එකට පෝස්ට් එක යැවීම """
    post_message = f"📢 අලුත්ම රැකියා අවස්ථාවක්! \n\n📌 තනතුර: {job_title}\n🔗 වැඩි විස්තර සහ අයදුම් කිරීමට: {job_url}{HASHTAGS}"
    
    if image_url:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
        payload = {'url': image_url, 'caption': post_message, 'access_token': PAGE_ACCESS_TOKEN}
    else:
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"
        payload = {'message': post_message, 'link': job_url, 'access_token': PAGE_ACCESS_TOKEN}
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"🎯 සාර්ථකව Facebook පෝස්ට් එක දැම්මා: {job_title}")
        else:
            print(f"❌ FB Error: {response.json().get('error', {}).get('message')}")
    except Exception as e: print(f"⚠️ FB Connection Error: {str(e)}")

def get_job_flyer(driver, job_link):
    """ ජොබ් පේජ් එකට ගිහින් ලොකුම සහ නියම Flyer එක සොයාගැනීම """
    # 🚫 අයින් කළ යුතු පින්තූර වල නමේ තියෙන වචන
    KEYWORDS_TO_IGNORE = ["logo", "banner", "follow-us", "whatsapp", "plusinfo-channel", "generic-logo", "adsense", "uber"]

    try:
        driver.get(job_link)
        time.sleep(6) # පින්තූර ලෝඩ් වීමට කාලය දීම
        img_elements = driver.find_elements(By.TAG_NAME, "img")
        best_image, max_width = None, 0

        for img in img_elements:
            src = img.get_attribute("src")
            if not src: continue
            
            # 1. නම අනුව පරීක්ෂාව
            src_lower = src.lower()
            if any(kw in src_lower for kw in KEYWORDS_TO_IGNORE): continue

            try:
                width = int(img.get_attribute("naturalWidth") or 0)
                height = int(img.get_attribute("naturalHeight") or 0)
                
                # 2. මානයන් සහ හැඩය අනුව පරීක්ෂාව (Aspect Ratio)
                # පෝස්ටරයක් නම් සාමාන්‍යයෙන් පළල 450px ට වඩා වැඩියි සහ උස 400px ට වඩා වැඩියි
                if width > 450 and height > 400:
                    # පින්තූරය ගොඩක් දිගටි (Landscape) නම් ඒක Flyer එකක් නෙවෙයි (Ad Banner එකක්)
                    if width < (height * 1.8):
                        if width > max_width:
                            max_width, best_image = width, src
            except: continue
        return best_image
    except: return None

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_site(driver, url, name, seen_jobs):
    print(f"\n🔍 {name} පරීක්ෂා කරමින් පවතියි...")
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
            elif any(x in url for x in ["rajayejobs.com", "colombojobs.lk", "plusinfo.lk", "blogspot.com"]):
                if (href.endswith(".html") or "/2026/" in href or "/2025/" in href) and len(title) > 20:
                    valid = True

            if valid and len(title) > 15:
                if href not in seen_jobs and href not in [j['link'] for j in found_jobs]:
                    found_jobs.append({'title': title, 'link': href})

        if found_jobs:
            print(f"✅ අලුත් ජොබ් {len(found_jobs[:2])}ක් හමු වුණා!")
            for job in found_jobs[:2]:
                print(f"🖼️ {job['title']} පෝස්ටරය සොයමින්...")
                flyer_url = get_job_flyer(driver, job['link'])
                post_to_facebook(job['title'], job['link'], flyer_url)
                save_new_job(job['link'])
                seen_jobs.append(job['link'])
                time.sleep(15) 
        else: print("😴 අලුත් ජොබ් කිසිවක් නැත.")
    except Exception as e: print(f"❌ {name} හිදී පොඩි අවුලක්: {str(e)}")

if __name__ == "__main__":
    print("🤖 Lanka Career Hub Bot පණ ගැන්වෙයි...")
    seen_jobs, driver = load_seen_jobs(), get_driver()
    
    sites = [
        ("XpressJobs", "https://xpress.jobs/jobs"),
        ("Ikman", "https://ikman.lk/en/ads/sri-lanka/jobs"),
        ("TopJobs", "http://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=ALL"),
        ("JobVacanciesSL", "https://jobvacanciesinsl.blogspot.com/"),
        ("RajayeJobs", "https://www.rajayejobs.com/search/label/Government%20Jobs?max-results=7"),
        ("ColomboJobs", "https://www.colombojobs.lk/"),
        ("PlusInfoGov", "https://www.plusinfo.lk/search/label/Government%20Jobs"),
        ("PlusInfoPrivate", "https://www.plusinfo.lk/search/label/Private%20Jobs"),
        ("PlusInfoNGO", "https://www.plusinfo.lk/search/label/NGO%20Jobs")
    ]
    
    try:
        for name, url in sites:
            scrape_site(driver, url, name, seen_jobs)
    finally:
        driver.quit()
        print("\n🏁 සියලුම පරීක්ෂාවන් අවසන්! සුබ රාත්‍රියක් මචං!")