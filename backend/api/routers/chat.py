"""
backend/api/routers/chat.py
RAG Chat & Multimodal Media Attachment endpoint.
Supports:
  - Text financial questions
  - Uploading PDFs, DOCs, TXT files
  - Uploading Chart Screenshots & Images (PNG, JPG, WebP)
"""

import os
import uuid
import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from backend.api.dependencies import get_chatbot
from backend.models.schemas import ChatRequest, ChatResponse
from src.rag.chatbot import FinancialChatbot
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

_sessions: dict = {}

SUGGESTED_QUESTIONS = {
    "AAPL": [
        "What are the main risk factors Apple mentioned in their 10-K?",
        "How has Apple's revenue trended recently?",
        "What did analysts say about iPhone sales?",
        "What is Apple's outlook for next quarter?",
    ],
    "MSFT": [
        "What is Microsoft's Azure cloud growth strategy?",
        "How is Microsoft performing in the AI space?",
        "What are Microsoft's main risk factors?",
        "What did Microsoft say about Copilot adoption?",
    ],
    "GOOGL": [
        "How is Google's advertising revenue performing?",
        "What are Alphabet's main AI investments?",
        "What regulatory risks does Google face?",
        "How is Google Cloud competing with AWS and Azure?",
    ],
    "TSLA": [
        "What are Tesla's production and delivery numbers?",
        "How is Tesla's energy storage business growing?",
        "What are the main risks Tesla faces?",
        "What is Tesla's outlook for autonomous driving?",
    ],
    "DEFAULT": [
        "Summarize recent news sentiment for this company.",
        "What are the main risk factors mentioned?",
        "What financial figures were highlighted recently?",
        "What is the overall analyst sentiment?",
    ]
}


@router.post("/upload")
async def upload_attachment(file: UploadFile = File(...)):
    """
    Upload a financial document (PDF, TXT, DOCX) or chart image (PNG, JPG).
    Extracts text/metadata for multimodal Gemini analysis.
    """
    try:
        content = await file.read()
        filename = file.filename
        content_type = file.content_type or ""
        size_kb = round(len(content) / 1024, 1)

        extracted_text = ""

        # Handle PDF
        if "pdf" in content_type or filename.lower().endswith(".pdf"):
            try:
                import pypdf
                import io
                reader = pypdf.PdfReader(io.BytesIO(content))
                pages = [page.extract_text() or "" for page in reader.pages[:15]]
                extracted_text = "\n".join(pages).strip()
            except Exception:
                extracted_text = f"[Attached PDF: {filename} ({size_kb} KB)]"

        # Handle Images (PNG, JPG, WebP)
        elif "image" in content_type or any(filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            b64_img = base64.b64encode(content).decode("utf-8")
            extracted_text = f"[Attached Chart/Image: {filename} ({size_kb} KB)]"
            return {
                "filename": filename,
                "size_kb": size_kb,
                "type": "image",
                "preview": f"data:{content_type};base64,{b64_img[:50]}...",
                "extracted_text": extracted_text,
            }

        # Handle Text / Markdown
        else:
            try:
                extracted_text = content.decode("utf-8", errors="ignore")[:10000]
            except Exception:
                extracted_text = f"[Attached Document: {filename}]"

        return {
            "filename": filename,
            "size_kb": size_kb,
            "type": "document",
            "extracted_text": extracted_text[:4000],
        }
    except Exception as e:
        logger.error(f"File upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


@router.post("", response_model=ChatResponse)
async def chat(
    request:    ChatRequest,
    chatbot_:   FinancialChatbot = Depends(get_chatbot),
):
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in _sessions:
        _sessions[session_id] = FinancialChatbot()

    session_bot = _sessions[session_id]

    try:
        result = session_bot.ask(
            question = request.question,
            ticker   = request.ticker,
            top_k    = request.top_k,
        )
        return ChatResponse(
            answer           = result["answer"],
            sources          = result["sources"],
            retrieved_chunks = result["retrieved_chunks"],
            session_id       = session_id,
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session's conversation history."""
    if session_id in _sessions:
        _sessions[session_id].clear_history()
        del _sessions[session_id]
    return {"cleared": True}


@router.get("/suggestions/{ticker}")
async def get_suggestions(ticker: str):
    questions = SUGGESTED_QUESTIONS.get(
        ticker.upper(),
        SUGGESTED_QUESTIONS["DEFAULT"]
    )
    return {"ticker": ticker, "suggestions": questions}
