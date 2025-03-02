import json
import os
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

### 🚀 Step 1: Scraper Functions ###
def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""

        for page in doc:
            text += page.get_text("text") + "\n"

        return text.strip()  # Remove leading/trailing spaces
    except Exception as e:
        print(f"Error: {e}")
        return None

def scrape_sec_document(url):
    """Scrapes text from an SEC HTML document, using paragraph tags for better accuracy."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract text from <p> tags
        paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

        return "\n\n".join(paragraphs)  # Maintain logical paragraph breaks
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def scrape_local_html(file_path):
    """Parses and cleans a local HTML SEC filing document while preserving paragraph structure."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()

        # Preserve tables and important formatting
        for table in soup.find_all('table'):
            for attr in ["border", "cellspacing", "cellpadding", "width"]:
                table.attrs.pop(attr, None)

        # Extract text from <p> tags for better accuracy
        paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

        return "\n\n".join(paragraphs)  # Preserve paragraph spacing
    except Exception as e:
        return f"Error: {e}"

def scrape_website_text(url):
    """Scrapes text from a general website, using paragraph tags for better chunking."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text from <p> tags to maintain accuracy
        paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

        return "\n\n".join(paragraphs)
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

### 🚀 Step 2: Structuring Data for JSON ###
def create_json_entry(document_name, document_type, document_link, issuer, resource_name, raw_text):
    """Creates a structured JSON entry with paragraph-level segmentation."""
    
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    
    return {
        "document_name": document_name,  
        "document_type": document_type,
        "document_link": document_link,
        "issuer": issuer,
        "resource_name": resource_name,
        "section_content": raw_text,
        "content": {f"Paragraph_{i+1}": para for i, para in enumerate(paragraphs)}
    }

### 🚀 Step 3: User Interface ###
def main():
    print("📌 Choose the type of document to scrape:")
    print("1. SEC Financial Document (Online)")
    print("2. SEC Financial Document (Local HTML)")
    print("3. PDF Document")
    print("4. Website HTML")
    
    choice = input("Enter the number of your choice: ")

    if choice == "1":
        url = input("Enter SEC document URL: ")
        raw_text = scrape_sec_document(url)
        document_name = input("Enter document name (e.g., '10-K Report'): ")
        document_type = "Raw Financials"
        document_link = url
        issuer = input("Enter issuer name (e.g., 'FTX Trading Ltd.'): ")
        resource_name = "SEC"

    elif choice == "2":
        file_path = input("Enter the path to the local SEC HTML file: ")
        raw_text = scrape_local_html(file_path)
        document_name = os.path.splitext(os.path.basename(file_path))[0]  
        document_type = "Raw Financials"
        document_link = "N/A"
        issuer = input("Enter issuer name: ")
        resource_name = "SEC"

    elif choice == "3":
        pdf_path = input("Enter the path to the PDF file: ")
        raw_text = extract_text_from_pdf(pdf_path)  
        if not raw_text:
            print("❌ Failed to extract text from the PDF. Exiting.")
            return
        
        document_name = os.path.splitext(os.path.basename(pdf_path))[0]  
        document_type = input("Enter document type: ")
        document_link = "N/A"
        issuer = input("Enter issuer name: ")
        resource_name = input("Enter resource name: ")

    elif choice == "4":
        url = input("Enter website URL: ")
        raw_text = scrape_website_text(url)  
        document_name = input("Enter document name: ")
        document_type = "Market"
        document_link = url
        issuer = input("Enter issuer name: ")
        resource_name = input("Enter resource name: ")

    else:
        print("❌ Invalid choice. Please restart the script.")
        return

    # Use document name as the JSON filename
    json_filename = f"{document_name.replace(' ', '_')}.json"

    # Create JSON data
    document_json = {
        "company": issuer,
        "documents": [create_json_entry(document_name, document_type, document_link, issuer, resource_name, raw_text)]
    }

    # Save JSON file
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(document_json, json_file, indent=4)

    print(f"✅ Scraped data saved to {json_filename}")

if __name__ == "__main__":
    main()
