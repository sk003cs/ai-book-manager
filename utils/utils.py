import logging
import os
import constants.app as AppConstant
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from langchain_community.document_loaders import (
    CSVLoader, UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader, 
    TextLoader, UnstructuredRTFLoader, UnstructuredImageLoader, 
    PyMuPDFLoader, PDFPlumberLoader
)
from langchain.docstore.document import Document
from langchain.text_splitter import TokenTextSplitter
from typing import List
import pandas as pd
from utils.document_loaders import CustomPDFLoader
from cleantext import clean
import requests

# Initialize the logger instance for App
logger = logging.getLogger(AppConstant.LoggerNames.APP.value)

# Dictionary mapping file extensions to the corresponding document loader classes
LoaderMap = {
    "pdf": CustomPDFLoader,
    "doc": UnstructuredWordDocumentLoader,
    "docx": UnstructuredWordDocumentLoader,
    "ppt": UnstructuredPowerPointLoader,
    "pptx": UnstructuredPowerPointLoader,
    "txt": TextLoader,
    "rtf": UnstructuredRTFLoader,
    "csv": CSVLoader,
    "jpg": UnstructuredImageLoader,
    "jpeg": UnstructuredImageLoader,
    "png": UnstructuredImageLoader,
    "gif": UnstructuredImageLoader
}

# Convert an Excel file to CSV format
def xls_to_csv(xls_file_path: str) -> str:
    """Converts an Excel (.xls/.xlsx) file to CSV format."""
    try:
        df = pd.read_excel(xls_file_path)  # Load Excel file into a DataFrame
        csv_file_path = f"{xls_file_path}.csv"
        df.to_csv(csv_file_path, index=False)  # Save DataFrame to CSV
        logger.info(f"Successfully converted Excel file to CSV: {csv_file_path}")
        return csv_file_path
    except Exception as e:
        logger.exception(f"Error converting Excel to CSV: {xls_file_path} -- {repr(e)}")
        raise e

# Process an unstructured file and return the extracted documents
def extract_text(filepath: str, max_tokens: int, remove_file: bool = False) -> List[Document]:
    """Loads and processes documents from various unstructured file formats."""
    logger.debug(f"Starting document extraction for file: {filepath}")

    file_extension = os.path.splitext(filepath)[-1][1:]  # Get the file extension without the dot
    documents: List[Document] = []
    try:
        # Check if the file is a supported type
        if file_extension in {"pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "rtf", "csv", "jpg", "jpeg", "png", "gif"}:
            csv_file_path = None  # Placeholder for potential Excel to CSV conversion

            # Load the document using the appropriate loader
            document_loader = LoaderMap.get(file_extension)
            if document_loader:
                loader = document_loader(filepath)
            elif file_extension in {"xls", "xlsx"}:
                csv_file_path = xls_to_csv(filepath)
                loader = CSVLoader(file_path=csv_file_path)
            
            # If a loader is found, load the documents
            if loader:
                documents = loader.load()
                
                if remove_file:
                    os.remove(filepath)  # Delete the file
                    if csv_file_path: 
                        os.remove(csv_file_path)  # Delete csv file which is converted xls to csv

        if max_tokens and len(documents) > 0:
            # Merge all document content
            page_content = ""
            metadata = documents[0].metadata
            for document in documents:
                page_content += document.page_content
            documents = [Document(page_content=page_content, metadata=metadata)]

            # Update document metadata with file type
            for document in documents:
                document.metadata["file_type"] = file_extension

            # Clean HTML content in text files
            if os.path.splitext(filepath)[1] in {'.txt', '.html'}:
                for doc in documents:
                    doc.page_content = clean(BeautifulSoup(doc.page_content, "html.parser").get_text())
            
            token_splitter = TokenTextSplitter(
                chunk_size = max_tokens, 
                chunk_overlap = round((max_tokens * .10) / 100) * 100
            )
            documents = token_splitter.split_documents(documents)
    except Exception as e:
        logger.exception(f"Error processing unstructured file: {filepath} -- {repr(e)}")
        raise e
    
    logger.debug(f"Document extraction completed for file: {filepath}")
    return documents

def get_sentence_embeddings(text: str, model: str = "sentence-transformers/distilbert-base-nli-mean-tokens") -> dict:
    """
    Fetches sentence embeddings for the input text using the Hugging Face API.
    
    Args:
        text (str): The input text for which embeddings are to be generated.
        model (str): The model to be used for generating embeddings. Defaults to 'distilbert-base-nli-mean-tokens'.
    
    Returns:
        dict: The response from the API containing sentence embeddings.
    """
    # API key for Hugging Face authentication
    api_key = ""  # Replace with your actual API key
    
    # Construct the API URL for the model
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    
    # Set up the headers including the authorization token
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Prepare the payload with the input text
    payload = {"inputs": text}
    
    # Make a POST request to the API with the headers and payload
    response = requests.post(api_url, headers=headers, json=payload)
    
    # Return the JSON response from the API
    return response.json()