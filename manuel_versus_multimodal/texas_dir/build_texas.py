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
        
        name_element = soup.select_one('div.views-field-title span.field-content')
        name = name_element.get_text(strip=True) if name_element else 'Unavailable'

        position_element = soup.select_one('div.views-field-field-contact-faculty-title div.field-content')
        position = position_element.get_text(strip=True) if position_element else 'Unavailable'

        # research_interests_element = soup.select_one('div.views-field-field-research-areas div.field-content')
        # research_interests = research_interests_element.get_text(strip=True) if research_interests_element else 'none'
        
        research_interests_element = soup.select_one('div.views-field-field-research-areas')
        if research_interests_element:
            research_interests = []
            for link in research_interests_element.select('a'):
                interest = link.get_text(strip=True)
                if interest:
                    research_interests.append(interest)
            research_interests = ', '.join(research_interests)
        else:
            research_interests = 'none'

        faculty_info = {
            'name': name,
            'position': position,
            'research_interests': research_interests,
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
        
    ]

    # Define the XPath selectors for elements to remove
    xpaths_to_remove = ["/html/body/div[2]/div[6]/div/div[3]/div/div/ul", "/html/body/div[2]/div[5]/div/div[3]/div/div[1]" ,"/html/body/div[2]/div[5]/div/div[2]/div/div[1]/form/div/div", "/html/body/div[2]/div[5]/div/article/div/div", "/html/body/div[2]/div[5]/div/div[1]/ul", "/html/body/div[2]/div[2]/header/nav/div[2]/div/ul", "/html/body/div[2]/div[4]", "/html/body/div[2]/div[5]/div/div[1]/ul", "/html/body/div[2]/div[5]/div/article/div/div/div/div/div[1]/p", "/html/body/div[2]/div[5]/div/article/div/div/div/div/div[2]", "/html/body/div[2]/div[5]/div/div[2]/div/div[1]/form/div/div", "/html/body/div[2]/div[6]", "/html/body/div[2]/div[5]/div/div[3]/div/div[1]/h2", "/html/body/div[2]/div[5]/div/div[1]", "/html/body/div[2]/div[2]/header/div[2]/nav[1]/div/div[2]/p/a", "/html/body/div[2]/div[5]/div/article/div/div/div/div/div[2]", "/html/body/div[2]/div[5]/div/div[1]/ul", "/html/body/div[2]/div[5]/div/article", "/html/body/div[2]/div[5]/div/div[3]/div/div[1]", "/html/body/div[2]/div[6]", "/html/body/div[2]/div[6]/div", "/html/body/div[2]/div[5]/div/div[1]" , "/html/body/div[2]/div[5]/div/article", "/html/body/div[2]/div[5]/div/div[2]"]
    remove_unwanted_elements(driver, xpaths_to_remove)
    remove_names(driver, names_to_exclude)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    faculty_sections = []
    
    view_content_divs = soup.select('div.view-content')
    for view_content_div in view_content_divs:
        faculty_sections.extend(view_content_div.select('div.faculty-and-researchers'))
    
    total_faculty = len(faculty_sections)
    start_index = 0

    while start_index < total_faculty:
        end_index = min(start_index + num_faculty, total_faculty)
        batch_dir = os.path.join(output_dir, f"batch_{start_index + 1}-{end_index}")
        os.makedirs(batch_dir, exist_ok=True)

        # Hide all non-batch faculty sections
        for i in range(total_faculty):
            element = driver.find_elements(By.CSS_SELECTOR, 'div.faculty-and-researchers')[i]
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
            element = driver.find_elements(By.CSS_SELECTOR, 'div.faculty-and-researchers')[i]
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