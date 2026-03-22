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

# සිංහල අකුරු ප්‍රශ්නය විසඳීමට
sys.stdout.reconfigure(encoding='utf-8')

# --- FACEBOOK CONFIGURATION ---
PAGE_ACCESS_TOKEN = "EAAU4hyMkW0IBRMk8y7PXRL1YNCdk21ZCpIgRQoV6wX9yOV3CEyKiu5zUIZBThjDLAfNsJOFzEfLVuULogxfh9jGh4iHZCCaooMSDwEZCfL9zpCapbr1IR4100pcY1roK4yiVGHZAZCrBlhTPaQKsJm1NUmEKlD8fbP5mMMwjZCw7V5XgZAjqnvhtLjZAjsBJfGkM6xBsx"
PAGE_ID = "1071332246054096"
HASHTAGS = "\n\n#jobsearch #JobOpportunity #SriLankaJobs #srilanka #jobopportunities #jobseekers #jobvacancy #jobs"

# පෝස්ට් කරපු ජොබ් මතක තබා ගන්නා ෆයිල් එක
DB_FILE = "seen_jobs.txt"

def load_seen_jobs():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r") as f: return f.read().splitlines()

def save_new_job(link):
    with open(DB_FILE, "a") as f: f.write(link + "\n")

def post_to_facebook(job_title, job_url, image_url=None):
    """ Facebook එකට පෝස්ට් එක (පින්තූරය සමඟ හෝ නැතිව) යවන Function එක """
    post_message = f"📢 අලුත්ම රැකියා අවස්ථාවක්! \n\n📌 තනතුර: {job_title}\n🔗 වැඩි විස්තර සහ අයදුම් කිරීමට: {job_url}{HASHTAGS}"
    
    # පින්තූරයක් ඇත්නම් සහ එය පෝස්ටරයක් ලෙස හඳුනාගත හැකිනම් පමණක් /photos භාවිතා කරයි
    if image_url:
        url = f"https://graph.facebook.com/v25.0/{PAGE_ID}/photos"
        payload = {
            'url': image_url,
            'caption': post_message,
            'access_token': PAGE_ACCESS_TOKEN
        }
    else:
        # පින්තූරයක් නැතිවිට සාමාන්‍ය Feed එකට link එකක් ලෙස යවයි (මෙය Timeline එකේ හොඳින් පෙනේ)
        url = f"https://graph.facebook.com/v25.0/{PAGE_ID}/feed"
        payload = {
            'message': post_message,
            'link': job_url, # මෙතන ලින්ක් එක දාන නිසා ලස්සන preview එකක් වැටෙයි
            'access_token': PAGE_ACCESS_TOKEN
        }
    
    try:
        response = requests.post(url, data=payload)
        res_data = response.json()
        if response.status_code == 200:
            print(f"🎯 සාර්ථකව Facebook පෝස්ට් එක දැම්මා: {job_title}")
        else:
            print(f"❌ FB Error: {res_data.get('error', {}).get('message')}")
    except Exception as e:
        print(f"⚠️ FB Connection Error: {str(e)}")

def get_job_flyer(driver, job_link):
    """ ජොබ් පේජ් එකට ගිහින් නියම Flyer එක (පොඩි ලෝගෝ නොවී) හොයාගන්නා හැටි """
    try:
        driver.get(job_link)
        time.sleep(4) # පින්තූර ලෝඩ් වීමට වැඩිපුර වෙලාවක් දීම
        
        img_elements = driver.find_elements(By.TAG_NAME, "img")
        
        best_image = None
        max_width = 0

        for img in img_elements:
            src = img.get_attribute("src")
            # පින්තූරයේ සැබෑ පළල ලබා ගැනීම
            width = int(img.get_attribute("naturalWidth") or 0)
            
            # සාමාන්‍යයෙන් පෝස්ටර් එකක් width 400px ට වඩා වැඩියි
            if src and width > 400:
                if width > max_width:
                    max_width = width
                    best_image = src
                    
        return best_image
    except:
        return None

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
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        
        found_jobs = []
        links = driver.find_elements(By.TAG_NAME, "a")

        for link in links:
            href = str(link.get_attribute("href"))
            title = link.text.strip()
            
            valid = False
            if "xpress.jobs" in url and "/view/" in href: valid = True
            elif "ikman.lk" in url and "/ad/" in href: valid = True
            elif "topjobs.lk" in url and "vacancy" in href: valid = True
            elif any(x in url for x in ["blogspot.com", ".lk", ".com"]):
                if (href.endswith(".html") or "/2026/" in href) and len(title) > 20:
                    valid = True

            if valid and len(title) > 15:
                if href not in seen_jobs and href not in [j['link'] for j in found_jobs]:
                    found_jobs.append({'title': title, 'link': href})

        if found_jobs:
            print(f"✅ අලුත් ජොබ් {len(found_jobs[:2])}ක් හමු වුණා!")
            for job in found_jobs[:2]:
                print(f"🖼️ {job['title']} සඳහා පෝස්ටරය සොයමින්...")
                flyer_url = get_job_flyer(driver, job['link'])
                
                # පින්තූරය ෂුවර් නැත්නම් Flyer_url එක None ලෙස යවයි
                post_to_facebook(job['title'], job['link'], flyer_url)
                
                save_new_job(job['link'])
                seen_jobs.append(job['link'])
                time.sleep(10) # Facebook එකෙන් Spam නොවීමට වැඩිපුර වෙලාවක් දීම
        else:
            print("😴 අලුත් ජොබ් කිසිවක් නැත.")

    except Exception as e:
        print(f"❌ {name} හිදී පොඩි අවුලක්: {str(e)}")

if __name__ == "__main__":
    print("🤖 Lanka Career Hub Bot පණ ගැන්වෙයි...")
    seen_jobs = load_seen_jobs()
    driver = get_driver()
    
    sites = [
        ("XpressJobs", "https://xpress.jobs/jobs"),
        ("Ikman", "https://ikman.lk/en/ads/sri-lanka/jobs"),
        ("TopJobs", "http://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=ALL"),
        ("JobVacanciesSL", "https://jobvacanciesinsl.blogspot.com/")
    ]
    
    try:
        for name, url in sites:
            scrape_site(driver, url, name, seen_jobs)
    finally:
        driver.quit()
        print("\n🏁 සියලුම පරීක්ෂාවන් අවසන්! සුබ රාත්‍රියක් මචං!")