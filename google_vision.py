from google.cloud import vision
import io
import os
from dotenv import load_dotenv
import pdfplumber
import PyPDF2
load_dotenv()


def detect_text_image(path):
    """Detects text in the file and prints only the words."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        # The first element in text_annotations contains all the text in the image
        # Each subsequent element is a word or line
        print("Detected words:")
        print(" ".join(text.description for text in texts[1:]))
    else:
        print("No text detected in the image.")

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    
def convert_pdf_to_images(file):
    """Convert PDF pages to images."""
    images = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            im = page.to_image()
            img = im.original
            images.append(img)
    return images

def process_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text


def detect_text_pdf(pdf_path,watermark):
    
    """Detects text in a PDF file."""
    if not watermark:
        print('Extracting without watermark...')
        text=process_pdf(pdf_path)
        return text
    else:
        print('Extracting with watermark...')
        client = vision.ImageAnnotatorClient()
        
        # Extract images from PDF
        images = convert_pdf_to_images(pdf_path)
        
        all_text = []
        
        for i, image in enumerate(images):
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            content = img_byte_arr.getvalue()
            
            vision_image = vision.Image(content=content)
            response = client.text_detection(image=vision_image)
            texts = response.text_annotations
            
            if texts:
                page_text = texts[0].description  # Get all text from the page
                all_text.append(f"\n{page_text}\n")
            
            if response.error.message:
                raise Exception(
                    '{}\nFor more info on error messages, check: '
                    'https://cloud.google.com/apis/design/errors'.format(
                        response.error.message))
        print("Done extracting...")
        
        return "\n".join(all_text)


def read_text_from_image(image_path):
    # Create a client
    client = vision.ImageAnnotatorClient()

    # Load the image from the file system
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    # Construct an image instance
    image = vision.Image(content=content)

    # Perform text detection on the image
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        raise Exception(f"Error with the vision API: {response.error.message}")

    # Return the detected text
    if texts:
        return texts[0].description.strip()
    else:
        return "No text found in the image."

