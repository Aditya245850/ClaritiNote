import boto3
import os
from dotenv import load_dotenv

load_dotenv()

textract = boto3.client(
    'textract',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
def perform_ocr(image_path):
    with open(image_path, 'rb') as document:
        response = textract.detect_document_text(Document={'Bytes': document.read()})

    extracted_text = ''
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            extracted_text += item['Text'] + '\n'

    return extracted_text