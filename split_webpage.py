import argparse
from logging.handlers import QueueHandler
import os
from selenium import webdriver
from time import sleep
from utils_webarena import fetch_browser_info, fetch_page_accessibility_tree, parse_accessibility_tree, clean_accesibility_tree
from multiprocessing import Pool
import multiprocessing
from utils import resize_image, encode_image
import csv
from openai import OpenAI
import base64
import requests
import json
import logging
from PIL import Image
import time
from datetime import datetime

config_api_key = None
with open("/Users/jasonz/web_voyager_repo/WebVoyager/config.json", "r") as file:
    api_key_data = json.load(file)
    config_api_key = api_key_data["api_key"]



def call_gpt4v_api(gpt_args, openai_client, messages):
    try:
        openai_response = openai_client.chat.completions.create(
                    model=gpt_args['model'], messages=messages, seed=gpt_args['seed'], max_tokens=1000)
        return openai_response

    except Exception as e:
        logging.error(f'An error occurred: {e}')
        return None

def capture_webpage(args):
    url, output_dir, webpage_index = args
    
    try:
        # Create a directory for the webpage
        webpage_dir = os.path.join(output_dir, f"webpage_{webpage_index}")
        os.makedirs(webpage_dir, exist_ok=True)
        
        # Set the window size and scale factor
        window_size = (1366, 768)  # Adjust the size as needed
        scale_factor = 1.0  # Adjust the scale factor as needed

        # Set the Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # Run in headless mode for servers
        chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        chrome_options.add_argument(f"--force-device-scale-factor={scale_factor}")

        # Initialize the Chrome WebDriver
        driver = webdriver.Chrome(options=chrome_options)

        # Navigate to the URL
        driver.get(url)
        sleep(1)  # Wait for page to load

        # Hardcoded to remove click cookie button
        if url == "https://cs.illinois.edu/about/people/all-faculty":
            try:
                # Find the button with the class "onetrust-close-btn-handler" and click it
                button = driver.find_element_by_class_name("onetrust-close-btn-handler")
                button.click()
                sleep(1)  # Wait for the button click to take effect
            except Exception as e:
                logging.warning(f"Failed to click cookie button for URL: {url}. Error: {str(e)}")

        # Get the total height of the page
        total_height = driver.execute_script("return document.body.scrollHeight")

        # Initialize variables for scrolling and capturing
        current_position = 0
        viewport_count = 1

        while current_position < total_height:
            # Scroll to the current position
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            sleep(0.2)  # Wait for the page to load after scrolling

            # Extract the browser info and accessibility tree for the current viewport
            browser_info = fetch_browser_info(driver)
            accessibility_tree = fetch_page_accessibility_tree(browser_info, driver, current_viewport_only=True)
            content, obs_nodes_info = parse_accessibility_tree(accessibility_tree)
            content = clean_accesibility_tree(content)

            # Create a directory for the current viewport
            viewport_dir = os.path.join(webpage_dir, f"viewport_{viewport_count}")
            os.makedirs(viewport_dir, exist_ok=True)

            # Capture and save the screenshot for the current viewport
            screenshot_path = os.path.join(viewport_dir, "screenshot.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot for viewport {viewport_count} of webpage {webpage_index} saved to {screenshot_path} at {datetime.now()}")

            # Save the cleaned accessibility tree as a text file for the current viewport
            accessibility_tree_path = os.path.join(viewport_dir, "accessibility_tree.txt")
            with open(accessibility_tree_path, "w", encoding="utf-8") as file:
                file.write(content)
            logging.info(f"Accessibility tree for viewport {viewport_count} of webpage {webpage_index} saved to {accessibility_tree_path} at {datetime.now()}")

            # Update the current position and viewport count
            current_position += window_size[1]  # Scroll by the window height
            viewport_count += 1

            # Update the total height after scrolling
            total_height = driver.execute_script("return document.body.scrollHeight")

        # Save the full HTML of the webpage
        full_html = driver.page_source
        full_html_path = os.path.join(webpage_dir, "full_html.html")
        with open(full_html_path, "w", encoding="utf-8") as file:
            file.write(full_html)
        logging.info(f"Full HTML of webpage {webpage_index} saved to {full_html_path}")

        # Save the full text of the webpage
        full_text = driver.execute_script("return document.body.innerText;")
        full_text_path = os.path.join(webpage_dir, "full_text.txt")
        with open(full_text_path, "w", encoding="utf-8") as file:
            file.write(full_text)
        logging.info(f"Full text of webpage {webpage_index} saved to {full_text_path}")

    except Exception as e:
        logging.error(f"Error capturing webpage {webpage_index} (URL: {url}). Error: {str(e)}")

    finally:
        # Clean up
        driver.quit()


def extract_information(args):
    webpage_dir, prompt = args

    if not os.path.exists(webpage_dir):
        logging.error(f"Webpage directory does not exist: {webpage_dir}. Function will return.")
        return

    # Iterate over each viewport directory within the webpage directory
    for viewport_dir in [d for d in os.listdir(webpage_dir) if d.startswith("viewport_")]:
        viewport_path = os.path.join(webpage_dir, viewport_dir)

        try:
            # Load the screenshot and accessibility tree
            screenshot_path = os.path.join(viewport_path, "screenshot.png")
            accessibility_tree_path = os.path.join(viewport_path, "accessibility_tree.txt")

            with open(accessibility_tree_path, "r", encoding="utf-8") as file:
                accessibility_tree = file.read()

            # Convert PNG to JPEG
            jpeg_path = os.path.join(viewport_path, "screenshot.jpg")
            try:
                with Image.open(screenshot_path) as img:
                    img.convert('RGB').save(jpeg_path, 'JPEG')
            except Exception as e:
                logging.warning(f"Failed to convert PNG to JPEG for viewport: {viewport_dir}. Error: {str(e)}")
                continue

            # Encode the image as base64
            try:
                encoded_image = encode_image(jpeg_path)
            except Exception as e:
                logging.warning(f"Failed to encode image as base64 for viewport: {viewport_dir}. Error: {str(e)}")
                continue

            messages = [
                {"role": "system", "content": "You are an AI assistant that can analyze images and extract relevant information based on a given prompt and accessibility tree from a webpage."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{prompt}-\n{accessibility_tree}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}",
                            },
                        },
                    ],
                }
            ]

            # Create a client instance
            client = OpenAI(api_key=config_api_key)

            # Define arguments needed for the function call
            gpt_args = {
                'text_only': False,  # Set to True if you only want to process text
                'model': 'gpt-4-turbo-2024-04-09',  # Replace with your model of choice
                'seed': 12,  # Optional, for deterministic results
            }

            # Call the API with retry mechanism
            max_retries = 3
            retry_delay = 2
            for attempt in range(max_retries):
                try:
                    response = call_gpt4v_api(gpt_args, client, messages)
                    if response:
                        extracted_info = response.choices[0].message.content.strip()
                        break
                except Exception as e:
                    logging.warning(f"API request failed for viewport: {viewport_dir}. Attempt {attempt + 1}/{max_retries}. Error: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
            else:
                logging.error(f"API request failed after {max_retries} attempts for viewport: {viewport_dir}. Skipping.")
                continue

            # Save the extracted information to a file
            extraction_output_path = os.path.join(viewport_path, "extraction_output.txt")
            try:
                with open(extraction_output_path, "w", encoding="utf-8") as file:
                    file.write(extracted_info)
                logging.info(f"Extracted information saved to {extraction_output_path} at {datetime.now()}")
            except Exception as e:
                logging.error(f"Failed to save extracted information for viewport: {viewport_dir}. Error: {str(e)}")

        except Exception as e:
            logging.error(f"Error extracting information for viewport: {viewport_dir}. Error: {str(e)}")
    

def worker_init(log_queue):
    # Create a QueueHandler for each worker process
    queue_handler = QueueHandler(log_queue)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(queue_handler)

def listener_process(log_queue, log_file_path):
    # Create a FileHandler and StreamHandler for the listener process
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Create a logger for the listener process
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    while True:
        try:
            record = log_queue.get()
            if record is None:
                break
            logger.handle(record)
        except Exception:
            import sys, traceback
            print('Whoops! Problem:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture webpage screenshots and accessibility trees.")
    parser.add_argument("--urls", type=str, nargs="+", help="The URLs of the webpages to capture.")
    parser.add_argument("--csv", type=str, help="Path to the CSV file containing URLs.")
    #parser.add_argument("--prompt", type=str, required=True, help="Prompt for extracting information")
    parser.add_argument("--output_dir", type=str, help="The directory to save the output.")
    args = parser.parse_args()

    if args.urls:
        urls = args.urls
    elif args.csv:
        with open(args.csv, "r") as file:
            reader = csv.DictReader(file)
            urls = [row["URL"] for row in reader]
    else:
        parser.error("Please provide either URLs using the --urls argument or a CSV file using the --csv argument.")



    # Create the output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Create the log file path based on the output_dir argument
    log_file_path = os.path.join(args.output_dir, 'program.log2')

    # Create a multiprocessing queue for log records
    log_queue = multiprocessing.Queue()

    # Start the listener process
    listener = multiprocessing.Process(target=listener_process, args=(log_queue, log_file_path))
    listener.start()

    # Configure the root logger to use QueueHandler
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    queue_handler = QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    logging.info(f"Program started at {datetime.now()}")
    start_time = time.time()

    # Step 1 getting information from webpages such as accessibility tree and image
    # Create a pool of worker processes with initializer and initargs
    pool = Pool(initializer=worker_init, initargs=(log_queue,))

    # Prepare the arguments for each webpage
    webpage_args = [(url, args.output_dir, index + 1) for index, url in enumerate(urls)]

    # Run the capture_webpage function in parallel for each webpage
    pool.map(capture_webpage, webpage_args)
    

    # Close the pool
    pool.close()
    pool.join()

    logging.info(f"Part1 completed at {datetime.now()}")
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"Total execution time: {execution_time:.2f} seconds")

    # Step 2
    # Extract information with gpt4
    # pool = Pool(initializer=worker_init, initargs=(log_queue,))

    # Prepare the arguments for information extraction
    #extraction_args = [(os.path.join(args.output_dir, f"webpage_{index+1}"), args.prompt) for index, _ in enumerate(urls)]
    prompt = """Find all of the Assistant Professors' names and put them in a list. for example: {[name1, name2, etc]}. The extraction has to have the wording "Assistant Proffesor" in order to be extracted."""
    extraction_args = [(os.path.join(args.output_dir, f"webpage_{index+1}"), prompt) for index, _ in enumerate(urls)]

    # # Run the extract_information function in parallel for each webpage
    # pool.map(extract_information, extraction_args)

    # # Close the pool
    # pool.close()
    # pool.join()

    logging.info(f"Program completed at {datetime.now()}")
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"Total execution time: {execution_time:.2f} seconds")

     # Put a None record to indicate the end of logs
    log_queue.put_nowait(None)
    listener.join()