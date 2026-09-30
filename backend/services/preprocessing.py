# backend/services/preprocessing.py
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import LabelEncoder
import emoji
import contractions

logger = logging.getLogger(__name__)

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

class TextPreprocessor:
    def __init__(self, use_cache: bool = True):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.use_cache = use_cache
        self._setup_custom_stopwords()
        
        # Cache for expensive operations
        if use_cache:
            self.clean_text = lru_cache(maxsize=1000)(self._clean_text_uncached)
        else:
            self.clean_text = self._clean_text_uncached
    
    def _setup_custom_stopwords(self):
        """Add custom stopwords specific to news domain"""
        custom_stopwords = {
            'said', 'says', 'according', 'reported', 'news', 'article', 
            'read', 'like', 'would', 'could', 'should', 'get', 'also'
        }
        self.stop_words.update(custom_stopwords)
    
    def _clean_text_uncached(self, text: str) -> str:
        """
        Comprehensive text cleaning and preprocessing
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Expand contractions
        text = contractions.fix(text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove user mentions and hashtags
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', text)
        
        # Remove special characters and numbers but keep basic punctuation
        text = re.sub(r'[^a-zA-Z\s\.\!\?]', ' ', text)
        
        # Handle emojis - convert to text description or remove
        text = emoji.demojize(text, delimiters=(" ", " "))
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and short tokens
        tokens = [
            token for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        # POS tagging and lemmatization with context
        pos_tags = pos_tag(tokens)
        lemmatized_tokens = []
        
        for token, pos in pos_tags:
            if pos.startswith('V'):  # Verbs
                lemma = self.lemmatizer.lemmatize(token, pos='v')
            elif pos.startswith('J'):  # Adjectives
                lemma = self.lemmatizer.lemmatize(token, pos='a')
            elif pos.startswith('R'):  # Adverbs
                lemma = self.lemmatizer.lemmatize(token, pos='r')
            else:  # Nouns and others
                lemma = self.lemmatizer.lemmatize(token, pos='n')
            lemmatized_tokens.append(lemma)
        
        return ' '.join(lemmatized_tokens)
    
    def batch_preprocess(self, texts: List[str], n_jobs: int = 4) -> List[str]:
        """
        Preprocess multiple texts in parallel
        """
        if n_jobs == 1:
            return [self.clean_text(text) for text in texts]
        
        with ThreadPoolExecutor(max_workers=n_jobs) as executor:
            results = list(executor.map(self.clean_text, texts))
        
        return results
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """
        Extract linguistic features from text
        """
        cleaned_text = self.clean_text(text)
        tokens = word_tokenize(cleaned_text)
        
        features = {
            'word_count': len(tokens),
            'char_count': len(text),
            'avg_word_length': np.mean([len(word) for word in tokens]) if tokens else 0,
            'sentence_count': len(re.split(r'[.!?]+', text)),
            'stopword_ratio': len([w for w in tokens if w in self.stop_words]) / len(tokens) if tokens else 0,
            'unique_word_ratio': len(set(tokens)) / len(tokens) if tokens else 0,
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
        }
        
        return features
    
    def create_vectorizer(self, texts: List[str], method: str = 'tfidf', **kwargs) -> Any:
        """
        Create and fit a text vectorizer
        """
        cleaned_texts = self.batch_preprocess(texts)
        
        if method == 'tfidf':
            vectorizer = TfidfVectorizer(
                max_features=kwargs.get('max_features', 5000),
                min_df=kwargs.get('min_df', 2),
                max_df=kwargs.get('max_df', 0.8),
                ngram_range=kwargs.get('ngram_range', (1, 2)),
                stop_words='english',
                **{k: v for k, v in kwargs.items() if k not in ['max_features', 'min_df', 'max_df', 'ngram_range']}
            )
        elif method == 'count':
            vectorizer = CountVectorizer(
                max_features=kwargs.get('max_features', 5000),
                min_df=kwargs.get('min_df', 2),
                max_df=kwargs.get('max_df', 0.8),
                ngram_range=kwargs.get('ngram_range', (1, 2)),
                stop_words='english',
                **{k: v for k, v in kwargs.items() if k not in ['max_features', 'min_df', 'max_df', 'ngram_range']}
            )
        else:
            raise ValueError("Method must be 'tfidf' or 'count'")
        
        vectorizer.fit(cleaned_texts)
        return vectorizer
    
    def prepare_training_data(self, 
                            texts: List[str], 
                            labels: List[Any],
                            vectorizer_method: str = 'tfidf',
                            test_size: float = 0.2,
                            **vectorizer_kwargs) -> Tuple[Any, Any, Any, Any]:
        """
        Prepare data for model training
        """
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder
        
        # Preprocess texts
        cleaned_texts = self.batch_preprocess(texts)
        
        # Create and fit vectorizer
        vectorizer = self.create_vectorizer(
            cleaned_texts, 
            method=vectorizer_method, 
            **vectorizer_kwargs
        )
        
        # Transform texts
        X = vectorizer.transform(cleaned_texts)
        
        # Encode labels
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        return X_train, X_test, y_train, y_test, vectorizer, label_encoder

# Singleton instance
preprocessor = TextPreprocessor()