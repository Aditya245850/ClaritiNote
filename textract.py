import boto3

textract = boto3.client(
    'textract',
    aws_access_key_id='',
    aws_secret_access_key='',
    region_name=''  
)
def perform_ocr(image_path):
    with open(image_path, 'rb') as document:
        response = textract.detect_document_text(Document={'Bytes': document.read()})

    extracted_text = ''
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            extracted_text += item['Text'] + '\n'

    return extracted_text