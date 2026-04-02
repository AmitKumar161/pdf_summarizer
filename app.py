from __future__ import annotations

import re
from collections import Counter
from io import BytesIO
from typing import Any

from flask import Flask, render_template, request
from PyPDF2 import PdfReader

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "this",
    "these",
    "those",
    "or",
    "not",
    "but",
    "we",
    "you",
    "they",
    "their",
    "our",
}


def extract_text_and_page_count(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from a PDF and return the text plus page count."""
    reader = PdfReader(BytesIO(file_bytes))
    pages_text: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(page_text)

    return "\n".join(pages_text).strip(), len(reader.pages)


def generate_summary(text: str, max_sentences: int = 5) -> str:
    """Generate an extractive summary using sentence scoring."""
    cleaned_text = " ".join(text.split())
    if not cleaned_text:
        return "No readable text was found in this PDF."

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned_text) if s.strip()]
    if len(sentences) <= max_sentences:
        return cleaned_text

    words = re.findall(r"\b[a-zA-Z]{3,}\b", cleaned_text.lower())
    filtered_words = [word for word in words if word not in STOPWORDS]
    if not filtered_words:
        return " ".join(sentences[:max_sentences])

    frequencies = Counter(filtered_words)
    max_frequency = max(frequencies.values())
    normalized = {word: freq / max_frequency for word, freq in frequencies.items()}

    sentence_scores: list[tuple[int, float]] = []
    for idx, sentence in enumerate(sentences):
        sentence_words = re.findall(r"\b[a-zA-Z]{3,}\b", sentence.lower())
        filtered_sentence_words = [w for w in sentence_words if w not in STOPWORDS]
        if not filtered_sentence_words:
            continue

        score = sum(normalized.get(w, 0) for w in filtered_sentence_words) / len(
            filtered_sentence_words
        )
        sentence_scores.append((idx, score))

    if not sentence_scores:
        return " ".join(sentences[:max_sentences])

    top_indices = {
        idx
        for idx, _ in sorted(sentence_scores, key=lambda item: item[1], reverse=True)[
            :max_sentences
        ]
    }
    ordered_summary = [sentence for i, sentence in enumerate(sentences) if i in top_indices]
    return " ".join(ordered_summary)


def build_result_context(
    filename: str,
    summary: str,
    error: bool,
    word_count: int = 0,
    sentence_count: int = 0,
    page_count: int = 0,
) -> dict[str, Any]:
    return {
        "filename": filename,
        "summary": summary,
        "error": error,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "page_count": page_count,
    }


@app.route("/", methods=["GET"])
def index() -> str:
    return render_template("index.html")


@app.errorhandler(413)
def file_too_large(_: Exception) -> tuple[str, int]:
    return (
        render_template(
            "result.html",
            **build_result_context(
                filename="Upload too large",
                summary="File exceeds the 16MB upload limit. Please upload a smaller PDF.",
                error=True,
            ),
        ),
        413,
    )


@app.route("/summarize", methods=["POST"])
def summarize() -> str:
    uploaded_file = request.files.get("pdf_file")

    if uploaded_file is None or uploaded_file.filename == "":
        return render_template(
            "result.html",
            **build_result_context(
                filename="No file selected",
                summary="Please go back and upload a valid PDF file.",
                error=True,
            ),
        )

    if not uploaded_file.filename.lower().endswith(".pdf"):
        return render_template(
            "result.html",
            **build_result_context(
                filename=uploaded_file.filename,
                summary="Only PDF files are supported.",
                error=True,
            ),
        )

    try:
        file_bytes = uploaded_file.read()
        if not file_bytes:
            return render_template(
                "result.html",
                **build_result_context(
                    filename=uploaded_file.filename,
                    summary="The uploaded PDF appears to be empty.",
                    error=True,
                ),
            )

        extracted_text, page_count = extract_text_and_page_count(file_bytes)
        summary = generate_summary(extracted_text)
        sentence_count = len(
            [s for s in re.split(r"(?<=[.!?])\s+", summary.strip()) if s.strip()]
        )
        word_count = len(summary.split())

        return render_template(
            "result.html",
            **build_result_context(
                filename=uploaded_file.filename,
                summary=summary,
                error=False,
                word_count=word_count,
                sentence_count=sentence_count,
                page_count=page_count,
            ),
        )
    except Exception:
        return render_template(
            "result.html",
            **build_result_context(
                filename=uploaded_file.filename,
                summary="Something went wrong while processing your PDF. Please try another file.",
                error=True,
            ),
        )


if __name__ == "__main__":
    app.run(debug=True)
