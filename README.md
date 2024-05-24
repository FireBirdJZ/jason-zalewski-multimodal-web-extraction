# jason-zalewski-mlm-web-extraction

## Overview

This module can be split into two main parts:
    
1. The first module extracts all of the professors names, positions and research interests from a faculty cs webpage by Classifying similar html subtrees into regions containing records for each professor with pydepta; then extracting the professor's information inside a records with a large language model. 

2. The second module compares two large language models(gpt3.5turbo and Beluga which is a finetuned Llama2) by running a set of web information extraction prompts to test the capability of each model with direct comparison of each other.

The Rest of the folders and files were used in exploration and research such as the experiments folder which tests things out dealing with langchain, natbot, and vector databases.

A Break Down of the structure of the repo's file structure:
```
.
├── diagram.png
├── LICENSE
├── README.md
├── requirements.txt
└── src
    ├── experiments
    │   ├── generated_code_directory
    │   │   ├── generated_code.py
    │   │   └── output.txt
    │   ├── langchain_testing.ipynb
    │   ├── natbot_extract_text_json
    │   ├── natbot_generated_program_directory
    │   │   ├── natbot_generated_output.txt
    │   │   └── natbot_generated_program.py
    │   ├── natbot_prompt_program.py
    │   ├── natbot_testing.py
    │   ├── sematic_regular_expressions_testing.py
    │   └── testing_markuplm.py
    ├── extracted_info.json
    ├── main.py
    ├── segmentation
    │   └── pydepta
    │       ├── LICENSE
    │       ├── Makefile.buildbot
    │       ├── pydepta
    │       │   ├── comparing_models
    │       │   │   ├── gpt3.5turbo_illini.json
    │       │   │   └── gpt3.5turbo_mit.json
    │       │   ├── comparing_models.py
    │       │   ├── cot_comparing_models
    │       │   │   ├── gpt3.5turbo_illini2.json
    │       │   │   └── gpt3.5turbo_illini.json
    │       │   ├── depta.py
    │       │   ├── extract_prof_names.py
    │       │   ├── htmls.py
    │       │   ├── illini1_professors.json
    │       │   ├── illini2_professors.json
    │       │   ├── illlini3_professors.json
    │       │   ├── __init__.py
    │       │   ├── llm_benchmark_suite
    │       │   │   ├── benchmark_output.txt
    │       │   │   ├── benchmark_prompts_file.txt
    │       │   │   └── text_analysis
    │       │   │       ├── output_analysis.txt
    │       │   │       ├── prompt_analysis.txt
    │       │   │       ├── video_output_demo.txt
    │       │   │       └── video_prompt_demo.txt
    │       │   ├── LLMBenchmarkSuite.py
    │       │   ├── mdr.py
    │       │   ├── output_depta
    │       │   │   ├── cmu_depta_output.txt
    │       │   │   ├── illini_depta_output.txt
    │       │   │   └── mit_depta_output.txt
    │       │   ├── __pycache__
    │       │   │   ├── comparing_models.cpython-311.pyc
    │       │   │   ├── extract_prof_names.cpython-311.pyc
    │       │   │   ├── htmls.cpython-311.pyc
    │       │   │   ├── mdr.cpython-311.pyc
    │       │   │   ├── trees.cpython-311.pyc
    │       │   │   └── trees_cython.cpython-311.pyc
    │       │   ├── saved_faculty_html_files
    │       │   │   ├── csd.cmu.edu.html
    │       │   │   ├── cs.illinois.edu.html
    │       │   │   └── www.eecs.mit.edu.html
    │       │   ├── tests
    │       │   │   ├── __init__.py
    │       │   │   ├── resources
    │       │   │   │   ├── 1.html
    │       │   │   │   ├── 1.txt
    │       │   │   │   ├── 2.html
    │       │   │   │   ├── 2.txt
    │       │   │   │   ├── 3.html
    │       │   │   │   ├── 3.txt
    │       │   │   │   ├── 4.html
    │       │   │   │   ├── 4.txt
    │       │   │   │   ├── 5.html
    │       │   │   │   ├── 5.txt
    │       │   │   │   ├── 6.html
    │       │   │   │   └── 7.html
    │       │   │   └── test_depta.py
    │       │   ├── trees_cython.c
    │       │   ├── trees_cython.py
    │       │   ├── trees_cython.pyx
    │       │   ├── trees.py
    │       │   └── video_test_comparing_models
    │       │       ├── gpt3.5turbo_illini.txt
    │       │       ├── v2.2_gpt3.5turbo_cmu_full.txt
    │       │       ├── v2.2_gpt3.5turbo_illini_full.txt
    │       │       ├── v2.2_gpt3.5turbo_mit_full.txt
    │       │       ├── v2_gpt3.5turbo_illini_full.txt
    │       │       ├── v2_gpt3.5turbo_illini.txt
    │       │       ├── v2_gpt3.5turbo_mit_full2.txt
    │       │       └── v2_gpt3.5turbo_mit_full.txt
    │       ├── README.rst
    │       ├── requirements.txt
    │       ├── runtests.sh
    │       ├── setup.py
    │       ├── snapshot1.png
    │       └── test.py
    ├── shopify_extracted_info.json
    ├── vector_db.py
    └── web_extractor.py
```



## Setup

module's dependencies: 
Python Version 3.11.5
Pip Version 23.3

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

**Usage Example**

```python
harvester = FacultyDataHarvester()
url = "http://example.com/faculty"
html_content = harvester.fetch_html_from_url(url)
harvester.save_html_to_file(url)
text_content = harvester.extract_text()
regions = d.extract(html=html_content)
harvester.find_names_in_region(regions, "output_directory", "faculty_data", "txt")
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

[![Demo Video](https://img.youtube.com/vi/8swVj_onO30/maxresdefault.jpg)](https://youtu.be/8swVj_onO30)



## Algorithmic Design 

First, We take the input of a faculty webpage url or it's HTML and run it through pydepta to generate regions that classifies similar structure subtrees in the HTML.

Next, we classify these regions with a large language model asking if a region contains Professor names. If the region does contain Professor names we go to the next step in the algorithm, otherwise we skip this region and go onto the next one to classify.

After, We check 3 records at a time inside a region. a record is a list which usually consists of single Professor with information related to the Professor that pydepta classifies in it's subtree such as the Professor's email and Position depending on the webpage. We put these 3 records inside a large language model's and asking the model to output in JSON format the Professor's name, position and research interests. If it doesn't find this information it should fill it with null.(Exact prompts used are in comparing_models.py).

Lastly, we take the returned answer from the language model from the current 3 records and insert it inside a file to store. Then repeat the same steps onto the next 3 records inside that Region.

![design architecture](https://github.com/FireBirdJZ/forward_data-llm_ie/blob/main/diagram.png)



## Issues and Future Work

* Localllm Beluga doesn't work with the same exact program in comparing_models.py that was built for gpt3.5turbo.
* In comparing_models.py the large language model will not always output correct JSON output which will cause the program to skip inserting into the file to prevent the program from crashing. In the future I will most likely switch this file from a .json to a .txt file when inserting, or come up with a way to parse the llm's answer and manually build the Json as the large language model is inconsistent of building the correct JSON object even if it's answer could be correct of extraction the correct information.
* For very long webpages it's possible that pydepta can crash.
* Pydepta pip package does not currently work as the project seems to be abandoned as well as it's dependencies. So I modified the files to run inside of pydepta and used only what I needed for my research.
* Petals can sometimes take long period of times or not find connections to run the local llm, such as in the presentation I cut the video short of it finishing its output.
* Beluga generates the prompt into its answer.


## Change log

12/22/2023: Added folder to show pydepta output from UIUC, MIT and CMU faculty webpages. Updated V2 prompt to v2.2 to improve the LLM's ability to get research interests that are not null and to better be able to disguish a professor's name from its position; added another example for the llm to use in the chain of thought prompt. Ran extraction with the new prompt for UIUC, MIT, and CMU faculty webpages.



## References 
include links related to datasets and papers describing any of the methodologies models you used. E.g. 

* Pydepta fork: https://github.com/ZhijiaCHEN/pydepta/tree/master (Thank you to Zhijia Chen for explaining his modifications and code to pydepta)
* For Running Local LLMs: https://github.com/bigscience-workshop/petals
* Emotional Prompts: https://arxiv.org/pdf/2307.11760
* LLMs Don't say what they think: https://arxiv.org/pdf/2305.04388
* Depta Paper: https://dl.acm.org/doi/10.1145/1060745.1060761
* Openai for gpt: https://openai.com/

Used in exploration and research but not in main solution:
* Natbot.py: https://github.com/nat/natbot/blob/main/natbot.py
* Langchain: https://www.langchain.com/
