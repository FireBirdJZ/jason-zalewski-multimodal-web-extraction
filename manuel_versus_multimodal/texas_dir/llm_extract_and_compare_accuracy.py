import argparse
import os
import json
import base64
from PIL import Image
import io
from openai import OpenAI
import time

config_api_key = None
with open("/Users/jasonz/web_voyager_repo/WebVoyager/config.json", "r") as file:
    api_key_data = json.load(file)
    config_api_key = api_key_data["api_key"]

def load_mock_response(file_path):
    with open(file_path, "r") as file:
        mock_response = json.load(file)
    mock_response = json.loads(json.dumps(mock_response, ensure_ascii=False))
    return mock_response

def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    except Exception as e:
        print(f"Error encoding image: {image_path}. Error: {str(e)}")
        return None

def resize_image(image_path, max_size):
    try:
        with Image.open(image_path) as img:
            if img.format not in ['PNG', 'JPEG', 'GIF', 'WEBP']:
                print(f"Skipping unsupported image format: {image_path}")
                return None

            # Calculate the aspect ratio
            width, height = img.size
            aspect_ratio = width / height

            # Convert the image to JPEG format
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Reduce the image quality while maintaining the aspect ratio
            quality = 95
            while True:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', optimize=True, quality=quality)
                img_size = img_buffer.tell()
                if img_size <= max_size:
                    break
                quality -= 5
                img_buffer.close()

            # Save the resized image as JPEG
            resized_img_path = os.path.splitext(image_path)[0] + "_resized.jpg"
            img.save(resized_img_path, format='JPEG', optimize=True, quality=quality)

            return resized_img_path
    except Exception as e:
        print(f"Error resizing image: {image_path}. Error: {str(e)}")
        return None

def call_gpt4_api(gpt_args, openai_client, messages, use_mock=False, mock_file=None):
    if use_mock and mock_file:
        return load_mock_response(mock_file)
    else:
        try:
            openai_response = openai_client.chat.completions.create(
                model=gpt_args['model'], messages=messages, seed=gpt_args['seed'], max_tokens=1000)
            return openai_response
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

def extract_information(image_path, prompt, max_image_size):
    # For testing
    use_mock = False  # Set this flag to True when testing with the mock response
    mock_file = "mock_api_response.json"  # Specify the path to your mock response JSON file

    try:
        # Check image size and resize if needed
        if os.path.getsize(image_path) > max_image_size:
            print(f"Resizing image: {image_path}")
            resized_image_path = resize_image(image_path, max_image_size)
            if resized_image_path:
                image_path = resized_image_path
            else:
                print(f"Error resizing image: {image_path}")
                return None

        # Encode the image as base64
        encoded_image = encode_image(image_path)
        if not encoded_image:
            return None

        messages = [
            {"role": "system", "content": "You are an AI assistant that can analyze images and extract relevant information based on a given prompt. You can only output in JSON format."},
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
        # gpt_args = {
        #     'model': 'gpt-4-turbo-2024-04-09',
        #     'seed': 12,
        # }

        gpt_args = {
            'model': 'gpt-4o-2024-05-13',
            'seed': 12,
        }
        

        # Call the API with retry mechanism
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                response = call_gpt4_api(gpt_args, client, messages, use_mock, mock_file)
                if response:
                    extracted_info = response.choices[0].message.content.strip()
                    
                    # Check if the response is wrapped in a JSON code block
                    if extracted_info.startswith("```json") and extracted_info.endswith("```"):
                        extracted_info = extracted_info[7:-3].strip()
                        print(f"Removed JSON code block wrapping for image: {image_path}")
                    
                    try:
                        extracted_json = json.loads(extracted_info)
                        extracted_json = json.loads(json.dumps(extracted_json, ensure_ascii=False))
                        return extracted_json
                    except json.JSONDecodeError:
                        print(f"Error: Could not parse the extracted information as JSON for image: {image_path}")
                        # Save the raw extracted information to the not_parseable.txt file
                        with open("not_parseable.txt", "a") as file:
                            file.write(f"Image: {image_path}\n")
                            file.write(f"Raw Extracted Information:\n{extracted_info}\n\n")
                        return None
            except Exception as e:
                print(f"Error calling GPT-4 API for image: {image_path}. Attempt {attempt + 1}/{max_retries}. Error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        else:
            print(f"Error: Failed to call GPT-4 API after {max_retries} attempts for image: {image_path}")
            return None
    except Exception as e:
        print(f"Error extracting information for image: {image_path}. Error: {str(e)}")
        return None

def compare_extractions(manual_extraction, llm_extraction):
    accuracy = {}
    for field in manual_extraction:
        if field in llm_extraction:
            accuracy[field] = 1.0 if manual_extraction[field] == llm_extraction[field] else 0.0
        else:
            accuracy[field] = 0.0
    return accuracy

def preprocess_json(data):
    json_string = json.dumps(data, ensure_ascii=False)
    return json.loads(json_string)

def main(args, prompt):
    image_dir = args.image_dir
    output_file = args.output_file
    max_image_size = 20 * 1024 * 1024  # 20 MB in bytes

    results = []
    accuracy_sum = 0
    total_batches = 0

    for batch_folder in os.listdir(image_dir):
        if batch_folder.startswith("batch_"):
            batch_path = os.path.join(image_dir, batch_folder)
            image_path = os.path.join(batch_path, "fullpage_screenshot.png")
            manual_extraction_file = os.path.join(batch_path, "faculty_info.json")
            gpt_extraction_file = os.path.join(batch_path, "gpt_faculty_info.json")
            output_batch_file = os.path.join(batch_path, "batch_results.json")
            batch_accuracy_file = os.path.join(batch_path, "batch_accuracy.txt")
            mismatch_note_file = os.path.join(batch_path, "mismatch_note.txt")

            try:
                # Load the manual extraction from the file
                with open(manual_extraction_file, "r") as file:
                    manual_extractions = json.load(file)
            except FileNotFoundError:
                print(f"Error: Manual extraction file not found: {manual_extraction_file}")
                continue
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON format in manual extraction file: {manual_extraction_file}")
                continue

            llm_extractions = extract_information(image_path, prompt, max_image_size)
            batch_results = []
            batch_accuracy_sum = 0
            mismatch_note = ""

            if llm_extractions:
                for llm_extraction in llm_extractions:
                    for manual_extraction in manual_extractions:
                        if manual_extraction["name"] == llm_extraction["name"]:
                            accuracy = compare_extractions(manual_extraction, llm_extraction)
                            batch_accuracy_sum += sum(accuracy.values()) / len(accuracy)
                            result = {
                                "llm_extraction": llm_extraction,
                                "manual_extraction": manual_extraction,
                                "accuracy": accuracy
                            }
                            batch_results.append(result)
                            break
                    else:
                        mismatch_note += f"No corresponding manual extraction found for LLM extraction: {llm_extraction}\n"
                        batch_results.append({"llm_extraction": llm_extraction, "manual_extraction": None, "accuracy": None})

                # Check for manual extractions not found in LLM extractions
                for manual_extraction in manual_extractions:
                    if not any(llm_extraction["name"] == manual_extraction["name"] for llm_extraction in llm_extractions):
                        mismatch_note += f"Manual extraction not found in LLM extractions: {manual_extraction}\n"
                        batch_results.append({"llm_extraction": None, "manual_extraction": manual_extraction, "accuracy": None})

            else:
                mismatch_note = "No LLM extractions found for the batch."
                for manual_extraction in manual_extractions:
                    batch_results.append({"llm_extraction": None, "manual_extraction": manual_extraction, "accuracy": None})

            batch_accuracy = batch_accuracy_sum / len(batch_results) if batch_results else 0.0
            accuracy_sum += batch_accuracy
            total_batches += 1

            # Preprocess the batch_results and manual_extractions before writing to JSON files
            batch_results = preprocess_json(batch_results)
            manual_extractions = preprocess_json(manual_extractions)

            llm_extractions_cleaned = preprocess_json(llm_extractions) 


            with open(gpt_extraction_file, "w") as file:
                json.dump({"GPT4 faculty info": llm_extractions_cleaned}, file, indent=4)

            with open(output_batch_file, "w") as file:
                json.dump({"batch_results": batch_results}, file, indent=4)

            # Write the batch accuracy and mismatch notes to the batch directory
            with open(batch_accuracy_file, "w") as file:
                file.write(str(batch_accuracy))
                if mismatch_note:
                    file.write("\n\nMismatch Notes:\n")
                    file.write(mismatch_note)

            # Write the mismatch note to a separate file in the batch directory
            with open(mismatch_note_file, "w") as file:
                if mismatch_note:
                    file.write("Mismatch Notes:\n")
                    file.write(mismatch_note)

    avg_accuracy = accuracy_sum / total_batches if total_batches > 0 else 0

    # Write the overall average accuracy to the output file
    try:
        with open(output_file, "w") as file:
            json.dump({"average_accuracy": avg_accuracy}, file, indent=4)
        print(f"Average accuracy saved to: {output_file}")
    except Exception as e:
        print(f"Error saving average accuracy to output file: {output_file}. Error: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract information from images using GPT-4.")
    parser.add_argument("--image_dir", type=str, required=True, help="Path to the directory containing the images.")
    parser.add_argument("--output_file", type=str, required=True, help="Path to the output JSON file.")
    args = parser.parse_args()
    prompt = """
    Analyze the provided image and extract the relevant information for each faculty member based on the visible content. Note that the information might be partial or incomplete, and there could be multiple faculty members in the image.

    For each faculty member, provide the extracted information in a structured JSON format, organizing the data into appropriate fields and using "none" for any missing or unavailable information.

    The information to extract for each faculty member includes:
    - Name
    - Position
    - Research interests
    - Email
    - Phone

    Output the extracted information for all faculty members in the following JSON format:
    [
        {
            "name": "<faculty_name_1>",
            "position": "<faculty_position_1>",
            "research_interests": "<research_interests_1>",
            "email": "<email_address_1>",
            "phone": "<phone_number_1>"
        },
        {
            "name": "<faculty_name_2>",
            "position": "<faculty_position_2>",
            "research_interests": "<research_interests_2>",
            "email": "<email_address_2>",
            "phone": "<phone_number_2>"
        },
        ...
    ]

    If any of the fields are not available for a faculty member, use "none" as the value for that field.
    """

    main(args, prompt)


    #An error occurred: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}