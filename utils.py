import os
import tempfile
import google.generativeai as genai
from config import Config

class GeminiProcessor:
    def __init__(self):
        self.config = Config()
        genai.configure(api_key=self.config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro-vision')
        self.text_model = genai.GenerativeModel('gemini-pro')
    
    def image_to_text(self, image_path):
        """Convert image to text using Gemini"""
        try:
            image = genai.upload_file(image_path)
            response = self.model.generate_content(["Extract all text from this legal document.", image])
            return response.text
        except Exception as e:
            raise Exception(f"Gemini image processing failed: {str(e)}")
    
    def pdf_to_text(self, pdf_path):
        """Convert PDF to text using Gemini (page by page)"""
        try:
            # Convert PDF to images first
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path)
            
            full_text = ""
            for img in images:
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    img.save(tmp.name, 'JPEG')
                    full_text += self.image_to_text(tmp.name) + "\n\n"
            return full_text
        except Exception as e:
            raise Exception(f"PDF processing failed: {str(e)}")

def process_uploaded_file(uploaded_file):
    """Handle uploaded files using Gemini"""
    processor = GeminiProcessor()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    
    if uploaded_file.type.startswith('image/'):
        return processor.image_to_text(tmp_path)
    elif uploaded_file.type == 'application/pdf':
        return processor.pdf_to_text(tmp_path)
    else:
        raise Exception("Unsupported file type")