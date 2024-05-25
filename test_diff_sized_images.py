import argparse
import os
from selenium import webdriver
from time import sleep
from utils_webarena import fetch_browser_info, fetch_page_accessibility_tree, parse_accessibility_tree, clean_accesibility_tree
import multiprocessing
from utils import resize_image, encode_image
import csv
import logging
from PIL import Image
import time
from datetime import datetime
from logging.handlers import QueueHandler
import json
from openai import OpenAI
import base64
import io

config_api_key = None
with open("/Users/jasonz/web_voyager_repo/WebVoyager/config.json", "r") as file:
    api_key_data = json.load(file)
    config_api_key = api_key_data["api_key"]

def capture_webpage(args):
    url, output_dir, webpage_index, size = args
    
    try:
        # Create a directory for the webpage and size
        webpage_dir = os.path.join(output_dir, f"webpage_{webpage_index}", f"size_{size[0]}x{size[1]}")
        os.makedirs(webpage_dir, exist_ok=True)
        
        # Set the Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # Run in headless mode for servers
        chrome_options.add_argument(f"--window-size={size[0]},{size[1]}")

        # Initialize the Chrome WebDriver
        driver = webdriver.Chrome(options=chrome_options)

        # Navigate to the URL
        driver.get(url)
        sleep(1)  # Wait for page to load


        # Save the full HTML of the webpage
        full_html = driver.page_source
        full_html_path = os.path.join(webpage_dir, "full_html.html")
        with open(full_html_path, "w", encoding="utf-8") as file:
            file.write(full_html)
        logging.info(f"Full HTML of webpage {webpage_index} saved to {full_html_path}")

        # Get the total height of the page
        total_height = driver.execute_script("return document.body.scrollHeight")

        # Calculate the overlap between viewports
        overlap = size[1] // 4

        # Initialize variables for scrolling and capturing
        current_position = 0
        viewport_count = 1

        # Create a dictionary to store webpage metadata
        webpage_metadata = {
            "url": url,
            "total_height": total_height,
            "viewport_count": 0,
            "size": size
        }

        while current_position < total_height:
            # Scroll to the current position
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            sleep(0.2)  # Wait for the page to load after scrolling

            # Create a directory for the current viewport
            viewport_dir = os.path.join(webpage_dir, f"viewport_{viewport_count}")
            os.makedirs(viewport_dir, exist_ok=True)

            # Capture and save the screenshot for the current viewport
            screenshot_path = os.path.join(viewport_dir, "screenshot.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot for viewport {viewport_count} of webpage {webpage_index} with size {size} saved to {screenshot_path} at {datetime.now()}")

            # Update the current position and viewport count
            current_position += size[1] - overlap
            viewport_count += 1

        # Update the viewport count in webpage metadata
        webpage_metadata["viewport_count"] = viewport_count - 1

        # Save the webpage metadata as a JSON file
        metadata_path = os.path.join(webpage_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(webpage_metadata, f)

    except Exception as e:
        logging.error(f"Error capturing webpage {webpage_index} (URL: {url}) with size {size}. Error: {str(e)}")

    finally:
        # Clean up
        driver.quit()

def worker_init(log_queue):
    queue_handler = QueueHandler(log_queue)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(queue_handler)


def listener_process(log_queue, log_file_path):
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

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


def call_gpt4_api(gpt_args, openai_client, messages):
    try:
        openai_response = openai_client.chat.completions.create(
                    model=gpt_args['model'], messages=messages, seed=gpt_args['seed'], max_tokens=1000)
        return openai_response

    except Exception as e:
        logging.error(f'An error occurred: {e}')
        return None

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def extract_information(args):
    webpage_dir, prompt = args

    if not os.path.exists(webpage_dir):
        logging.error(f"Webpage directory does not exist: {webpage_dir}. Function will return.")
        return

     # Save the prompt in the webpage directory
    prompt_path = os.path.join(webpage_dir, "prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as file:
        file.write(prompt)
    logging.info(f"Prompt saved to {prompt_path}")

    # Iterate over each size directory within the webpage directory
    for size_dir in [d for d in os.listdir(webpage_dir) if d.startswith("size_")]:
        size_path = os.path.join(webpage_dir, size_dir)

        # Iterate over each viewport directory within the size directory
        for viewport_dir in [d for d in os.listdir(size_path) if d.startswith("viewport_")]:
            viewport_path = os.path.join(size_path, viewport_dir)

            try:
                # Load the screenshot
                screenshot_path = os.path.join(viewport_path, "screenshot.png")

                # Convert PNG to JPEG and resize the image
                jpeg_path = os.path.join(viewport_path, "screenshot.jpg")
                try:
                    with Image.open(screenshot_path) as img:
                        # Resize the image while maintaining the aspect ratio
                        img.thumbnail((1024, 1024))
                        
                        # Compress the image with a lower quality setting
                        img = img.convert('RGB')
                        img_buffer = io.BytesIO()
                        img.save(img_buffer, format='JPEG', quality=85)
                        img_buffer.seek(0)
                        
                        # Save the resized and compressed image
                        with open(jpeg_path, 'wb') as f:
                            f.write(img_buffer.getvalue())
                        
                except Exception as e:
                    logging.warning(f"Failed to convert PNG to JPEG and resize for viewport: {viewport_dir}. Error: {str(e)}")
                    continue

                # Encode the image as base64
                try:
                    encoded_image = encode_image(jpeg_path)
                except Exception as e:
                    logging.warning(f"Failed to encode image as base64 for viewport: {viewport_dir}. Error: {str(e)}")
                    continue

                messages = [
                    {"role": "system", "content": "You are an AI assistant that can analyze images and extract relevant information based on a given prompt."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"{prompt}"},
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
                        response = call_gpt4_api(gpt_args, client, messages)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture webpage screenshots in different sizes.")
    parser.add_argument("--urls", type=str, nargs="+", help="The URLs of the webpages to capture.")
    parser.add_argument("--csv", type=str, help="Path to the CSV file containing URLs.")
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
    log_file_path = os.path.join(args.output_dir, 'program.log')

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

    # Create a pool of worker processes with initializer and initargs
    pool = multiprocessing.Pool(initializer=worker_init, initargs=(log_queue,))

    # Define the different image sizes
    sizes = [(800, 600), (1024, 768), (1366, 768), (1920, 1080), (2560, 1440)]

    # Prepare the arguments for each webpage and size combination
    webpage_args = [(url, args.output_dir, index + 1, size) for index, url in enumerate(urls) for size in sizes]

    # Run the capture_webpage function in parallel for each webpage and size combination
    pool.map(capture_webpage, webpage_args)

    # Close the pool
    pool.close()
    pool.join()

    logging.info(f"Capture completed at {datetime.now()}")

    # Extract information with GPT-4
    prompt = """Analyze the provided section or screenshot of the e-commerce product page and extract the relevant information based on the visible content. Note that the information might be partial or spread across multiple sections of the page.

    Identify which part of the page the current image or section represents and extract the available information accordingly. If any of the requested details are not present in the current image or section, mention that in your response or use null for the respective field.

    Please provide the extracted information in a structured JSON format, organizing the data into appropriate fields and using null for any missing or unavailable information.

    The information to extract includes:

    1. Product details:
    - Product title
    - Product category or type
    - Brand or manufacturer
    - Specifications or key features

    2. Pricing and availability:
    - Current price
    - Discounts or promotions
    - Stock availability
    - Shipping options or delivery estimates

    3. Images and multimedia:
    - Number of product images or videos
    - Description of the main product image or video
    - Presence of image galleries, 360-degree views, or interactive media

    4. Ratings and reviews:
    - Average rating
    - Total number of customer reviews
    - Notable or highlighted customer reviews

    5. Page layout and design:
    - Overall layout and design of the page
    - Prominent calls-to-action (CTAs) or buttons
    - Related products or recommended items

    6. Detailed customer reviews:
    - Number of reviews displayed on the current section
    - For each visible review:
        - Reviewer name or username
        - Rating given by the reviewer
        - Date of the review
        - Review title or summary
        - Full text of the review
    - Common themes or topics mentioned in the visible reviews
    - Specific pros, cons, or feedback mentioned in the visible reviews

    Output the extracted information in the following JSON format:

    {
    "page_section": "<identified_page_section>",
    "product_details": {
        "title": "<product_title>",
        "category": "<product_category>",
        "brand": "<product_brand>",
        "specifications": [
        "<spec_1>",
        "<spec_2>",
        ...
        ]
    },
    "pricing_and_availability": {
        "price": "<current_price>",
        "discounts": "<discount_details>",
        "stock": "<stock_status>",
        "shipping": "<shipping_details>"
    },
    "images_and_multimedia": {
        "image_count": <image_count>,
        "main_image": "<main_image_description>",
        "image_gallery": <image_gallery_available>,
        "interactive_media": "<interactive_media_details>"
    },
    "ratings_and_reviews": {
        "average_rating": <average_rating>,
        "review_count": <review_count>,
        "highlighted_reviews": [
        "<review_1>",
        "<review_2>",
        ...
        ]
    },
    "page_layout_and_design": {
        "layout": "<page_layout_description>",
        "ctas": [
        "<cta_1>",
        "<cta_2>",
        ...
        ],
        "related_products": "<related_products_details>"
    },
    "detailed_customer_reviews": {
        "reviews_on_page": <review_count_on_page>,
        "reviews": [
        {
            "reviewer": "<reviewer_1>",
            "rating": <rating_1>,
            "date": "<review_date_1>",
            "title": "<review_title_1>",
            "text": "<review_text_1>"
        },
        {
            "reviewer": "<reviewer_2>",
            "rating": <rating_2>,
            "date": "<review_date_2>",
            "title": "<review_title_2>",
            "text": "<review_text_2>"
        },
        ...
        ],
        "common_themes": [
        "<theme_1>",
        "<theme_2>",
        ...
        ],
        "pros_and_cons": {
        "pros": [
            "<pro_1>",
            "<pro_2>",
            ...
        ],
        "cons": [
            "<con_1>",
            "<con_2>",
            ...
        ]
        }
    }
    }

    If the image does not appear to be a section of an e-commerce product page or if no relevant information can be extracted, output:

    {
    "error": "Not a valid e-commerce product page section or insufficient information available."
    }
    """

    # extraction_args = [(os.path.join(args.output_dir, f"webpage_{index+1}"), prompt) for index, _ in enumerate(urls)]

    # # Run the extract_information function in parallel for each webpage
    # pool = multiprocessing.Pool(initializer=worker_init, initargs=(log_queue,))
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
