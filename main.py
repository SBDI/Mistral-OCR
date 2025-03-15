import streamlit as st
import os
import base64
import json
import time
from mistralai import Mistral

# Page configuration
st.set_page_config(layout="wide", page_title="Mistral OCR", page_icon=":material/file_present:")

# Sidebar for configuration - keep only API key here
with st.sidebar:
    st.title("Configuration")
    
    # API Key Input stays in sidebar
    api_key = st.text_input("Enter your Mistral API Key", type="password")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Mistral OCR extracts text from PDFs and images using Mistral OCR API.")
    st.markdown("---")


# Main content area
st.title("Mistral OCR Test")

# API Key validation
if not api_key:
    st.info("Please enter your API key in the sidebar to continue.")
    st.stop()

# Initialize session state variables for persistence
if "ocr_result" not in st.session_state:
    st.session_state["ocr_result"] = []
if "preview_src" not in st.session_state:
    st.session_state["preview_src"] = []
if "image_bytes" not in st.session_state:
    st.session_state["image_bytes"] = []

# Input area with improved UI
st.subheader("Document Input")

# Create a card-like container for the input options
with st.container():
    # Add some padding and a border to create a card effect
    st.markdown("""
    <style>
    .stExpander {
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
        background-color: #f9f9f9;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # First row - file type selection with icons
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Select Document Type")
        file_type = st.radio(
            "Select file type",
            ("PDF", "Image"),
            label_visibility="collapsed",
            horizontal=True,
            index=0
        )
    
    with col2:
        st.markdown("##### Select Input Method")
        source_type = st.radio(
            "Select source type",
            ("URL", "Local Upload"),
            label_visibility="collapsed",
            horizontal=True,
            index=0
        )
    
    # Second row - input field based on selection
    st.markdown("---")
    
    input_url = ""
    uploaded_files = []
    
    if source_type == "URL":
        input_url = st.text_area(
            f"Enter {'PDF' if file_type == 'PDF' else 'image'} URLs (one per line)",
            placeholder=f"https://example.com/sample.{'pdf' if file_type == 'PDF' else 'jpg'}"
        )
    else:
        file_types = ["pdf"] if file_type == "PDF" else ["jpg", "jpeg", "png"]
        uploaded_files = st.file_uploader(
            f"Upload {file_type.lower()} file(s)",
            type=file_types,
            accept_multiple_files=True
        )

# Process Button with improved styling
process_button = st.button(
    "📄 Process Document", 
    type="primary", 
    use_container_width=True
)

# OCR Processing
if process_button:
    if source_type == "URL" and not input_url.strip():
        st.error("Please enter at least one valid URL.")
    elif source_type == "Local Upload" and not uploaded_files:
        st.error("Please upload at least one file.")
    else:
        client = Mistral(api_key=api_key)
        st.session_state["ocr_result"] = []
        st.session_state["preview_src"] = []
        st.session_state["image_bytes"] = []
        
        sources = input_url.split("\n") if source_type == "URL" else uploaded_files
        
        with st.status("Processing documents...") as status:
            progress_bar = st.progress(0)
            for idx, source in enumerate(sources):
                st.write(f"Processing document {idx+1} of {len(sources)}")
                
                if file_type == "PDF":
                    if source_type == "URL":
                        document = {"type": "document_url", "document_url": source.strip()}
                        preview_src = source.strip()
                    else:
                        file_bytes = source.read()
                        encoded_pdf = base64.b64encode(file_bytes).decode("utf-8")
                        document = {"type": "document_url", "document_url": f"data:application/pdf;base64,{encoded_pdf}"}
                        preview_src = f"data:application/pdf;base64,{encoded_pdf}"
                else:
                    if source_type == "URL":
                        document = {"type": "image_url", "image_url": source.strip()}
                        preview_src = source.strip()
                    else:
                        file_bytes = source.read()
                        mime_type = source.type
                        encoded_image = base64.b64encode(file_bytes).decode("utf-8")
                        document = {"type": "image_url", "image_url": f"data:{mime_type};base64,{encoded_image}"}
                        preview_src = f"data:{mime_type};base64,{encoded_image}"
                        st.session_state["image_bytes"].append(file_bytes)
                
                try:
                    ocr_response = client.ocr.process(model="mistral-ocr-latest", document=document, include_image_base64=True)
                    time.sleep(1)  # wait 1 second between request to prevent rate limit exceeding
                    
                    pages = ocr_response.pages if hasattr(ocr_response, "pages") else (ocr_response if isinstance(ocr_response, list) else [])
                    result_text = "\n\n".join(page.markdown for page in pages) or "No result found."
                except Exception as e:
                    result_text = f"Error extracting result: {e}"
                
                st.session_state["ocr_result"].append(result_text)
                st.session_state["preview_src"].append(preview_src)
                
                # Update progress bar
                progress_bar.progress((idx + 1) / len(sources))
            
            status.update(label="Processing complete!", state="complete")

# Display Preview and OCR Results if available
if st.session_state["ocr_result"]:
    st.markdown("---")
    st.header("📑 Results")
    
    tabs = st.tabs([f"Document {i+1}" for i in range(len(st.session_state["ocr_result"]))])
    
    for idx, tab in enumerate(tabs):
        with tab:
            result = st.session_state["ocr_result"][idx]
            
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                st.markdown("#### 📄 Document Preview")
                if file_type == "PDF":
                    pdf_embed_html = f'<iframe src="{st.session_state["preview_src"][idx]}" width="100%" height="700" frameborder="0" style="border: 1px solid #e6e6e6; border-radius: 5px;"></iframe>'
                    st.markdown(pdf_embed_html, unsafe_allow_html=True)
                else:
                    if source_type == "Local Upload" and st.session_state["image_bytes"]:
                        st.image(st.session_state["image_bytes"][idx], use_container_width=True, caption="Uploaded Image")
                    else:
                        st.image(st.session_state["preview_src"][idx], use_container_width=True, caption="Input Image")
            
            with col2:
                st.markdown("#### 📝 OCR Results")
                
                def create_download_link(data, filetype, filename, button_text, format_color):
                    b64 = base64.b64encode(data.encode()).decode()
                    btn_style = """
                        <style>
                        .download-button {
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            gap: 8px;
                            padding: 8px 16px;
                            background-color: #ffffff;
                            color: #333333;
                            text-decoration: none;
                            border-radius: 6px;
                            margin: 8px;
                            text-align: center;
                            transition: all 0.2s ease;
                            font-weight: 500;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                            border: 1px solid #e0e0e0;
                            min-width: 120px;
                        }
                        .download-button:hover {
                            background-color: #f5f5f5;
                            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                            transform: translateY(-1px);
                        }
                        .download-icon {
                            color: #555;
                            margin-right: 4px;
                        }
                        .format-badge {
                            font-size: 12px;
                            padding: 2px 6px;
                            border-radius: 4px;
                            color: white;
                            background-color: ${formatColor};
                            font-weight: bold;
                        }
                        </style>
                    """.replace("${formatColor}", format_color)
                    
                    # SVG download icon
                    download_icon = """
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="download-icon">
                      <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                      <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                    </svg>
                    """
                    
                    href = f'{btn_style}<a class="download-button" href="data:{filetype};base64,{b64}" download="{filename}">{download_icon} Download <span class="format-badge">{button_text}</span></a>'
                    return href
                
                # Create download links with better styling and icons
                json_data = json.dumps({"ocr_result": result}, ensure_ascii=False, indent=2)
                
                st.markdown("##### Download Results:")
                download_links = "<div style='margin: 15px 0px; display: flex; flex-wrap: wrap; gap: 5px;'>"
                download_links += create_download_link(json_data, "application/json", f"Output_{idx+1}.json", "JSON", "#2196F3")
                download_links += create_download_link(result, "text/plain", f"Output_{idx+1}.txt", "TXT", "#4CAF50") 
                download_links += create_download_link(result, "text/markdown", f"Output_{idx+1}.md", "MD", "#FF9800")
                download_links += "</div>"
                
                st.markdown(download_links, unsafe_allow_html=True)
                
                # Results display with dynamic height and RTL support
                st.markdown("##### Extracted Text:")
                
                # Custom CSS for the text container
                st.markdown("""
                    <style>
                    .text-container {
                        padding: 15px;
                        border: 1px solid #e6e6e6;
                        border-radius: 5px;
                        background-color: #fafafa;
                        font-family: 'Noto Sans', sans-serif;
                        line-height: 1.6;
                        direction: auto;
                        text-align: start;
                        min-height: 100px;
                        max-height: 800px;
                        overflow-y: auto;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                    
                    /* Custom scrollbar styling */
                    .text-container::-webkit-scrollbar {
                        width: 8px;
                    }
                    
                    .text-container::-webkit-scrollbar-track {
                        background: #f1f1f1;
                        border-radius: 4px;
                    }
                    
                    .text-container::-webkit-scrollbar-thumb {
                        background: #888;
                        border-radius: 4px;
                    }
                    
                    .text-container::-webkit-scrollbar-thumb:hover {
                        background: #666;
                    }
                    
                    /* RTL specific styles */
                    .text-container[dir="rtl"] {
                        font-family: 'Noto Naskh Arabic', 'Noto Sans', sans-serif;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # Function to detect if text contains RTL script
                def contains_rtl(text):
                    # Unicode ranges for RTL scripts (Arabic, Hebrew, etc.)
                    rtl_ranges = [
                        (0x0590, 0x05FF),   # Hebrew
                        (0x0600, 0x06FF),   # Arabic
                        (0x0750, 0x077F),   # Arabic Supplement
                        (0x08A0, 0x08FF),   # Arabic Extended-A
                        (0xFB50, 0xFDFF),   # Arabic Presentation Forms-A
                        (0xFE70, 0xFEFF),   # Arabic Presentation Forms-B
                    ]
                    
                    for char in text:
                        code = ord(char)
                        for start, end in rtl_ranges:
                            if start <= code <= end:
                                return True
                    return False
                
                # Determine text direction
                is_rtl = contains_rtl(result)
                dir_attr = 'rtl' if is_rtl else 'ltr'
                align_attr = 'right' if is_rtl else 'left'
                
                # Display the text with appropriate direction and styling
                st.markdown(
                    f"""<div class="text-container" dir="{dir_attr}" style="text-align: {align_attr};">
                    {result.replace(chr(10), '<br>')}
                    </div>""",
                    unsafe_allow_html=True
                )
