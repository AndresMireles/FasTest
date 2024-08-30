# FasTest

This repository contains the backend for **FasTest**, a mobile application designed to read files uploaded by users and generate tests based on the content. The backend utilizes **Natural Language Processing (NLP)** and similar advanced techniques to process the text, analyze it, and create various types of questions, which are then used to generate the test.

## Overview

### Project Purpose  
FasTest helps users quickly generate practice tests from textual content, making it ideal for students and educators. The backend handles the heavy lifting of text processing, question generation, and integration with cloud services.

### Key Components

1. **Text Parsing and Cleaning**  
   - **File Handling**: The backend reads text from different file formats (e.g., PDFs, text files) and cleans the data, preparing it for analysis.  
   - **Text Processing**: It segments the text into meaningful units like words, sentences, and paragraphs, facilitating the extraction of key information.

2. **Question Generation**  
   The core functionality involves generating various types of questions, including:  
   - **Fill-in-the-Blank**: Based on keywords identified in the text.  
   - **Multiple-Choice**: Created using names, places, and dates extracted from the content.  
   - **Enumeration Questions**: Derived from lists or sequences found in the text.

3. **Cloud Integration**  
   - **Firebase Integration**: The backend uses Firebase for file storage and retrieval, allowing seamless interaction between the mobile app and the backend.  
   - **Google Cloud Functions**: Some tasks, like PDF processing and language-specific text handling, are offloaded to Google Cloud Functions, ensuring efficient and scalable operations.

4. **Multilingual Support**  
   The system is capable of processing text in multiple languages, adapting the question generation process according to the language detected in the content.

### How It Works  
1. **File Upload**: Users upload a file through the FasTest mobile app.  
2. **Processing**: The backend retrieves the file from Firebase, extracts and processes the text, and generates questions.  
3. **Test Generation**: The questions are compiled into a test format, which is then sent back to the mobile app for the user to take.
