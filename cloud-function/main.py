import functions_framework
import os
import tempfile
import fitz
from fpdf import FPDF
from google.cloud import storage
from vertexai.generative_models import GenerativeModel
import vertexai

PROJECT_ID = os.getenv("PROJECT_ID", "eight-brothers")
REGION = os.getenv("REGION", "us-central1")
MODEL_NAME = "gemini-2.5-flash-preview-05-20"
FONT_PATH = os.path.join(os.path.dirname(__file__), "NotoSans-Regular.ttf")

vertexai.init(project=PROJECT_ID, location=REGION)
chat = GenerativeModel(MODEL_NAME).start_chat(history=[])

def extract_text(file_path):
    if file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_path.endswith(".pdf"):
        doc = fitz.open(file_path)
        return "\n".join(page.get_text() for page in doc)
    else:
        raise ValueError("Unsupported file type")

def translate_text(text, target_language="English"):
    if not chat:
        raise RuntimeError("Gemini not initialized")
    prompt = f"""Detect the language and translate to {target_language}. Return only the translation.

    ```{text[:3000]}```"""
    response = chat.send_message(prompt)
    if not response.text.strip():
        raise ValueError("Translation returned empty response")
    return response.text

class UnicodePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.add_font("NotoSans", "", FONT_PATH, uni=True)
        self.set_font("NotoSans", "", 11)

    def add_text(self, lines):
        for line in lines:
            self.multi_cell(0, 6, line.strip())
        self.ln(1)

def process_and_upload(bucket_name, source_blob_name):
    print(f"[INFO] Processing: {source_blob_name}")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    _, ext = os.path.splitext(source_blob_name)
    if ext not in [".txt", ".pdf"]:
        print(f"[WARN] Unsupported file extension: {ext}")
        return

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_input:
        blob.download_to_filename(temp_input.name)
        print(f"[INFO] Downloaded to temp: {temp_input.name}")

    try:
        text = extract_text(temp_input.name)
        print(f"[INFO] Extracted text (preview): {text[:100]}")
    except Exception as e:
        print(f"[ERROR] Text extraction failed: {e}")
        return

    try:
        translated = translate_text(text)
        print(f"[INFO] Translation successful. Preview: {translated[:100]}")
    except Exception as e:
        print(f"[ERROR] Translation failed: {e}")
        return

    try:
        pdf = UnicodePDF()
        pdf.add_text(translated.splitlines())
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_output:
            pdf.output(temp_output.name)
            output_blob_name = source_blob_name.replace("Upload/", "Download/").rsplit(".", 1)[0] + "-translated.pdf"
            bucket.blob(output_blob_name).upload_from_filename(temp_output.name)
            print(f"[SUCCESS] Uploaded PDF to: gs://{bucket_name}/{output_blob_name}")
    except Exception as e:
        print(f"[ERROR] PDF generation/upload failed: {e}")

@functions_framework.cloud_event
def gcs_trigger(cloud_event):
    try:
        data = cloud_event.data
        bucket_name = data["bucket"]
        file_name = data["name"]
        if not file_name.startswith("Upload/"):
            print(f"[INFO] Skipping: {file_name}")
            return
        process_and_upload(bucket_name, file_name)
    except Exception as e:
        import traceback
        print(f"[FATAL] Error in trigger: {e}")
        traceback.print_exc()

