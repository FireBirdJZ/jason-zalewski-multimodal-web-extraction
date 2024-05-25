# jason-zalewski-multimodal-web-extraction

## Overview

This module can be split into two main parts:
    
1. The first module extracts all of the professors names, positions and research interests from a faculty cs webpage by Classifying similar html subtrees into regions containing records for each professor with pydepta; then extracting the professor's information inside a records with a large language model. 

2. The second module compares two large language models(gpt3.5turbo and Beluga which is a finetuned Llama2) by running a set of web information extraction prompts to test the capability of each model with direct comparison of each other.

The Rest of the folders and files were used in exploration and research such as the experiments folder which tests things out dealing with langchain, natbot, and vector databases.

A Break Down of the structure of the repo's file structure:
```
.
├── IE_Faculty_dataset.csv
├── README.md
├── config.json
├── manuel_versus_multimodal
│   ├── caltech_dir
│   │   ├── build_caltech.py
│   │   └── llm_extract_and_compare_accuracy.py
│   ├── texas_dir
│   │   ├── build_texas.py
│   │   └── llm_extract_and_compare_accuracy.py
│   └── uc_dir
│       ├── build_validate_case_and_extract.py
│       ├── llm_extract_and_compare_accuracy.py
│       └── table.txt
├── requirements.txt
├── split_webpage.py
├── utils.py
├── utils_webarena.py
└── video_example_running_scripts.txt
```



## Setup

module's dependencies: 
Python Version 3.10.13
Pip Version 24.0

The Rest of the python dependencies can be installed with:
```
pip install -r requirements.txt 
```

You will also need a openai api-key inorder to use gpt3.5turbo which can be stored inside a config.json file.


Some of the important files/components of the repo:

`src/segmentation/pydepta/pydepta/depta.py`: Runs pydepta to classify regions in HTML and extracts professor info with LLM.

`src/segmentation/pydepta/pydepta/comparing_models.py`: Class where depta.py calls to classify regions and extract professor info with LLM.

`src/segmentation/pydepta/pydepta/LLMBenchmarkSuite.py`: File which runs gpt3.5turbo and Beluga on different standarized prompts for IE in inorder to test the capability of each model.

`src/segmentation/pydepta/pydepta/output_depta`: Shows examples of complete output from Pydepta for UIUC, MIT, and CMU faculty webpages.

`src/segmentation/pydepta/pydepta/video_test_comparing_models`: Shows results from past experiments of extracting professor info with LLMs. Files starting with v2.2 show the results using the newest version of cot prompt. 



## Functional Design (Usage)

### FacultyDataHarvester Class

**Overview**
The `FacultyDataHarvester` class located which can be run from depta.py is designed to facilitate the extraction and processing of faculty-related data from web pages. It provides methods to fetch HTML content, extract text, and identify faculty names and related information.

**Methods**

* `fetch_html_from_url(url: str) -> str`  
  _Fetches HTML content from the specified URL._
  - **Input**: A string representing the URL of the web page.
  - **Output**: A string containing the raw HTML content of the page.

* `save_html_to_file(url: str, folder_path: str = 'saved_faculty_html_files')`  
  _Saves the fetched HTML content to a file._
  - **Input**:
    - `url`: URL of the web page.
    - `folder_path`: Optional. The directory path where the HTML file will be saved.
  - **Output**: None. The HTML content is saved to a file in the specified directory.

* `load_html_from_file(url: str) -> str`  
  _Loads HTML content from a saved file._
  - **Input**: A string representing the URL of the web page. The URL is used to determine the filename.
  - **Output**: A string containing the HTML content loaded from the file.

* `extract_text() -> str`  
  _Extracts and returns the textual content from the loaded HTML._
  - **Input**: None. Operates on the internal `raw_html` attribute.
  - **Output**: A string containing the extracted textual content.

* `find_names_in_region(region: List[List[Any]], folder_path: str, file_name: str, write_mode: str = 'txt')`  
  _Processes the provided region to identify and classify faculty names and related information, and saves the output in the specified format._
  - **Input**:
    - `region`: A list of lists containing the data to be processed.
    - `folder_path`: The directory path where the output file will be saved.
    - `file_name`: The name of the output file.
    - `write_mode`: Optional. Specifies the output format ('json' or 'txt').
  - **Output**: None. The processed data is saved to a file in the specified format.

**Usage Examples**

1. `build_texas.py` script parameters:
   - `"https://www.cs.utexas.edu/people"`: The URL of the webpage to process.
   - `18`: The number of faculty members to include in each batch.
   - `texas_output18`: The directory where the output will be saved.

2. `llm_extract_and_compare_accuracy.py` script parameters:
   - `--image_dir texas_output18`: The directory containing the images to process.
   - `--output_file texas_output18/texas_results`: The file path where the results will be saved.

```bash
cd manuel_versus_multimodal/texas_dir
python3 build_texas.py "https://www.cs.utexas.edu/people" 18 texas_output18
python3 llm_extract_and_compare_accuracy.py --image_dir texas_output18 --output_file texas_output18/texas_results
```



`split_webpage.py` script parameters:
   - `--urls "https://math.yale.edu/people/all-faculty" "https://www.gps.caltech.edu/people?category=17"`: The URLs of the webpages to process, separated by spaces and enclosed in quotes.
   - `--output_dir "video_rec_splitwebpage_output"`: The directory where the output will be saved.

```bash
python split_webpage.py --urls "https://math.yale.edu/people/all-faculty" "https://www.gps.caltech.edu/people?category=17" --output_dir "video_rec_splitwebpage_output"
```


`test_diff_sized_images.py` script parameters:
   - `--urls "https://math.yale.edu/people/all-faculty" "https://www.gps.caltech.edu/people?category=17"`: The URLs of the webpages to process, separated by spaces and enclosed in quotes.
   - `--output_dir "video_rec_diffsizedimages_output"`: The directory where the output will be saved.

```bash
python test_diff_sized_images.py --urls "https://math.yale.edu/people/all-faculty" "https://www.gps.caltech.edu/people?category=17" --output_dir "video_rec_diffsizedimages_output"
```



 ### LLM Benchmark Suite - Asynchronous Processing

**Overview**
This section focuses on asynchronous processing of text analysis using large language models (LLMs). It provides functionality for reading prompts from a file, comparing responses from different models asynchronously, and writing the outputs to a file inside of LLMBenchmarkSuite.py.

**Key Functions**

* `read_prompts_from_file(file_path: str, delimiter: str = "#@@@@#") -> List[str]`  
  _Reads prompts for text analysis from a specified file._
  - **Input**: 
    - `file_path`: Path to the file containing prompts.
    - `delimiter`: String delimiter used to separate prompts in the file.
  - **Output**: List of prompts as strings.

* `collect_all_responses_async(prompts: List[str]) -> str`  
  _Asynchronously collects responses from LLMs for each prompt._
  - **Input**: List of prompts to process.
  - **Output**: Concatenated string of all responses.

* `write_to_file(file_path: str, data: str) -> None`  
  _Writes the given data to a file at the specified path._
  - **Input**: 
    - `file_path`: Path to the output file.
    - `data`: String data to write to the file.
  - **Output**: None. The data is written to the file.

## Demo video

[![Demo Video](https://drive.google.com/file/d/19HggW0x5sm8qySDudxUWFJsJ5jaeQfd4/view?usp=drive_link)]



## Algorithmic Design 

### 1. Viewport and accesibility tree extraction algorithm
First the program goes to the url and renders the webpage with selenium. Next, it takes a screenshot and creates an assesibility tree which is similar to the HTML of whatever is currently in the viewport so it can be feed to an MultiModal Model. One thing to note is the assebility tree sometimes has slightly more infomration inside it than the image, so the model might extract information seen in the assebility tree but not the image. The accesibility tree was taken from the webvoyager's utility file. After we scroll down an even distance and repeat the process of getting a screenshot and getting the assebility tree until we reach the bottom of the webpage. This algorithm uses multiprocessing so we can do this for multiple webpages at once. Lastly, we go though all of these viewports and send the accesibility tree and image to the GPT4 api to extract a task based on the prompt. The extraction output from the model is then saved inside the same viewport directory it was extracted.

 ### 2. Comparing different sized images from the Viewport and accesibility tree extraction algorithm
 This program works similary as the Viewport and accesibility tree extraction algorithm but it has the ability to take different sized images when taking a screenshot of each viewport so you can compare the results of which sized image works best for a given extraction.

### 3. Manuel extraction versus llm extraction results
This program was an attempt to come up with a automated way to grade the LLMs results on different amount of imformation the Multimodal model had to extract on a image. Intead of taking screenshots and scrolling down the viewport, I first manuelly removed all the information I didn't want to be an a given image for the screenshot by deleting it off the html. The 3 webpages I did this for were all for different faculty pages. Next, I found where the faculty information was located in the html, and I would go in order of picking a speceficed amount of Professors I wanted to currently look at on the page, say 3, then delete all of the other ones on HTML and take a screenshot of the whole page. I would then redo this step until I had pictures of all the professors with the given amount in each screenshot. This program allows you to pick how many professors you want to look at in each image so that you can comapre results of extracting of say 6 professors at once or 21 professors at once.
I want to mention some of the problems that this program has so that if you try to use it for extraction, I recommend not trusting the results of the llm extraction part, as some my results had problems with utf encodings and comparing the exact strings of text from the maunel extraction to the MLM extractions version, which would mark the answer wrong.   


![design architecture](https://github.com/FireBirdJZ/forward_data-llm_ie/blob/main/diagram.png)



## Issues and Future Work

* In the Manuel extraction versus llm extraction results program, the grading of the MLM versus has manuel extracting has issues of utf encoding errors and trying to come up with ways to match some of the strings in an exact manner, which would cause the answer to be marked wrong. Also, the accruacy of the caltech page displays a 0.78 accuracy for each batch of images its currently at, which is not correct. The UC webpage out of the three should be the most accuracte even with some utf encoding errors if you feel you need to look at something quantitatively. The caltech page extraction should not be looked at quantitatively At least from the accuracy shown in the results of my extraction.
* The assesibility in the Viewport and accesibility tree extraction algorithm might have encoding errors when saving it to the file. The accuracy of the model's extraction seems to be not majorly effected by this, but should still be mentioned.
* The accesibility tree algorithm seems to get exponetially slower the more complex and longer a webpage is.




## Change log





## References 
include links related to datasets and papers describing any of the methodologies models you used. E.g. 
* WebVoyager: https://arxiv.org/pdf/2401.13919
* The Future of Web Data Mining: https://aclanthology.org/2024.case-1.1.pdf
* Mind2Web: https://arxiv.org/pdf/2306.06070
* SeeAct: https://osu-nlp-group.github.io/SeeAct/
* Openai for gpt: https://openai.com/
