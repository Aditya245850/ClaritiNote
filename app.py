from flask import Flask, request, render_template
from pdf2image import convert_from_path
import os
from openai import OpenAI
import cv2

from OCR_pipline import binarize_image, denoise_image, sharpen_image
from textract import perform_ocr

client = OpenAI(api_key='')

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    pdf_text = None
    summarized_text = None

    if request.method == 'POST':
        pdf = request.files.get('file')
        if pdf:
            pdf.save("saved_pdf.pdf")

            pages = convert_from_path("saved_pdf.pdf")

            pdf_text = ""
            for page in pages:
                page.save("page.png")

                image = cv2.imread("page.png")

                image = denoise_image(image)

                image = sharpen_image(image)

                image = binarize_image(image)

                cv2.imwrite("preprocessed_page.png", image)

                extracted_text = perform_ocr("preprocessed_page.png")

                pdf_text += extracted_text + "\n"

                os.remove("page.png")

            os.remove("saved_pdf.pdf")
            os.remove("preprocessed_page.png")

            chat_completion = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes content."},
                    {"role": "user", "content": f"Please summarize the following text: {pdf_text}"}
                ],
                max_tokens=150
            )
            summarized_text = chat_completion.choices[0].message.content

    return render_template('index.html', summarized_text=summarized_text)


if __name__ == '__main__':
    app.run(debug=True)