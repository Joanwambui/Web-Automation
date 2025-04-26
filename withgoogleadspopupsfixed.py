import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

# === WebDriver Setup ===
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--enable-unsafe-swiftshader")
driver = webdriver.Chrome(options=options)

# === Popup Closing Function ===
def attempt_close_popups(driver):
    popups_to_try = [
        '//*[@id="onesignal-slidedown-cancel-button"]',
        '//*[@id="dismiss-button"]',
        '//button[text()="Close"]'
    ]

    popup_closed = False

    for xpath in popups_to_try:
        try:
            print(f"Trying to close popup with XPath: {xpath}")
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            close_button.click()
            print(f"Popup closed with XPath: {xpath}")
            popup_closed = True
            time.sleep(2)
            return
        except:
            print(f"No popup or unable to click popup with XPath: {xpath}")

    # Handle Google Ads iframe
    try:
        print("Checking for Google Ads iframe...")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "google_esf"))
        )
        driver.switch_to.frame("google_esf")
        print("Switched into Google Ads iframe.")

        try:
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="Close"]'))
            )
            close_button.click()
            print("Google Ad closed via button.")
            popup_closed = True
        except:
            print("Close button not clickable. Removing iframe via JS.")

        driver.switch_to.default_content()

    except Exception as e:
        print(f"No google_esf iframe or failed to handle it: {e}")
        driver.switch_to.default_content()

    if not popup_closed:
        print("Attempting to forcibly remove ad popups using JS...")
        try:
            driver.execute_script("""
                const adFrame = document.getElementById("google_esf");
                if (adFrame) adFrame.remove();
            """)
            print("Google ad iframe forcibly removed.")
        except Exception as e:
            print(f"Final JS removal failed: {e}")

# === Close Initial Popup ===
def close_initial_popup(driver):
    attempt_close_popups(driver)

# === Search Jobs ===
def search_jobs(driver, job_title):
    try:
        print("Searching for jobs...")
        search_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="search-key"]'))
        )
        search_box.clear()
        search_box.send_keys(job_title)
        search_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="search-but"]'))
        )
        search_button.click()
        print("Search initiated. Waiting for page...")
        time.sleep(15)
        driver.refresh()
        time.sleep(30)
        attempt_close_popups(driver)
        driver.refresh()
        time.sleep(30)
        attempt_close_popups(driver)
    except Exception as e:
        print(f"Error during job search: {e}")

# === Extract Job Details ===
def extract_job_details(driver, job_title):
    try:
        print("Extracting job details...")
        titles = driver.find_elements(By.XPATH, '//*[@id="printable"]/div[2]/p')
        job_description = ""

        for i, title in enumerate(titles):
            job_description += title.text + "\n"
            list_items = driver.find_elements(By.XPATH, f'//*[@id="printable"]/div[2]/ul[{i+1}]/li')
            for item in list_items:
                job_description += item.text + "\n"
            job_description += "\n"

        try:
            additional_info = driver.find_element(By.XPATH, '//*[@id="printable"]/div[4]').text
        except:
            additional_info = "No additional information available."

        return {"Title": job_title, "Description": job_description.strip(), "Date": additional_info}
    except Exception as e:
        print(f"Error extracting job details: {e}")
        return {}

# === Save to Excel ===
def save_to_excel(job_list, folder_name="proj"):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    file_name = f"job_listings_{timestamp}.xlsx"
    df = pd.DataFrame(job_list)
    df.to_excel(os.path.join(folder_name, file_name), index=False)
    print(f"Job listings saved to {file_name} in the {folder_name} folder.")

# === Retry Wrapper ===
def execute_with_retry(step_function, *args, **kwargs):
    start_time = time.time()
    while True:
        try:
            step_function(*args, **kwargs)
            break
        except Exception as e:
            print(f"Error: {e}. Retrying after refresh...")
            driver.refresh()
            time.sleep(30)
            attempt_close_popups(driver)
            if time.time() - start_time > 90:
                print("Step took too long. Skipping...")
                break

# === Placeholder Login ===
def login(driver):
    try:
        print("Attempting to log in...")
        print("Logged in successfully!")
    except Exception as e:
        print(f"Error during login: {e}")

# === Placeholder Logout ===
def logout(driver):
    try:
        print("Attempting to log out...")
        print("Logged out successfully!")
    except Exception as e:
        print(f"Error during logout: {e}")

# === Navigate to Main ===
def navigate_back_and_refresh(driver, url):
    driver.get(url)
    print("Navigated back to the main page.")
    time.sleep(30)
    attempt_close_popups(driver)

# === Main Execution ===
try:
    url = "https://www.myjobmag.co.ke/"
    driver.get(url)
    print("Page loaded. Waiting for content...")
    time.sleep(30)
    attempt_close_popups(driver)

    execute_with_retry(close_initial_popup, driver)
    execute_with_retry(login, driver)
    execute_with_retry(search_jobs, driver, "data analyst")

    job_list = []

    job_xpaths = [
        '//*[@id="cat-left-sec"]/ul/li[1]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[2]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[4]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[5]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[6]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[7]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[9]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[10]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[11]/ul/li[2]/ul/li[1]/h2/a',
        '//*[@id="cat-left-sec"]/ul/li[12]/ul/li[2]/ul/li[1]/h2/a'
    ]

    for i, xpath in enumerate(job_xpaths, start=1):
        attempt = 0
        max_attempts = 3
        job_successfully_extracted = False

        while attempt < max_attempts and not job_successfully_extracted:
            try:
                print(f"Attempting to click on job {i} (Attempt {attempt + 1})...")

                if attempt >= 1:
                    print("Waiting 20 seconds before retry...")
                    time.sleep(20)

                job_element = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                job_title = job_element.text
                job_element.click()
                print("Job clicked.")
                time.sleep(10)

                driver.refresh()
                time.sleep(30)
                attempt_close_popups(driver)

                if attempt >= 1:
                    print("Waiting another 20 seconds before retry click...")
                    time.sleep(20)

                job_element = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                job_element.click()
                print("Second click done.")
                time.sleep(10)

                attempt_close_popups(driver)

                job_details = extract_job_details(driver, job_title)

                if job_details and job_details.get("Description"):
                    job_list.append(job_details)
                    print(f"✅ Successfully extracted job details for job {i}.")
                    job_successfully_extracted = True
                else:
                    raise Exception("Empty job description returned.")

            except Exception as e:
                print(f"❌ Error processing job {i}, attempt {attempt + 1}: {e}")
                attempt += 1
                driver.refresh()
                time.sleep(30)
                attempt_close_popups(driver)

        if not job_successfully_extracted:
            print(f"⚠️ Failed to extract job {i} after {max_attempts} attempts.")

        execute_with_retry(logout, driver)
        execute_with_retry(login, driver)
        navigate_back_and_refresh(driver, url)
        driver.refresh()
        time.sleep(30)
        attempt_close_popups(driver)
        execute_with_retry(search_jobs, driver, "data analyst")
        driver.refresh()
        time.sleep(30)
        attempt_close_popups(driver)

    save_to_excel(job_list)

finally:
    driver.quit()
