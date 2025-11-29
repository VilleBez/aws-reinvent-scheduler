#!/usr/bin/env python3
"""
HTML Analysis script for AWS re:Invent event catalog
This script will crawl the page and save HTML for analysis
"""

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config


def setup_driver():
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    
    # Don't run headless so we can see what's happening
    # chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        print("✅ Chrome WebDriver initialized successfully")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize Chrome WebDriver: {e}")
        return None


def apply_venue_filter(driver):
    """Apply venue filter to show only Caesars Forum, Venetian, Wynn"""
    print("🏢 Applying venue filter...")
    
    try:
        # Look for filter options
        filter_selectors = [
            "button[aria-label*='filter']",
            "button[aria-label*='Filter']",
            ".filter-button",
            "[data-test*='filter']",
            "button:contains('Filter')",
            "button:contains('Filters')"
        ]
        
        filter_button = None
        for selector in filter_selectors:
            try:
                filter_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found filter button with selector: {selector}")
                break
            except TimeoutException:
                continue
        
        if not filter_button:
            # Try XPath approach
            try:
                filter_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Filter') or contains(text(), 'filter')]")
                print("✅ Found filter button with XPath")
            except NoSuchElementException:
                print("⚠️ Could not find filter button")
                return False
        
        # Click filter button
        filter_button.click()
        time.sleep(2)
        
        # Look for venue filter options
        venue_options = ["Caesars Forum", "Venetian", "Wynn"]
        
        for venue in venue_options:
            try:
                # Try different selectors for venue checkboxes
                venue_selectors = [
                    f"input[value*='{venue}']",
                    f"label:contains('{venue}') input",
                    f"[data-value*='{venue}']"
                ]
                
                venue_checkbox = None
                for selector in venue_selectors:
                    try:
                        venue_checkbox = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                if not venue_checkbox:
                    # Try XPath
                    venue_checkbox = driver.find_element(By.XPATH, f"//label[contains(text(), '{venue}')]//input | //input[@value='{venue}']")
                
                if venue_checkbox and not venue_checkbox.is_selected():
                    venue_checkbox.click()
                    print(f"✅ Selected venue: {venue}")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"⚠️ Could not select venue {venue}: {e}")
        
        # Apply filter
        apply_selectors = [
            "button[type='submit']",
            "button:contains('Apply')",
            "button:contains('Search')",
            ".apply-filter"
        ]
        
        for selector in apply_selectors:
            try:
                apply_button = driver.find_element(By.CSS_SELECTOR, selector)
                apply_button.click()
                print("✅ Applied venue filter")
                time.sleep(3)
                return True
            except NoSuchElementException:
                continue
        
        print("⚠️ Could not find apply button")
        return False
        
    except Exception as e:
        print(f"⚠️ Error applying venue filter: {e}")
        return False


def expand_all_content(driver):
    """Expand all content by clicking 'Show more' buttons"""
    print("📈 Expanding all content...")
    
    max_attempts = 10
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        print(f"🔄 Expansion attempt {attempts}/{max_attempts}")
        
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Look for "Show more" buttons
        show_more_selectors = [
            "button[data-test='rf-button-learn-more']",
            "button.show-more-btn",
            "button:contains('Show more')",
            "button:contains('Load more')"
        ]
        
        found_button = False
        for selector in show_more_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        button_text = button.text.lower()
                        if 'show more' in button_text or 'load more' in button_text:
                            print(f"✅ Clicking 'Show more' button")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", button)
                            found_button = True
                            time.sleep(3)
                            break
                if found_button:
                    break
            except Exception as e:
                continue
        
        if not found_button:
            # Try XPath
            try:
                button = driver.find_element(By.XPATH, "//span[@data-test='button-text' and contains(text(), 'Show more')]/parent::button")
                if button.is_displayed() and button.is_enabled():
                    print("✅ Found 'Show more' button with XPath")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", button)
                    found_button = True
                    time.sleep(3)
            except Exception as e:
                pass
        
        if not found_button:
            print("✅ No more 'Show more' buttons found - content fully expanded")
            break
    
    print(f"📈 Content expansion completed after {attempts} attempts")


def analyze_page_structure(driver):
    """Analyze the page structure and save HTML"""
    print("🔍 Analyzing page structure...")
    
    # Get page source
    html_content = driver.page_source
    
    # Save full HTML
    html_file = 'data/aws_reinvent_page.html'
    os.makedirs('data', exist_ok=True)
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"💾 Saved full HTML to {html_file}")
    
    # Parse with BeautifulSoup for analysis
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find potential session elements
    print("\n🔍 Analyzing potential session elements...")
    
    # Look for elements that might contain session information
    potential_selectors = [
        'div[class*="session"]',
        'div[class*="event"]',
        'div[class*="item"]',
        'article',
        'li[class*="item"]',
        '.title-text',
        'div[data-test*="component"]'
    ]
    
    analysis_results = {}
    
    for selector in potential_selectors:
        elements = soup.select(selector)
        if elements:
            analysis_results[selector] = {
                'count': len(elements),
                'sample_html': str(elements[0])[:500] + '...' if elements else '',
                'sample_text': elements[0].get_text(strip=True)[:200] + '...' if elements else ''
            }
    
    # Save analysis results
    analysis_file = 'data/html_analysis.txt'
    with open(analysis_file, 'w', encoding='utf-8') as f:
        f.write("AWS re:Invent HTML Structure Analysis\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Page Title: {soup.title.string if soup.title else 'N/A'}\n")
        f.write(f"Page URL: {driver.current_url}\n\n")
        
        for selector, data in analysis_results.items():
            f.write(f"Selector: {selector}\n")
            f.write(f"Count: {data['count']}\n")
            f.write(f"Sample Text: {data['sample_text']}\n")
            f.write(f"Sample HTML: {data['sample_html']}\n")
            f.write("-" * 30 + "\n\n")
    
    print(f"💾 Saved analysis results to {analysis_file}")
    
    # Print summary
    print("\n📊 Analysis Summary:")
    for selector, data in analysis_results.items():
        if data['count'] > 0:
            print(f"  {selector}: {data['count']} elements")
    
    return analysis_results


def main():
    """Main function"""
    print("🔍 Starting HTML analysis for AWS re:Invent...")
    
    driver = setup_driver()
    if not driver:
        print("❌ Could not initialize WebDriver")
        return False
    
    try:
        # Navigate to the event catalog
        print(f"📍 Navigating to: {Config.LOGIN_URL}")
        driver.get(Config.LOGIN_URL)
        time.sleep(5)
        
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
        # Check if login is required
        if 'login' in driver.current_url.lower():
            print("🔐 Login required - please login manually in the browser")
            input("Press Enter after you have logged in and reached the event catalog...")
        
        # Apply venue filter
        apply_venue_filter(driver)
        
        # Expand all content
        expand_all_content(driver)
        
        # Analyze page structure
        analysis_results = analyze_page_structure(driver)
        
        print("\n✅ HTML analysis completed successfully!")
        print("📁 Files created:")
        print("  - data/aws_reinvent_page.html (full page HTML)")
        print("  - data/html_analysis.txt (structure analysis)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False
        
    finally:
        print("🔒 Closing browser...")
        driver.quit()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)