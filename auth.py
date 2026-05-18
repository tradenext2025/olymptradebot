# ─── SELENIUM AUTO LOGIN & TOKEN REFRESH ──────────────────────────────────────
import time
import threading
import json
import os

current_token = None
token_expiry  = 0
_lock         = threading.Lock()

def get_chrome_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Railway/nixpacks chromium path
    for path in ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"]:
        if os.path.exists(path):
            options.binary_location = path
            break

    # Chromedriver path
    for drv in ["/usr/bin/chromedriver", "/usr/local/bin/chromedriver"]:
        if os.path.exists(drv):
            service = Service(drv)
            return webdriver.Chrome(service=service, options=options)

    return webdriver.Chrome(options=options)

def selenium_login(email, password):
    global current_token, token_expiry
    driver = None
    try:
        print("Starting Selenium login...")
        driver = get_chrome_driver()

        # Go to OlympTrade
        driver.get("https://olymptrade.com/platform")
        time.sleep(4)

        # Check if already on platform or needs login
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            # Try to find email input
            wait = WebDriverWait(driver, 10)

            # Click login if needed
            try:
                login_btn = driver.find_element(By.XPATH,
                    "//button[contains(text(),'Log in') or contains(text(),'Login') or contains(text(),'Sign in')]"
                )
                login_btn.click()
                time.sleep(2)
            except:
                pass

            # Enter email
            email_field = wait.until(EC.presence_of_element_located((
                By.XPATH, "//input[@type='email' or @name='login' or @placeholder='Email']"
            )))
            email_field.clear()
            email_field.send_keys(email)
            time.sleep(1)

            # Enter password
            pass_field = driver.find_element(
                By.XPATH, "//input[@type='password' or @name='password']"
            )
            pass_field.clear()
            pass_field.send_keys(password)
            time.sleep(1)

            # Click submit
            submit = driver.find_element(
                By.XPATH, "//button[@type='submit' or contains(text(),'Log in') or contains(text(),'Sign in')]"
            )
            submit.click()
            time.sleep(5)

        except Exception as e:
            print(f"Login form error: {e}")

        # Wait for platform to load
        time.sleep(5)

        # Extract access_token from cookies
        cookies = driver.get_cookies()
        token   = None
        for cookie in cookies:
            if cookie.get("name") == "access_token":
                token = cookie.get("value")
                break

        # Try JavaScript extraction if cookie not found
        if not token:
            try:
                token = driver.execute_script(
                    "return document.cookie.match(/access_token=([^;]+)/)?.[1]"
                )
            except:
                pass

        # Try localStorage
        if not token:
            try:
                token = driver.execute_script(
                    "return localStorage.getItem('access_token')"
                )
            except:
                pass

        if token:
            with _lock:
                current_token = token
                token_expiry  = time.time() + 82800  # 23 hours
            print(f"✅ Selenium login successful! Token obtained.")
            print(f"Token starts: {token[:30]}...")
            return token
        else:
            print("❌ Could not extract token from OlympTrade")
            return None

    except Exception as e:
        print(f"Selenium login error: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def get_valid_token():
    global current_token, token_expiry
    with _lock:
        if current_token and time.time() < token_expiry:
            return current_token
    # Fallback to config token
    from config import OLYMP_TOKEN
    return OLYMP_TOKEN

def start_auto_refresh(email, password):
    def refresh_loop():
        while True:
            try:
                print("Auto-refreshing OlympTrade token...")
                token = selenium_login(email, password)
                if token:
                    # Update websocket with new token
                    try:
                        import websocket_client
                        websocket_client.live_prices    = {}
                        websocket_client.candle_history = {}
                        websocket_client.ws_connected   = False
                    except:
                        pass
                    print("Token refreshed successfully!")
                else:
                    print("Token refresh failed - will retry in 1 hour")
            except Exception as e:
                print(f"Auto refresh error: {e}")
            # Refresh every 23 hours
            time.sleep(82800)

    # First login immediately
    t1 = threading.Thread(target=lambda: selenium_login(email, password), daemon=True)
    t1.start()

    # Then start refresh loop
    t2 = threading.Thread(target=refresh_loop, daemon=True)
    t2.start()
    print("Auto token refresh started - refreshes every 23 hours!")
