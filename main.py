import os, io
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import pdfplumber, openai

app = FastAPI()
templates = Jinja2Templates(directory="templates")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")
openai.api_key = OPENAI_KEY

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDFs accepted")

    data = await file.read()
    pdf_stream = io.BytesIO(data)
    with pdfplumber.open(pdf_stream) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    instr = """
You are a professional real estate AI that creates deal summaries ONLY for office & industrial.
Output exactly this format (no extras):

**[Property Name]** (…) … [your template here].
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": instr},
            {"role": "user",   "content": text[:20000]}
        ],
        temperature=0.2
    )
    summary = resp.choices[0].message.content.strip()
    return templates.TemplateResponse("result.html", {
        "request": request,
        "summary": summary
    })
