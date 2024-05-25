import argparse
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time

def capture_webpage(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument("--start-maximized")  # Start maximized to capture as much as possible initially
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    time.sleep(2)
    return driver

def remove_unwanted_elements(driver, xpaths):
    try:
        for xpath in xpaths:
            elements = driver.find_elements(By.XPATH, xpath)
            for element in elements:
                driver.execute_script("arguments[0].remove();", element)
    except Exception as e:
        print(f"Error removing sections using XPath {xpath}: {e}")

def save_fullpage_screenshot(driver, output_path):
    # Attempt to capture the entire page by scrolling and taking a screenshot
    original_size = driver.get_window_size()
    required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(required_width, required_height)
    driver.save_screenshot(output_path) 
    driver.set_window_size(original_size['width'], original_size['height'])  # Revert back to original dimensions

def extract_faculty_info(section):

    try:
        soup = BeautifulSoup(str(section), 'html.parser')
        
        h3_tag = soup.find('h3')
        
        if h3_tag:
            # Extract position from the <b> tag and then remove it from the <h3> tag
            position = h3_tag.find('b').get_text(strip=True) if h3_tag.find('b') else 'Unavailable'
            # Remove the <b> tag to isolate the name
            if h3_tag.find('b'):
                h3_tag.find('b').extract()  # This removes the <b> tag from the h3_tag
            name = h3_tag.get_text(strip=True)
        else:
            name = 'Unavailable'
            position = 'Unavailable'
        
        
        faculty_info = {
            'name': name,
            'position': position,
            'research_interests': 'none',
            'email': 'none',
            'phone': 'none'
        }
        return faculty_info
    except Exception as e:
        print(f"Error extracting faculty info: {e}")
        return None

def remove_names(driver, names_to_exclude):
    script = """
    var namesToExclude = arguments[0];
    document.querySelectorAll('.people_img h5').forEach(function(nameElement) {
        var nameText = nameElement.textContent.trim();
        if (namesToExclude.includes(nameText)) {
            var parentElement = nameElement.closest('li');
            if (parentElement) {
                parentElement.remove();
            }
        }
    });
    """
    driver.execute_script(script, names_to_exclude)


def main(url, num_faculty, output_dir):
    driver = capture_webpage(url)

    names_to_exclude = [
        "Yonatan Aljadeff", "Mohit Melwani Daswani", "Cosmin Deaconu", "Tiansong Deng",
        "Lizhi Dong", "Ander Simón Estévez", "Michel Fruchart", "Han Fu", "Toshihiro Fujii",
        "Anne Gambrel", "Christina Gao", "Varda Hagh", "Ryo Hanai", "Bob Harmon",
        "Katie Harrington", "Kabir Husain", "Grayson Jackson", "Bryan Lau", "Chieh Lin",
        "Michael McDonald", "Lauren McGough", "Eric Oberla", "Jacques Pienaar", "Alexandra Rahlin",
        "Kevin Singh", "Zhiqiang Wang", "Siwei Wang", "Setiawan Wenming", "Jonathan Winkelman", "Christina Gao", "Gaurav Chaudhary",
    ]

    # Define the XPath selectors for elements to remove
    xpaths_to_remove = ["/html/body/div[1]/div/div[3]/div[2]", "/html/body/div[1]/header", "/html/body/footer", "/html/body/div[1]/div/div[2]/div/h1"]
    remove_unwanted_elements(driver, xpaths_to_remove)
    remove_names(driver, names_to_exclude)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    faculty_sections = soup.select('li.mix')
    
    total_faculty = len(faculty_sections)
    start_index = 0

    while start_index < total_faculty:
        end_index = min(start_index + num_faculty, total_faculty)
        batch_dir = os.path.join(output_dir, f"batch_{start_index + 1}-{end_index}")
        os.makedirs(batch_dir, exist_ok=True)

        # Hide all non-batch faculty sections
        for i in range(total_faculty):
            element = driver.find_elements(By.CSS_SELECTOR, 'li.mix')[i]
            driver.execute_script("arguments[0].style.display = '{}';".format("none" if i < start_index or i >= end_index else "block"), element)

        # Process faculty data
        batch_sections = faculty_sections[start_index:end_index]
        faculty_data = [extract_faculty_info(section) for section in batch_sections if extract_faculty_info(section)]
        json_path = os.path.join(batch_dir, 'faculty_info.json')
        with open(json_path, 'w') as file:
            json.dump(faculty_data, file, ensure_ascii=False, indent=4)

        # Take a screenshot of the modified webpage
        screenshot_path = os.path.join(batch_dir, 'fullpage_screenshot.png')
        save_fullpage_screenshot(driver, screenshot_path)

        # Restore all sections if needed
        for i in range(total_faculty):
            element = driver.find_elements(By.CSS_SELECTOR, 'li.mix')[i]
            driver.execute_script("arguments[0].style.display = 'block';", element)

        start_index = end_index

    driver.quit()
    print(f"Faculty information extracted and saved in '{output_dir}'.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract faculty information from a webpage.')
    parser.add_argument('url', type=str, help='URL of the webpage')
    parser.add_argument('num_faculty', type=int, help='Number of faculty members to extract per batch')
    parser.add_argument('output_dir', type=str, help='Output directory to save the extracted information')
    args = parser.parse_args()

    main(args.url, args.num_faculty, args.output_dir)
