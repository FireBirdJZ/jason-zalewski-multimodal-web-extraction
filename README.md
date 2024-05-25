# jason-zalewski-multimodal-web-extraction

## Overview

This module contains several scripts for extracting and analyzing information from webpages:

1. `build_texas.py`, `build_caltech.py`, `build_uc.py`:
  These scripts are used to build datasets for different universities (Texas, Caltech, UC). They navigate to specific faculty pages, remove unwanted elements, and extract faculty information in batches. The extracted information is saved in JSON format, and screenshots of the modified webpage are taken for each batch.

2. `llm_extract_and_compare_accuracy.py` (located in `manuel_versus_multimodal/caltech_dir`, `manuel_versus_multimodal/texas_dir`, and `manuel_versus_multimodal/uc_dir`):
  This script works in conjunction with the dataset building scripts. It extracts information from the captured screenshots using the GPT-4 API. It iterates over each webpage directory, loads the screenshots and prompts, and sends them to the GPT-4 API for analysis. The extracted information is then compared with manually extracted information to calculate the accuracy for each field. The script saves the comparison results, average accuracy, and mismatch notes in separate files within each webpage directory.

3. `split_webpage.py`:
  This script captures webpage screenshots and saves them in a specified directory. It takes URLs or a CSV file containing URLs as input. The script navigates to each URL, captures screenshots of the entire page by scrolling and taking screenshots of each viewport. It also saves the full HTML and text of the webpage. The captured data is organized into separate directories for each webpage and viewport.

4. `test_diff_sized_images.py`:
  This script captures webpage screenshots in different sizes and saves them in a specified directory. It takes URLs or a CSV file containing URLs as input. The script sets up different image sizes, navigates to each URL, captures screenshots of the page in each size, and saves the screenshots in separate directories for each webpage, size, and viewport. It also saves the full HTML of the webpage and a metadata file containing information about the total height, viewport count, and size of each webpage.

These scripts can be used independently or in combination to extract and analyze webpage data, capture screenshots, and compare the performance of language models in extracting information from the captured data.

The repository also includes other directories and files:

- `manuel_versus_multimodal`: Contains subdirectories for different universities (`caltech_dir`, `texas_dir`, `uc_dir`), each containing scripts for building datasets and comparing the accuracy of language models.
- `utils.py` and `utils_webarena.py`: Utility files containing helper functions used by the scripts.
- `requirements.txt`: Lists the required Python dependencies for running the scripts.
- `IE_Faculty_dataset.csv`: A dataset file related to faculty information extraction.
- `config.json`: Configuration file for storing API keys and other settings.
- `video_example_running_scripts.txt`: A text file with examples of running the scripts.

Overall, this module focuses on webpage data extraction, screenshot capture, and comparing the performance of language models in extracting information from the captured data.

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
│       ├── build_uc.py.py
│       ├── llm_extract_and_compare_accuracy.py
│       └── table.txt
├── requirements.txt
├── split_webpage.py
├── test_diff_sized_images.py
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

You will also need a openai api-key inorder to use gpt4 which can be stored inside a config.json file.


## Functional Design (Usage)

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
