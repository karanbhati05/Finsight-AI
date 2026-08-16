# src/rag/chatbot.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from src.rag.embedder import DocumentEmbedder
from src.rag.vector_store import FinancialVectorStore
from src.rag.retriever import FinancialRetriever
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── System Prompt ────────────────────────────────────────────────────────────
# This is the most important prompt engineering decision in the project.
# It defines the chatbot's persona, rules, and output format.
# Every sentence is deliberate — read the comments carefully.

SYSTEM_PROMPT = """You are FinSight, an expert AI financial research analyst \
assistant built for institutional investors and analysts.

You have access to a curated knowledge base of:
- SEC filings (10-K annual reports, 10-Q quarterly reports, 8-K disclosures)
- Financial news articles from reputable sources
- Earnings call transcripts and analyst reports

YOUR CORE RULES — follow these without exception:

1. GROUNDING: Only answer using information from the provided context documents.
   If the context does not contain enough information to answer, say clearly:
   "I don't have sufficient information in my knowledge base to answer this.
   Please check the latest filings on SEC EDGAR or Bloomberg."

2. CITATIONS: Always cite your sources. Reference them as [Source 1], [Source 2] etc.
   matching the source numbers in the context. Never fabricate source references.

3. PRECISION: Be exact with financial figures. Never round or approximate numbers
   that are explicitly stated in the documents. If the document says $3.847 billion,
   say $3.847 billion — not "approximately $3.8 billion".

4. UNCERTAINTY: If you are uncertain about something, say so explicitly.
   Use phrases like "According to [Source 1]..." or "The filing indicates..."
   rather than stating things as absolute fact.

5. NO HALLUCINATION: Never generate financial figures, dates, executive names,
   or regulatory information that are not present in the provided context.
   In financial contexts, hallucinated numbers can cause real harm.

6. TONE: Professional, concise, and analytical. Write like a senior analyst
   briefing a portfolio manager — clear, structured, no unnecessary hedging.

Context documents:
{context}

If no context is provided or context is empty, tell the user you need to
search for relevant documents first and ask them to be more specific."""


# ── Prompt templates for different question types ────────────────────────────

# Standard Q&A prompt — most questions use this
QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

# Summary prompt — used for "give me an overview of X" questions
SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT + "\n\nProvide a structured summary with sections: "
               "Overview, Key Financial Metrics, Recent Developments, "
               "Risk Factors, and Analyst Outlook."),
    ("human", "Please provide a comprehensive summary for: {question}"),
])


class FinancialChatbot:
    """
    RAG-powered financial Q&A chatbot.

    Full pipeline per question:
        1. Classify question type (specific vs summary)
        2. Retrieve relevant document chunks via FinancialRetriever
        3. Format context with source citations
        4. Call LLM with system prompt + context + conversation history
        5. Parse and return the grounded answer

    Maintains conversation history for multi-turn dialogue:
        User: "What was Apple's revenue in Q3?"
        Bot:  "Apple reported $89.5 billion in Q3 2024 [Source 1]..."
        User: "How does that compare to Q2?"  ← needs history to understand "that"
        Bot:  "Compared to Q2's $85.8 billion, Q3 showed 4.3% growth [Source 2]..."

    Usage:
        bot = FinancialChatbot()
        result = bot.ask("What risks did Apple mention in their latest 10-K?",
                         ticker="AAPL")
        print(result["answer"])
        print(result["sources"])
    """

    def __init__(
        self,
        model_name:   str   = "gemini-2.5-flash",
        temperature:  float = 0.1,
        max_tokens:   int   = 1000,
        embedder:     DocumentEmbedder     = None,
        vector_store: FinancialVectorStore = None,
    ):
        """
        Initialize chatbot with LLM and retrieval components.

        Args:
            model_name:   Google Generative AI model to use
                          "gemini-2.5-flash" — fast, cheap, good for Q&A
                          "gemini-2.5-pro"  — slower, expensive, better reasoning
            temperature:  0.0–1.0 creativity. 0.1 for factual financial answers
                          Low temperature = more deterministic, fewer hallucinations
            max_tokens:   maximum response length
            embedder:     shared embedder instance (avoids reloading model)
            vector_store: shared vector store instance
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GOOGLE_API_KEY not set.\n"
                "Add it to your .env file: GOOGLE_API_KEY=your_key_here\n"
                "Get your key at: https://aistudio.google.com/app/apikey"
            )

        logger.info(f"Initializing FinancialChatbot | model={model_name}")

        # LLM — low temperature for factual financial answers
        self.llm = ChatGoogleGenerativeAI(
            model       = model_name,
            temperature = temperature,
            max_tokens  = max_tokens,
            api_key     = api_key,
        )

        # Retrieval components
        self.embedder     = embedder     or DocumentEmbedder()
        self.vector_store = vector_store or FinancialVectorStore()
        self.retriever    = FinancialRetriever(
            embedder     = self.embedder,
            vector_store = self.vector_store,
        )

        # Output parser — converts LLM message object to plain string
        self.parser = StrOutputParser()

        # Conversation history — list of HumanMessage / AIMessage objects
        # Enables multi-turn conversation with context awareness
        self.history: list = []

        # Session log — all Q&A pairs for this session
        self.session_log: list[dict] = []

        logger.info("FinancialChatbot ready")


    def ask(
        self,
        question:       str,
        ticker:         str   = None,
        top_k:          int   = 5,
        use_history:    bool  = True,
        sentiment_filter: str = None,
    ) -> dict:
        """
        Answer a financial question using RAG.

        This is the main public method — called by the Streamlit chatbot page.

        Args:
            question:         user's natural language question
            ticker:           optional: restrict search to this ticker
                              e.g. "AAPL" — only search Apple documents
            top_k:            number of document chunks to retrieve
            use_history:      include conversation history for multi-turn dialogue
            sentiment_filter: optional: only retrieve docs with this sentiment
                              "positive" / "negative" / "neutral"

        Returns:
            Dict with:
                answer:          LLM's grounded response string
                sources:         list of source metadata dicts
                retrieved_chunks: number of chunks retrieved
                context_used:    the context string passed to LLM
                question:        original question (for logging)
        """
        if not question or not question.strip():
            return {"answer": "Please ask a question.", "sources": []}

        logger.info(f"Question: '{question[:100]}'")

        # ── Step 1: Retrieve relevant context ───────────────────────────────
        context, sources = self.retriever.retrieve(
            query           = question,
            top_k           = top_k,
            ticker          = ticker,
            sentiment       = sentiment_filter,
        )

        if not context:
            no_context_answer = (
                f"I couldn't find relevant documents in my knowledge base "
                f"for your question about {ticker or 'this topic'}. "
                f"This may be because:\n"
                f"• The topic hasn't been covered in the ingested documents\n"
                f"• Try running the pipeline first: "
                f"`python scripts/run_pipeline.py --ticker {ticker or 'AAPL'}`\n"
                f"• Or rephrase your question with different keywords"
            )
            return {
                "answer":           no_context_answer,
                "sources":          [],
                "retrieved_chunks": 0,
                "context_used":     "",
                "question":         question,
            }

        # ── Step 2: Detect question type ─────────────────────────────────────
        is_summary = self._is_summary_question(question)
        prompt     = SUMMARY_PROMPT if is_summary else QA_PROMPT

        # ── Step 3: Build conversation history for LLM ───────────────────────
        # Only include last 6 messages (3 turns) to stay within token limits
        history = self.history[-6:] if use_history else []

        # ── Step 4: Build the chain and invoke ───────────────────────────────
        # LangChain chain: prompt → LLM → output parser
        chain = prompt | self.llm | self.parser

        try:
            answer = chain.invoke({
                "context":  context,
                "history":  history,
                "question": question,
            })
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            answer = (
                f"I encountered an error generating a response: {e}\n"
                f"Please check your OpenAI API key and try again."
            )

        # ── Step 5: Update conversation history ──────────────────────────────
        self.history.append(HumanMessage(content=question))
        self.history.append(AIMessage(content=answer))

        # ── Step 6: Log this Q&A pair ────────────────────────────────────────
        log_entry = {
            "question":         question,
            "answer":           answer,
            "sources":          sources,
            "retrieved_chunks": len(sources),
            "ticker":           ticker,
            "context_length":   len(context),
        }
        self.session_log.append(log_entry)

        logger.info(
            f"Answer generated | "
            f"chunks_used={len(sources)} | "
            f"answer_length={len(answer)}"
        )

        return {
            "answer":           answer,
            "sources":          sources,
            "retrieved_chunks": len(sources),
            "context_used":     context,
            "question":         question,
        }


    def _is_summary_question(self, question: str) -> bool:
        """
        Detect if the question is asking for a broad summary
        rather than a specific fact.

        Summary questions trigger a more structured response format
        with sections (Overview, Financials, Risks, Outlook).

        Args:
            question: user's question string

        Returns:
            True if question is a summary request
        """
        summary_keywords = [
            "summarize", "summary", "overview", "tell me about",
            "what do you know about", "give me a summary",
            "overall", "general", "broadly", "in general",
        ]
        q_lower = question.lower()
        return any(kw in q_lower for kw in summary_keywords)


    def clear_history(self) -> None:
        """
        Clear conversation history.
        Called when user starts a new topic or selects a different ticker.
        """
        self.history = []
        logger.info("Conversation history cleared")


    def get_session_summary(self) -> dict:
        """
        Return a summary of the current chat session.
        Used for logging and the session export feature.

        Returns:
            Dict with question_count, tickers_discussed, session_log
        """
        tickers = list({
            entry["ticker"]
            for entry in self.session_log
            if entry.get("ticker")
        })

        return {
            "question_count":   len(self.session_log),
            "tickers_discussed": tickers,
            "session_log":      self.session_log,
        }


    def ask_without_rag(self, question: str) -> str:
        """
        Ask a general financial question without document retrieval.
        Uses only the LLM's training knowledge — no context injection.

        Use cases:
            - Explaining financial concepts ("What is RSI?")
            - General market questions not requiring specific documents
            - Fallback when no relevant documents are found

        Args:
            question: general financial question

        Returns:
            LLM's answer as a plain string
        """
        general_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a knowledgeable financial analyst. Answer clearly and "
             "concisely. If you're uncertain, say so. Do not fabricate "
             "specific numbers, dates, or company-specific information — "
             "those require document retrieval."),
            ("human", "{question}"),
        ])

        chain  = general_prompt | self.llm | self.parser
        answer = chain.invoke({"question": question})

        logger.info(f"General Q&A (no RAG) | question='{question[:60]}'")
        return answer