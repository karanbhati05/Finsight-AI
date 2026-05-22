# src/nlp/ner.py

import spacy
import pandas as pd
from collections import Counter, defaultdict
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Entity types we care about in financial text
# spaCy's en_core_web_sm recognizes 18 types — we filter to the relevant ones
FINANCIAL_ENTITY_TYPES = {
    "ORG":     "Company / Organization",   # Apple, Goldman Sachs, Federal Reserve
    "PERSON":  "Person",                   # Tim Cook, Jerome Powell, Elon Musk
    "MONEY":   "Money Amount",             # $3.2 billion, €500 million
    "PERCENT": "Percentage",               # 12.5%, down 8%
    "DATE":    "Date / Period",            # Q3 2024, fiscal year, January
    "GPE":     "Country / City",           # United States, New York, China
    "PRODUCT": "Product / Service",        # iPhone, Azure, ChatGPT
    "EVENT":   "Event",                    # earnings call, IPO, merger
}


class FinancialNER:
    """
    Named Entity Recognition for financial documents.

    Uses spaCy's en_core_web_sm model — lightweight but effective
    for standard financial entity types.

    For production you'd fine-tune on financial text or use a
    dedicated model like dslim/bert-base-NER, but en_core_web_sm
    is sufficient for this project.

    Usage:
        ner = FinancialNER()
        entities = ner.extract_entities("Apple CEO Tim Cook said revenue hit $89.5 billion")
        # [{'text': 'Apple', 'label': 'ORG', ...},
        #  {'text': 'Tim Cook', 'label': 'PERSON', ...},
        #  {'text': '$89.5 billion', 'label': 'MONEY', ...}]
    """

    def __init__(self, model: str = "en_core_web_sm"):
        """
        Load spaCy model.
        Run: python -m spacy download en_core_web_sm (once, during setup)
        """
        logger.info(f"Loading spaCy model: {model}")
        try:
            self.nlp = spacy.load(model)
        except OSError:
            raise OSError(
                f"spaCy model '{model}' not found.\n"
                f"Run: python -m spacy download {model}"
            )

        # Disable pipeline components we don't need — speeds up processing
        # We only need 'ner', not 'parser' or 'textcat'
        self.nlp.select_pipes(enable=["tok2vec", "ner"])
        logger.info("spaCy NER ready")


    def extract_entities(self, text: str) -> list[dict]:
        """
        Extract named entities from a single text string.

        Args:
            text: cleaned text (use clean_for_ner() from preprocessor.py)

        Returns:
            List of entity dicts with keys:
                text:        the entity string e.g. "Tim Cook"
                label:       entity type e.g. "PERSON"
                label_desc:  human readable e.g. "Person"
                start:       character start position in text
                end:         character end position in text
        """
        if not text or not text.strip():
            return []

        # spaCy has a character limit — guard against very long texts
        doc = self.nlp(text[:100_000])

        entities = []
        seen = set()   # deduplicate identical entities in same document

        for ent in doc.ents:
            if ent.label_ not in FINANCIAL_ENTITY_TYPES:
                continue

            # Normalize the entity text for deduplication
            # "Apple Inc." and "Apple" should count as the same entity
            normalized = ent.text.strip().rstrip(".,")

            # Skip very short entities — usually noise
            if len(normalized) < 2:
                continue

            dedup_key = (normalized.lower(), ent.label_)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            entities.append({
                "text":       normalized,
                "label":      ent.label_,
                "label_desc": FINANCIAL_ENTITY_TYPES[ent.label_],
                "start":      ent.start_char,
                "end":        ent.end_char,
            })

        return entities


    def get_entity_summary(self, texts: list[str]) -> dict:
        """
        Aggregate entity counts across a collection of texts.
        Used by the dashboard to show "most mentioned companies this week."

        Args:
            texts: list of article texts

        Returns:
            Dict mapping entity type → list of (entity_text, count) tuples
            e.g. {"ORG": [("Apple", 47), ("Microsoft", 31), ...],
                  "PERSON": [("Tim Cook", 23), ...], ...}
        """
        logger.info(f"Running NER on {len(texts)} texts...")
        entity_counts = defaultdict(Counter)

        for i, text in enumerate(texts):
            entities = self.extract_entities(text)
            for ent in entities:
                entity_counts[ent["label"]][ent["text"]] += 1

            if (i + 1) % 100 == 0:
                logger.info(f"  NER progress: {i+1}/{len(texts)}")

        # Convert to sorted list of (text, count) tuples
        summary = {}
        for label, counter in entity_counts.items():
            summary[label] = counter.most_common(10)

        return summary


    def analyze_dataframe(
        self,
        df:       pd.DataFrame,
        text_col: str = "content_ner",
    ) -> pd.DataFrame:
        """
        Add entity columns to a news DataFrame.

        Adds two columns:
            entities:      list of entity dicts for each article
            entity_orgs:   comma-separated company names (for easy filtering)

        Args:
            df:       news DataFrame with cleaned NER text column
            text_col: column containing text cleaned for NER

        Returns:
            DataFrame with added entity columns
        """
        logger.info(f"Running NER on DataFrame with {len(df)} rows...")
        df = df.copy()

        all_entities = []
        all_orgs     = []

        for text in df[text_col].fillna(""):
            entities = self.extract_entities(text)
            all_entities.append(entities)

            # Extract just ORG entities as a comma-separated string
            # Useful for filtering articles by company in the dashboard
            orgs = [e["text"] for e in entities if e["label"] == "ORG"]
            all_orgs.append(", ".join(orgs[:5]))   # cap at 5 to keep manageable

        df["entities"]    = all_entities
        df["entity_orgs"] = all_orgs

        # Log how many articles had at least one entity found
        n_with_entities = sum(1 for e in all_entities if e)
        logger.info(
            f"NER complete | {n_with_entities}/{len(df)} articles had entities"
        )

        return df


    def extract_financial_figures(self, text: str) -> dict:
        """
        Specialized extractor for financial figures mentioned in text.
        Returns structured dict of money amounts and percentages found.

        Useful for the RAG chatbot to answer questions like
        "What revenue figures were mentioned?"

        Args:
            text: article or filing text

        Returns:
            dict with 'amounts' and 'percentages' lists
        """
        entities = self.extract_entities(text)

        return {
            "amounts":     [e["text"] for e in entities if e["label"] == "MONEY"],
            "percentages": [e["text"] for e in entities if e["label"] == "PERCENT"],
            "companies":   [e["text"] for e in entities if e["label"] == "ORG"],
            "people":      [e["text"] for e in entities if e["label"] == "PERSON"],
        }