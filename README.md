# Mistral OCR

A streamlined Streamlit application that uses Mistral AI's OCR capabilities to extract text from PDFs and images.


## Features

- PDF and Image file support
- URL or file upload options
- Real-time document preview
- Clean OCR results display
- One-click result downloads

## Quick Start

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Key:**
   ```bash
   # Windows
   set MISTRAL_API_KEY=your_api_key_here
   
   # Linux/Mac
   export MISTRAL_API_KEY=your_api_key_here
   ```

3. **Run App:**
   ```bash
   streamlit run main.py
   ```

## Requirements
- Python 3.7+
- Streamlit
- Mistral AI Python Client
