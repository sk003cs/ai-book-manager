import pdftotext
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyMuPDFLoader
import constants.app as AppConstant
import logging
import utils

# Setting up the logger
logger = logging.getLogger(AppConstant.LoggerNames.APP.value)

class CustomPDFLoader:
    def __init__(self, file_path):
        """
        Initializes the loader with the path to the PDF file.

        Parameters:
        - file_path (str): The path to the PDF file.
        """
        self.file_path = file_path
        self.pdf = None
        self.data = None
        self.metadata = {}
        logger.debug(f"Initialized CustomPDFLoader with file_path: {file_path}")

    def load(self):
        """
        Loads the PDF file and returns a list of LangChain Document objects, 
        each representing a page in the PDF.

        Returns:
        - List[Document]: A list of Document objects, one for each page.
        """
        logger.debug("Starting to load the PDF file.")
        # Open the PDF file in binary read mode
        with open(self.file_path, "rb") as f:
            logger.debug(f"Opened file {self.file_path}")
            # Load the PDF using pdftotext
            self.pdf = pdftotext.PDF(f)
            logger.debug(f"Loaded PDF with {len(self.pdf)} pages")
            # Combine all pages into a single string
            self.data = "\n\n".join(self.pdf)
            # Set metadata with the total number of pages
            self.metadata['metadata'] = {"total_pages": len(self.pdf)}
            logger.debug(f"Combined text length: {len(self.data)}")

        # If the combined text is less than 10 characters, use PyMuPDFLoader for more detailed extraction
        if len(self.data) < 10:
            logger.debug("Combined text is less than 10 characters, using PyMuPDFLoader for detailed extraction.")
            loader = PyMuPDFLoader(self.file_path, extract_images=True)
            # Load and split the PDF content into separate Document objects
            self.data = loader.load()
            logger.debug("Loaded data using PyMuPDFLoader")
        else:
            logger.debug("Creating Document objects from each page using pdftotext output.")
            # Otherwise, create Document objects from each page using pdftotext output
            self.data = [Document(page_content=page, metadata=self.metadata) for page in self.pdf]
            logger.debug(f"Created {len(self.data)} Document objects")

        logger.debug("Finished loading the PDF file.")
        return self.data
