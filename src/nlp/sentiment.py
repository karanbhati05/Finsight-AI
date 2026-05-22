# src/nlp/sentiment.py

import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ProsusAI/finbert is BERT fine-tuned on ~10,000 financial news sentences
# It understands financial language that generic models misclassify
# e.g. "the stock fell short of expectations" → negative (generic model might miss this)
# e.g. "better than feared" → positive (sarcastic framing that FinBERT handles)
MODEL_NAME = "ProsusAI/finbert"
LABELS     = ["positive", "negative", "neutral"]


class FinBERTSentiment:
    """
    Financial sentiment analyzer using FinBERT.

    Usage:
        model = FinBERTSentiment()
        result = model.predict("Apple reported record revenue beating estimates")
        # {'label': 'positive', 'score': 0.847, 'confidence': 0.923, ...}
    """

    def __init__(self, device: str = None):
        """
        Load FinBERT model and tokenizer.
        First call downloads ~440MB from HuggingFace — cached after that.

        Args:
            device: "cuda", "cpu", or None (auto-detect)
        """
        logger.info(f"Loading FinBERT: {MODEL_NAME}")

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model     = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

        # Auto-detect GPU — falls back to CPU silently
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model.to(self.device)
        self.model.eval()   # disable dropout — we're doing inference not training

        logger.info(f"FinBERT loaded on {self.device}")


    def predict(self, text: str) -> dict:
        """
        Predict sentiment for a single text string.

        Returns a dict with:
            label:      "positive", "negative", or "neutral"
            score:      float from -1.0 (very negative) to +1.0 (very positive)
                        computed as prob_positive - prob_negative
                        This gives a continuous signal better than just the label
            confidence: probability of the predicted label (0.0 to 1.0)
            prob_positive, prob_negative, prob_neutral: raw probabilities

        Why score = positive - negative instead of just the label?
            The ML model downstream needs a continuous feature, not a category.
            "positive with 0.95 confidence" and "positive with 0.51 confidence"
            are very different signals — the score captures this nuance.
        """
        if not text or not text.strip():
            return self._empty_result()

        # Tokenize: convert text to input IDs, attention mask
        # truncation=True: cut to 512 tokens (FinBERT's max)
        # padding=True: pad shorter texts to same length for batching
        inputs = self.tokenizer(
            text,
            return_tensors = "pt",
            truncation     = True,
            max_length     = 512,
            padding        = True,
        ).to(self.device)

        # Inference — no_grad() disables gradient computation (faster, less memory)
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Convert logits to probabilities with softmax
        # logits are raw scores — softmax normalizes them to sum to 1.0
        probs = softmax(outputs.logits, dim=-1).squeeze().cpu().numpy()

        # Map probabilities to label names
        # FinBERT's label order: positive=0, negative=1, neutral=2
        scores = {label: float(prob) for label, prob in zip(LABELS, probs)}

        predicted_label = max(scores, key=scores.get)

        # Continuous sentiment score: +1 = maximally positive, -1 = maximally negative
        sentiment_score = scores["positive"] - scores["negative"]

        return {
            "label":        predicted_label,
            "score":        round(sentiment_score,        4),
            "confidence":   round(scores[predicted_label],4),
            "prob_positive":round(scores["positive"],     4),
            "prob_negative":round(scores["negative"],     4),
            "prob_neutral": round(scores["neutral"],      4),
        }


    def predict_batch(self, texts: list[str], batch_size: int = 16) -> list[dict]:
        """
        Run sentiment prediction on a list of texts.

        Processes in batches for efficiency — loading the model once
        and running 16 texts through simultaneously is much faster
        than 16 separate model calls.

        Args:
            texts:      list of cleaned text strings
            batch_size: how many texts to process at once
                        16 is safe for CPU; increase to 32-64 on GPU

        Returns:
            List of result dicts in same order as input texts
        """
        results = []
        total   = len(texts)

        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]

            # Filter empty strings — model handles them poorly
            processed = []
            empty_indices = set()
            for j, text in enumerate(batch):
                if not text or not text.strip():
                    empty_indices.add(j)
                else:
                    processed.append(text)

            if not processed:
                results.extend([self._empty_result()] * len(batch))
                continue

            # Tokenize entire batch at once
            inputs = self.tokenizer(
                processed,
                return_tensors = "pt",
                truncation     = True,
                max_length     = 512,
                padding        = True,   # pad to longest in batch
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)

            # probs shape: (batch_size, 3)
            probs_batch = softmax(outputs.logits, dim=-1).cpu().numpy()

            # Reconstruct results including empty placeholders
            processed_iter = iter(probs_batch)
            batch_results  = []
            for j in range(len(batch)):
                if j in empty_indices:
                    batch_results.append(self._empty_result())
                else:
                    probs = next(processed_iter)
                    scores = {label: float(p) for label, p in zip(LABELS, probs)}
                    label  = max(scores, key=scores.get)
                    score  = scores["positive"] - scores["negative"]
                    batch_results.append({
                        "label":         label,
                        "score":         round(score,           4),
                        "confidence":    round(scores[label],   4),
                        "prob_positive": round(scores["positive"], 4),
                        "prob_negative": round(scores["negative"], 4),
                        "prob_neutral":  round(scores["neutral"],  4),
                    })

            results.extend(batch_results)

            logger.info(f"Sentiment: {min(i + batch_size, total)}/{total} articles processed")

        return results


    def analyze_dataframe(
        self,
        df:       pd.DataFrame,
        text_col: str = "content_sentiment",
    ) -> pd.DataFrame:
        """
        Add sentiment columns to a news DataFrame.

        Expects the preprocessed column from preprocessor.py
        e.g. "content_sentiment" (cleaned for FinBERT input).

        Args:
            df:       news DataFrame with cleaned text column
            text_col: column containing cleaned text for sentiment

        Returns:
            DataFrame with added columns:
                label, score, confidence,
                prob_positive, prob_negative, prob_neutral
        """
        logger.info(f"Running FinBERT sentiment on {len(df)} articles...")

        texts   = df[text_col].fillna("").tolist()
        results = self.predict_batch(texts)

        sentiment_df = pd.DataFrame(results)

        # Prefix columns to avoid clashes with existing DataFrame columns
        sentiment_df.columns = [f"sentiment_{c}" if c != "label" else "sentiment_label"
                                 for c in sentiment_df.columns]

        result = pd.concat([df.reset_index(drop=True), sentiment_df], axis=1)

        # Log distribution summary
        dist = result["sentiment_label"].value_counts().to_dict()
        logger.info(f"Sentiment distribution: {dist}")

        return result


    def _empty_result(self) -> dict:
        """Return a neutral zero-score result for empty/invalid inputs."""
        return {
            "label":         "neutral",
            "score":          0.0,
            "confidence":     0.0,
            "prob_positive":  0.0,
            "prob_negative":  0.0,
            "prob_neutral":   1.0,
        }