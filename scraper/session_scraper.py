"""
Session scraper for AWS re:Invent event catalog
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from config import Config
from .data_parser import SessionDataParser


class SessionScraper:
    def __init__(self):
        self.driver = None
        self.parser = SessionDataParser()
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        
        if Config.CHROME_HEADLESS:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Try to use system Chrome first
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(Config.CHROME_TIMEOUT)
            print("✅ Chrome WebDriver initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            print("🔄 Trying alternative ChromeDriver setup...")
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.implicitly_wait(Config.CHROME_TIMEOUT)
                print("✅ Chrome WebDriver initialized with ChromeDriverManager")
            except Exception as e2:
                print(f"❌ All WebDriver initialization attempts failed: {e2}")
                print("⚠️  Running in mock mode - will generate sample data")
                self.driver = None
    
    def login(self):
        """Login to AWS re:Invent registration site"""
        print("🔐 Logging in to AWS re:Invent...")
        
        if not self.driver:
            print("⚠️  Skipping login - running in mock mode")
            return True
        
        try:
            # Navigate to the event catalog page
            print(f"📍 Navigating to: {Config.LOGIN_URL}")
            self.driver.get(Config.LOGIN_URL)
            
            # Wait for page to load
            print("⏳ Waiting for page to load...")
            time.sleep(5)
            
            # Print current URL for debugging
            current_url = self.driver.current_url
            print(f"📍 Current URL: {current_url}")
            
            # Check if we need to login or if we're already at the event catalog
            if 'event-catalog' in current_url.lower() and 'login' not in current_url.lower():
                print("✅ Already at event catalog - no login required")
                return True
            
            # If URL contains 'login', we need to authenticate
            if 'login' in current_url.lower():
                print("🔐 Login page detected - proceeding with authentication...")
            else:
                print("⚠️ Unexpected page - attempting to find login form...")
            
            # Look for login elements
            print("🔍 Looking for login form...")
            
            # Handle cookie consent if present
            try:
                cookie_selectors = [
                    "button[id*='accept']",
                    "button[class*='accept']",
                    "button:contains('Accept')",
                    "button:contains('OK')",
                    "button:contains('Agree')"
                ]
                
                for selector in cookie_selectors:
                    try:
                        cookie_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        print("🍪 Accepting cookies...")
                        cookie_button.click()
                        time.sleep(2)
                        break
                    except TimeoutException:
                        continue
            except:
                pass
            
            # Wait for login form
            wait = WebDriverWait(self.driver, Config.CHROME_TIMEOUT)
            
            # Look for email/username field
            email_selectors = [
                "input[name='email']",
                "input[type='email']",
                "input[name='username']",
                "input[id*='email']",
                "input[id*='username']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    print(f"🔍 Trying email selector: {selector}")
                    email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"✅ Found email field with: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not email_field:
                # Try XPath approach
                try:
                    email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email' or contains(@name, 'email') or contains(@id, 'email')]")))
                    print("✅ Found email field with XPath")
                except TimeoutException:
                    print("❌ Could not find email field")
                    # Print page source for debugging
                    print("📄 Page title:", self.driver.title)
                    print("📄 Page contains 'login':", 'login' in self.driver.page_source.lower())
                    print("📄 Page contains 'email':", 'email' in self.driver.page_source.lower())
                    raise Exception("Could not find email field")
            
            # Enter email
            print("📧 Entering email...")
            email_field.clear()
            email_field.send_keys(Config.REINVENT_EMAIL)
            time.sleep(1)
            
            # Look for password field
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[id*='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    print(f"🔍 Trying password selector: {selector}")
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found password field with: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                try:
                    password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                    print("✅ Found password field with XPath")
                except NoSuchElementException:
                    raise Exception("Could not find password field")
            
            # Enter password
            print("🔑 Entering password...")
            password_field.clear()
            password_field.send_keys(Config.REINVENT_PASSWORD)
            time.sleep(1)
            
            # Look for submit button - AWS Events specific selectors
            submit_selectors = [
                # AWS Events specific button
                "span[data-test='button-text']",
                "button:has(span[data-test='button-text'])",
                ".mdBtnR-text",
                "button:has(.mdBtnR-text)",
                # Generic selectors
                "button[type='submit']",
                "input[type='submit']",
                ".login-button",
                "#login-button",
                "[value='Login']",
                "[value='Sign In']"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    print(f"🔍 Trying submit selector: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and ('login' in element.text.lower() or element.get_attribute('type') == 'submit'):
                            submit_button = element
                            print(f"✅ Found submit button with: {selector}")
                            break
                    if submit_button:
                        break
                except NoSuchElementException:
                    continue
            
            if not submit_button:
                # Try XPath for AWS Events specific button structure
                try:
                    submit_button = self.driver.find_element(By.XPATH, "//span[@data-test='button-text' and contains(text(), 'Login')]/parent::button")
                    print("✅ Found submit button with AWS Events XPath")
                except NoSuchElementException:
                    try:
                        submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign In') or contains(text(), 'Sign in')] | //input[@value='Login' or @value='Sign In']")
                        print("✅ Found submit button with generic XPath")
                    except NoSuchElementException:
                        raise Exception("Could not find submit button")
            
            # Submit the form
            print("🚀 Submitting login form...")
            submit_button.click()
            
            # Wait for login to process
            print("⏳ Waiting for login to process...")
            time.sleep(10)
            
            # Check login result
            current_url = self.driver.current_url
            print(f"📍 Post-login URL: {current_url}")
            
            # Check for successful login indicators
            success_indicators = [
                'event-catalog' in current_url.lower(),
                'dashboard' in current_url.lower(),
                'catalog' in current_url.lower(),
                'events' in current_url.lower()
            ]
            
            if any(success_indicators):
                print("✅ Login successful - redirected to event area")
                return True
            
            # Check if still on login page
            if 'login' in current_url.lower() or 'signin' in current_url.lower():
                # Look for error messages
                error_selectors = [
                    ".error", ".alert-danger", ".alert-error",
                    "[class*='error']", "[class*='alert']",
                    ".message", ".notification"
                ]
                
                error_messages = []
                for selector in error_selectors:
                    try:
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in error_elements:
                            if element.is_displayed() and element.text.strip():
                                error_messages.append(element.text.strip())
                    except:
                        continue
                
                if error_messages:
                    error_text = "; ".join(error_messages)
                    raise Exception(f"Login failed with errors: {error_text}")
                else:
                    raise Exception("Login failed: Still on login page with no error message")
            
            # If we get here, we're not sure about the login status
            print("⚠️ Login status unclear - proceeding with caution")
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            print(f"📍 Final URL: {self.driver.current_url}")
            print(f"📄 Page title: {self.driver.title}")
            raise
    
    def scrape_all_sessions(self):
        """Scrape all session data"""
        if not self.driver:
            print("⚠️  Generating mock session data...")
            return self._generate_mock_sessions()
        
        self.login()
        
        # Navigate to event catalog if not already there
        if 'event-catalog' not in self.driver.current_url.lower():
            catalog_url = Config.LOGIN_URL
            self.driver.get(catalog_url)
            time.sleep(3)
        
        sessions = []
        page = 1
        
        while True:
            print(f"📄 Scraping page {page}...")
            
            page_sessions = self._scrape_current_page()
            if not page_sessions:
                print("No more sessions found, stopping...")
                break
            
            sessions.extend(page_sessions)
            print(f"Found {len(page_sessions)} sessions on page {page}")
            
            # Try to go to next page
            if not self._go_to_next_page():
                print("No more pages available")
                break
            
            page += 1
            time.sleep(2)  # Be respectful to the server
        
        print(f"✅ Total sessions scraped: {len(sessions)}")
        return sessions
    
    def _scrape_current_page(self):
        """Scrape sessions from current page"""
        print("🔍 Analyzing page structure...")
        
        # Wait for page to load
        time.sleep(5)
        
        # Print page info for debugging
        print(f"📄 Page title: {self.driver.title}")
        print(f"📍 Current URL: {self.driver.current_url}")
        
        # Check if we need to handle login first
        if 'login' in self.driver.current_url.lower():
            print("🔐 Detected login page, attempting login...")
            # Try to find and fill login form
            try:
                # Look for email field
                email_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name*='email'], input[id*='email']")
                email_field.clear()
                email_field.send_keys(Config.REINVENT_EMAIL)
                
                # Look for password field
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.clear()
                password_field.send_keys(Config.REINVENT_PASSWORD)
                
                # Submit form
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                submit_button.click()
                
                # Wait for redirect
                time.sleep(10)
                print(f"📍 After login URL: {self.driver.current_url}")
                
            except Exception as e:
                print(f"⚠️ Login attempt failed: {e}")
        
        # First, handle any overlays or blocking elements
        self._handle_blocking_elements()
        
        # Then, expand all content before parsing
        print("🔄 Expanding all content first...")
        self._expand_all_content()
        
        # Try multiple selectors for session elements based on actual AWS re:Invent structure
        # ONLY use session containers, NOT individual elements like .title-text
        session_selectors = [
            # AWS Events specific selectors based on actual HTML structure
            "li.catalog-result.session-result",  # Main session container
            "li.catalog-result",  # Session container (broader match)
            "li[data-session-id]",  # Li elements with session ID
            "li[id*='session-']",  # Li elements with session in ID
            "li[class*='catalog-result']",  # Any li with catalog-result class
        ]
        
        session_elements = []
        for selector in session_selectors:
            try:
                print(f"🔍 Trying selector: {selector}")
                # Use shorter timeout for each attempt
                wait = WebDriverWait(self.driver, 5)
                elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                if elements and len(elements) > 1:  # Need more than 1 element to be meaningful
                    session_elements = elements
                    print(f"✅ Found {len(elements)} elements using selector: {selector}")
                    break
                else:
                    print(f"⚠️ Found {len(elements) if elements else 0} elements with {selector} - too few")
            except TimeoutException:
                print(f"⏰ Timeout for selector: {selector}")
                continue
            except Exception as e:
                print(f"❌ Error with selector {selector}: {e}")
                continue
        
        if not session_elements:
            print("⚠️ No session elements found with any selector")
            print("🔍 Trying to find any clickable elements...")
            
            # Try to find any elements that might be sessions
            try:
                all_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
                clickable_elements = [el for el in all_elements if el.is_displayed() and el.tag_name in ['div', 'article', 'li', 'a']]
                print(f"📊 Found {len(clickable_elements)} potentially relevant elements")
                
                # Look for elements with text content that might be sessions
                potential_sessions = []
                for el in clickable_elements[:50]:  # Check first 50 elements
                    try:
                        text = el.text.strip()
                        if text and len(text) > 20 and any(keyword.lower() in text.lower() for keyword in ['session', 'workshop', 'talk', 'demo', 'keynote']):
                            potential_sessions.append(el)
                    except:
                        continue
                
                if potential_sessions:
                    session_elements = potential_sessions
                    print(f"✅ Found {len(potential_sessions)} potential session elements by content analysis")
                else:
                    print("❌ No potential session elements found")
                    return []
                    
            except Exception as e:
                print(f"❌ Error in fallback element search: {e}")
                return []
        
        sessions = []
        
        for i, element in enumerate(session_elements):
            try:
                print(f"Parsing session {i+1}/{len(session_elements)}...")
                session_data = self.parser.parse_session_element(element)
                if session_data and session_data.get('title'):
                    sessions.append(session_data)
                    print(f"✓ Parsed: {session_data.get('title', 'Unknown')[:50]}...")
                else:
                    print(f"⚠️ Skipped session {i+1} - insufficient data")
            except Exception as e:
                print(f"⚠️ Error parsing session {i+1}: {e}")
                continue
        
        print(f"✅ Successfully parsed {len(sessions)} sessions from expanded content")
        return sessions
    
    def _go_to_next_page(self):
        """Navigate to the next page of results"""
        try:
            # Try different next page selectors
            next_selectors = [
                "a[aria-label='Next']",
                "button[aria-label='Next']",
                ".next-page",
                ".pagination-next",
                "[class*='next']"
            ]
            
            next_button = None
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled() and next_button.is_displayed():
                        break
                except NoSuchElementException:
                    continue
            
            if not next_button:
                # Try XPath for text-based search
                try:
                    next_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Next') or contains(text(), '→')] | //button[contains(text(), 'Next') or contains(text(), '→')]")
                except NoSuchElementException:
                    return False
            
            if next_button and next_button.is_enabled():
                # Scroll to button and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                next_button.click()
                time.sleep(3)  # Wait for page to load
                return True
            else:
                return False
                
        except Exception as e:
            print(f"⚠️ Error navigating to next page: {e}")
            return False
    
    def _handle_load_more(self):
        """Handle 'Load More' buttons for infinite scroll pages"""
        try:
            # AWS re:Invent specific "Show more" button selectors based on actual HTML
            load_more_selectors = [
                "button.mdBtnR.mdBtnR-primary.show-more-btn[data-test='rf-button-learn-more']",  # Exact match
                "button[data-test='rf-button-learn-more']",  # AWS re:Invent specific
                "button.show-more-btn",  # AWS re:Invent specific
                "button.mdBtnR-primary",  # AWS re:Invent button class
                ".mdBtnR.show-more-btn",  # AWS re:Invent specific
                # Generic selectors
                ".load-more",
                "[class*='load-more']",
                "button[class*='show-more']"
            ]
            
            for selector in load_more_selectors:
                try:
                    print(f"🔍 Looking for load more button with: {selector}")
                    load_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in load_more_buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.lower()
                            if 'show more' in button_text or 'load more' in button_text:
                                print(f"✅ Found and clicking 'Show more' button")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(1)
                                button.click()
                                time.sleep(3)
                                return True
                except NoSuchElementException:
                    continue
            
            # Try XPath for AWS re:Invent specific button structure
            try:
                # Match the exact structure: button with class and data-test, containing span with data-test='button-text'
                load_more_button = self.driver.find_element(By.XPATH, "//button[@class='mdBtnR mdBtnR-primary show-more-btn' and @data-test='rf-button-learn-more']//span[@data-test='button-text' and contains(text(), 'Show more')]/..")
                if load_more_button.is_displayed() and load_more_button.is_enabled():
                    print("✅ Found 'Show more' button with exact AWS re:Invent XPath")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                    time.sleep(1)
                    load_more_button.click()
                    time.sleep(3)
                    return True
            except NoSuchElementException:
                # Fallback XPath
                try:
                    load_more_button = self.driver.find_element(By.XPATH, "//span[@data-test='button-text' and contains(text(), 'Show more')]/parent::button")
                    if load_more_button.is_displayed() and load_more_button.is_enabled():
                        print("✅ Found 'Show more' button with fallback XPath")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                        time.sleep(1)
                        load_more_button.click()
                        time.sleep(3)
                        return True
                except NoSuchElementException:
                    pass
            
            # Try generic XPath for text-based search
            try:
                load_more_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Load More') or contains(text(), 'Show More') or contains(text(), 'Show more')]")
                if load_more_button.is_displayed() and load_more_button.is_enabled():
                    print("✅ Found load more button with generic XPath")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                    time.sleep(1)
                    load_more_button.click()
                    time.sleep(3)
                    return True
            except NoSuchElementException:
                pass
            
            print("⚠️ No 'Show more' button found")
            return False
            
        except Exception as e:
            print(f"⚠️ Error handling load more: {e}")
            return False
    
    def _scroll_to_load_content(self):
        """Scroll down to trigger lazy loading"""
        try:
            # Get initial page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(2)
                
                # Calculate new scroll height and compare with last height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    # Try load more button
                    if not self._handle_load_more():
                        break
                
                last_height = new_height
                
        except Exception as e:
            print(f"⚠️ Error during scroll loading: {e}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _generate_mock_sessions(self):
        """Generate mock session data for testing when WebDriver fails"""
        print("🎭 Generating mock session data...")
        
        mock_sessions = []
        keywords = Config.INTEREST_KEYWORDS
        venues = ["Venetian", "Caesars Palace", "Wynn", "Aria", "Bellagio"]
        session_types = ["Breakout Session", "Workshop", "Chalk Talk", "Builder Session"]
        
        # Generate sessions for each day
        for day in range(1, 6):  # Dec 1-5
            date = f"2025-12-0{day}"
            
            # Generate 40-50 sessions per day to ensure enough backups
            import random
            num_sessions = random.randint(40, 50)
            
            for i in range(num_sessions):
                # Random time between 9 AM and 6 PM, avoiding lunch break
                hour = random.randint(9, 17)
                minute = random.choice([0, 30])
                
                # Skip lunch break (11:00-13:00)
                if hour == 11 or (hour == 12):
                    hour = random.choice([9, 10, 13, 14, 15, 16, 17])
                
                start_time = f"{hour:02d}:{minute:02d}"
                
                # Session duration (30, 60, or 90 minutes)
                duration = random.choice([30, 60, 90])
                end_hour = hour + (minute + duration) // 60
                end_minute = (minute + duration) % 60
                end_time = f"{end_hour:02d}:{end_minute:02d}"
                
                # Ensure all keywords are represented
                keyword_index = i % len(keywords)
                keyword = keywords[keyword_index]
                venue = random.choice(venues)
                session_type = random.choice(session_types)
                
                # Create more diverse titles to ensure keyword coverage
                titles = [
                    f"{keyword} in Modern Cloud Architecture - {session_type}",
                    f"Advanced {keyword} Strategies for Enterprise",
                    f"Building Scalable Solutions with {keyword}",
                    f"{keyword} Best Practices and Implementation",
                    f"Deep Dive into {keyword} Technologies"
                ]
                
                session = {
                    'id': f"MOCK{day}{i:03d}",
                    'title': random.choice(titles),
                    'description': f"Deep dive into {keyword.lower()} technologies and best practices for enterprise applications. Learn how to implement scalable solutions using AWS services and {keyword.lower()} methodologies.",
                    'speakers': [f"Expert Speaker {i+1}", f"Senior Architect {i+2}"],
                    'date': date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'venue': venue,
                    'room': f"Room {random.randint(1, 20)}",
                    'session_type': session_type,
                    'level': random.choice(["Beginner", "Intermediate", "Advanced"]),
                    'tags': [keyword.lower(), "aws", "cloud", "architecture"]
                }
                
                mock_sessions.append(session)
        
        print(f"✅ Generated {len(mock_sessions)} mock sessions")
        return mock_sessions
    
    def _handle_blocking_elements(self):
        """Handle cookie banners and other blocking elements"""
        print("🍪 Handling blocking elements...")
        
        # Handle cookie consent banner
        cookie_selectors = [
            "#awsccc-cb-content",  # AWS cookie banner
            ".awsccc-u-btn-primary",  # AWS cookie accept button
            "button[id*='accept']",
            "button[class*='accept']",
            "[data-test*='accept']"
        ]
        
        # Also try XPath for text-based button selection
        cookie_xpath_selectors = [
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'OK')]",
            "//button[contains(text(), 'Agree')]",
            "//button[contains(text(), 'Allow')]"
        ]
        
        # Try CSS selectors first
        for selector in cookie_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        print(f"🍪 Found blocking element: {selector}")
                        # Try to close/accept it
                        if 'btn' in selector or 'button' in selector:
                            element.click()
                            print("✅ Clicked to dismiss blocking element")
                            time.sleep(2)
                        else:
                            # Try to find close button within the element
                            close_buttons = element.find_elements(By.CSS_SELECTOR, "button, .close, [class*='close']")
                            for btn in close_buttons:
                                if btn.is_displayed():
                                    btn.click()
                                    print("✅ Closed blocking element")
                                    time.sleep(2)
                                    break
                        break
            except Exception as e:
                print(f"⚠️ Error handling blocking element {selector}: {e}")
                continue
        
        # Try XPath selectors for text-based buttons
        for xpath in cookie_xpath_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed():
                        print(f"🍪 Found blocking element with XPath: {xpath}")
                        element.click()
                        print("✅ Clicked to dismiss blocking element")
                        time.sleep(2)
                        break
            except Exception as e:
                print(f"⚠️ Error handling blocking element {xpath}: {e}")
                continue
        
        # Handle any modal dialogs
        modal_selectors = [
            ".modal", ".dialog", ".popup", ".overlay",
            "[class*='modal']", "[class*='dialog']", "[class*='popup']"
        ]
        
        for selector in modal_selectors:
            try:
                modals = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for modal in modals:
                    if modal.is_displayed():
                        # Try to find close button
                        close_buttons = modal.find_elements(By.CSS_SELECTOR, ".close, [class*='close'], button[aria-label*='close']")
                        for btn in close_buttons:
                            if btn.is_displayed():
                                btn.click()
                                print("✅ Closed modal dialog")
                                time.sleep(2)
                                break
            except Exception as e:
                continue
        
        print("✅ Finished handling blocking elements")
    
    def _expand_all_content(self):
        """Expand all content by clicking all 'Show more' buttons"""
        print("📈 Starting content expansion process...")
        print(f"📍 Current URL: {self.driver.current_url}")
        print(f"📄 Page title: {self.driver.title}")
        
        max_attempts = 59  # Prevent infinite loops
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            print(f"🔄 Expansion attempt {attempts}/{max_attempts}")
            
            # Scroll to bottom to ensure all content is loaded
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Look for "Show more" buttons
            show_more_found = False
            
            # AWS re:Invent specific "Show more" button selectors
            load_more_selectors = [
                "button.mdBtnR.mdBtnR-primary.show-more-btn[data-test='rf-button-learn-more']",
                "button[data-test='rf-button-learn-more']",
                "button.show-more-btn",
                "button.mdBtnR-primary"
            ]
            
            for selector in load_more_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.lower()
                            if 'show more' in button_text or 'load more' in button_text:
                                print(f"✅ Found 'Show more' button, clicking...")
                                
                                # Scroll to button first
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                time.sleep(1)
                                
                                # Try JavaScript click to avoid interception
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    print("✅ Clicked 'Show more' button with JavaScript")
                                    show_more_found = True
                                    time.sleep(3)  # Wait for content to load
                                    break
                                except Exception as e:
                                    print(f"⚠️ JavaScript click failed: {e}")
                                    # Try regular click as fallback
                                    try:
                                        button.click()
                                        print("✅ Clicked 'Show more' button with regular click")
                                        show_more_found = True
                                        time.sleep(3)
                                        break
                                    except Exception as e2:
                                        print(f"⚠️ Regular click also failed: {e2}")
                    
                    if show_more_found:
                        break
                        
                except Exception as e:
                    print(f"⚠️ Error with selector {selector}: {e}")
                    continue
            
            # Also try XPath approach
            if not show_more_found:
                try:
                    xpath_button = self.driver.find_element(By.XPATH, "//span[@data-test='button-text' and contains(text(), 'Show more')]/parent::button")
                    if xpath_button.is_displayed() and xpath_button.is_enabled():
                        print("✅ Found 'Show more' button with XPath")
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", xpath_button)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", xpath_button)
                        print("✅ Clicked 'Show more' button with XPath + JavaScript")
                        show_more_found = True
                        time.sleep(3)
                except Exception as e:
                    print(f"⚠️ XPath approach failed: {e}")
            
            # If no more "Show more" buttons found, we're done
            if not show_more_found:
                print("✅ No more 'Show more' buttons found - content fully expanded")
                break
        
        print(f"📈 Content expansion completed after {attempts} attempts")