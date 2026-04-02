# pdf_summarizer
# PDF Summarizer (Flask)

A modern Flask web app that accepts a PDF upload, extracts text using `PyPDF2`, and returns a concise summary in a clean results UI.

## Features
- Drag-and-drop or click-to-upload PDF flow
- PDF text extraction with `PyPDF2`
- Lightweight extractive summary generation
- Modern glassmorphism-inspired UI with gradient background
- Responsive layout for mobile and desktop
- Summary metadata (pages, sentences, words)

## Project Structure
- `app.py` — Flask routes and summarization logic
- `templates/index.html` — Upload page
- `templates/result.html` — Summary page
- `static/css/style.css` — Styling and animations
- `static/js/app.js` — Drag/drop and client-side validation
- `requirements.txt` — Python dependencies

## Run Locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Run Tests
```bash
pytest -q
```
