from quart import Quart, request, render_template, Response
from pdf2image import convert_from_path
import os
import asyncio
import uuid
import json
from openai import AsyncOpenAI
import cv2
from dotenv import load_dotenv

load_dotenv()

from preprocessing_pipeline import binarize_image, denoise_image, sharpen_image
from textract import perform_ocr

client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Quart(__name__)

jobs = {}
job_events = {}


def process_page(page, page_idx, job_id):
    page_path = f"page_{job_id}_{page_idx}.png"
    preprocessed_path = f"preprocessed_{job_id}_{page_idx}.png"

    page.save(page_path)
    image = cv2.imread(page_path)
    image = denoise_image(image)
    image = sharpen_image(image)
    image = binarize_image(image)
    cv2.imwrite(preprocessed_path, image)

    text = perform_ocr(preprocessed_path)

    os.remove(page_path)
    os.remove(preprocessed_path)
    return text


async def run_pipeline(job_id, pdf_path):
    try:
        loop = asyncio.get_event_loop()
        pages = await loop.run_in_executor(None, convert_from_path, pdf_path)

        page_texts = await asyncio.gather(*[
            loop.run_in_executor(None, process_page, page, idx, job_id)
            for idx, page in enumerate(pages)
        ])

        pdf_text = "\n".join(page_texts)
        os.remove(pdf_path)

        chat_completion = await client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes content."},
                {"role": "user", "content": f"Please summarize the following text: {pdf_text}"}
            ],
            max_tokens=500
        )
        jobs[job_id] = {"status": "done", "result": chat_completion.choices[0].message.content}
    finally:
        if jobs[job_id]["status"] == "pending":
            jobs[job_id] = {"status": "error", "result": "Processing failed"}
        event = job_events.pop(job_id, None)
        if event:
            event.set()


@app.route('/', methods=['GET', 'POST'])
async def upload_file():
    files = await request.files
    pdf = files.get('file')
    if not pdf:
        return await render_template('index.html', job_id=None, job_name=None)

    job_id = str(uuid.uuid4())
    job_name = pdf.filename
    pdf_path = f"saved_pdf_{job_id}.pdf"
    await pdf.save(pdf_path)

    jobs[job_id] = {"status": "pending", "result": None}
    job_events[job_id] = asyncio.Event()
    asyncio.create_task(run_pipeline(job_id, pdf_path))

    return await render_template('index.html', job_id=job_id, job_name=job_name)


@app.route('/stream/<job_id>')
async def stream(job_id):
    async def event_stream():
        job = jobs.get(job_id)
        if not job:
            yield f"data: {json.dumps({'status': 'not_found'})}\n\n"
            return

        # If already finished by the time the client connects, send immediately
        if job["status"] in ("done", "error"):
            yield f"data: {json.dumps(job)}\n\n"
            return

        event = job_events.get(job_id)
        if event:
            await event.wait()
        yield f"data: {json.dumps(jobs[job_id])}\n\n"

    return Response(
        event_stream(),
        content_type='text/event-stream',
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


if __name__ == '__main__':
    app.run(debug=True)
