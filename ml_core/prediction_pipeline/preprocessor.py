# ml_core/prediction_pipeline/preprocessor.py

import re
import string
import emoji
import contractions
from typing import List, Dict, Any, Optional
import logging

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk import pos_tag
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Initialize stop words for the simple text_preprocessor function
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))

class TextPreprocessor:
    def __init__(self, use_spacy: bool = False):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.sia = SentimentIntensityAnalyzer()
        self.use_spacy = use_spacy
        
        # Download required NLTK data
        self._download_nltk_data()
        
        # Initialize spaCy if requested
        self.nlp = None
        if use_spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded successfully")
            except OSError:
                logger.warning("spaCy model not found. Please run: python -m spacy download en_core_web_sm")
                self.use_spacy = False
        
        self._setup_custom_stopwords()
        self._setup_regex_patterns()
    
    def _download_nltk_data(self):
        """Download required NLTK data"""
        nltk_data = [
            ('punkt', 'tokenizers/punkt'),
            ('stopwords', 'corpora/stopwords'),
            ('wordnet', 'corpora/wordnet'),
            ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger'),
            ('vader_lexicon', 'sentiment/vader_lexicon'),
            ('punkt_tab', 'tokenizers/punkt_tab')  # Add punkt_tab
        ]
        
        for resource, path in nltk_data:
            try:
                nltk.data.find(path)
            except LookupError:
                try:
                    nltk.download(resource)
                    logger.info(f"Downloaded NLTK resource: {resource}")
                except Exception as e:
                    logger.warning(f"Failed to download {resource}: {e}")
    
    def _setup_custom_stopwords(self):
        """Add domain-specific stopwords"""
        news_stopwords = {
            'said', 'says', 'according', 'reported', 'news', 'article', 
            'read', 'like', 'would', 'could', 'should', 'get', 'also',
            'one', 'two', 'three', 'first', 'last', 'new', 'time', 'year',
            'people', 'government', 'official', 'statement', 'department'
        }
        self.stop_words.update(news_stopwords)
    
    def _setup_regex_patterns(self):
        """Compile regex patterns for efficiency"""
        self.url_pattern = re.compile(r'http\S+|www\S+|https\S+')
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#\w+')
        self.email_pattern = re.compile(r'\S+@\S+')
        self.phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.special_char_pattern = re.compile(r'[^a-zA-Z\s\.\!\?]')
        self.whitespace_pattern = re.compile(r'\s+')
        self.number_pattern = re.compile(r'\b\d+\b')
        self.word_pattern = re.compile(r'\b\w+\b')  # For fallback tokenization
    
    def clean_text(self, text: str, 
                  remove_html: bool = True,
                  remove_urls: bool = True,
                  remove_mentions: bool = True,
                  remove_hashtags: bool = True,
                  remove_emails: bool = True,
                  remove_phones: bool = True,
                  remove_numbers: bool = False,
                  remove_special_chars: bool = True,
                  expand_contractions: bool = True,
                  handle_emojis: bool = True,
                  lowercase: bool = True) -> str:
        """
        Comprehensive text cleaning with customizable options
        """
        if not text or not isinstance(text, str):
            return ""
        
        cleaned_text = text
        
        # Remove HTML tags
        if remove_html:
            cleaned_text = self._remove_html_tags(cleaned_text)
        
        # Remove URLs
        if remove_urls:
            cleaned_text = self.url_pattern.sub('', cleaned_text)
        
        # Remove mentions and hashtags
        if remove_mentions:
            cleaned_text = self.mention_pattern.sub('', cleaned_text)
        if remove_hashtags:
            cleaned_text = self.hashtag_pattern.sub('', cleaned_text)
        
        # Remove email addresses
        if remove_emails:
            cleaned_text = self.email_pattern.sub('', cleaned_text)
        
        # Remove phone numbers
        if remove_phones:
            cleaned_text = self.phone_pattern.sub('', cleaned_text)
        
        # Expand contractions
        if expand_contractions:
            cleaned_text = contractions.fix(cleaned_text)
        
        # Handle emojis
        if handle_emojis:
            cleaned_text = emoji.demojize(cleaned_text, delimiters=(" ", " "))
        
        # Convert to lowercase
        if lowercase:
            cleaned_text = cleaned_text.lower()
        
        # Remove special characters but keep basic punctuation
        if remove_special_chars:
            cleaned_text = self.special_char_pattern.sub(' ', cleaned_text)
        
        # Remove numbers if requested
        if remove_numbers:
            cleaned_text = self.number_pattern.sub('', cleaned_text)
        
        # Remove extra whitespace
        cleaned_text = self.whitespace_pattern.sub(' ', cleaned_text).strip()
        
        return cleaned_text
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        try:
            soup = BeautifulSoup(text, "html.parser")
            return soup.get_text()
        except:
            return text
    
    def _safe_tokenize(self, text: str) -> List[str]:
        """Safely tokenize text with fallback if NLTK tokenization fails"""
        try:
            return word_tokenize(text)
        except LookupError as e:
            logger.warning(f"NLTK tokenization failed, using regex fallback: {e}")
            # Fallback to regex-based tokenization
            return self.word_pattern.findall(text)
    
    def tokenize_and_lemmatize(self, text: str, 
                              remove_stopwords: bool = True,
                              min_token_length: int = 2) -> List[str]:
        """
        Tokenize text and apply lemmatization with POS tagging
        """
        cleaned_text = self.clean_text(text)
        
        # Tokenize with fallback
        tokens = self._safe_tokenize(cleaned_text)
        
        # Remove stopwords and short tokens
        if remove_stopwords:
            tokens = [
                token for token in tokens 
                if token not in self.stop_words and len(token) >= min_token_length
            ]
        
        # POS tagging and context-aware lemmatization
        try:
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
            
            return lemmatized_tokens
        except Exception as e:
            logger.warning(f"POS tagging failed, using simple lemmatization: {e}")
            # Fallback to simple lemmatization without POS tagging
            return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def extract_linguistic_features(self, text: str) -> Dict[str, Any]:
        """
        Extract comprehensive linguistic features from text
        """
        cleaned_text = self.clean_text(text)
        tokens = self.tokenize_and_lemmatize(cleaned_text, remove_stopwords=False)
        
        # Use regex-based sentence tokenization as fallback
        try:
            sentences = sent_tokenize(cleaned_text)
        except:
            sentences = re.split(r'[.!?]+', cleaned_text)
            sentences = [s.strip() for s in sentences if s.strip()]
        
        # Basic statistics
        features = {
            'word_count': len(tokens),
            'sentence_count': len(sentences),
            'char_count': len(text),
            'avg_sentence_length': len(tokens) / len(sentences) if sentences else 0,
            'avg_word_length': sum(len(word) for word in tokens) / len(tokens) if tokens else 0,
            'unique_word_ratio': len(set(tokens)) / len(tokens) if tokens else 0,
            'stopword_ratio': sum(1 for w in tokens if w in self.stop_words) / len(tokens) if tokens else 0,
        }
        
        # Punctuation analysis
        features.update({
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'digit_ratio': sum(1 for c in text if c.isdigit()) / len(text) if text else 0,
        })
        
        # Sentiment analysis
        try:
            sentiment_scores = self.sia.polarity_scores(cleaned_text)
            features.update({
                'sentiment_positive': sentiment_scores['pos'],
                'sentiment_negative': sentiment_scores['neg'],
                'sentiment_neutral': sentiment_scores['neu'],
                'sentiment_compound': sentiment_scores['compound'],
            })
        except:
            features.update({
                'sentiment_positive': 0,
                'sentiment_negative': 0,
                'sentiment_neutral': 1,
                'sentiment_compound': 0,
            })
        
        # Readability scores (simplified)
        if sentences and tokens:
            features['flesch_reading_ease'] = self._calculate_flesch_reading_ease(
                len(sentences), len(tokens), sum(len(word) for word in tokens)
            )
        
        # SpaCy features if available
        if self.use_spacy and self.nlp:
            try:
                doc = self.nlp(cleaned_text)
                features.update({
                    'spacy_entities': len(doc.ents),
                    'spacy_noun_phrases': len(list(doc.noun_chunks)),
                    'spacy_avg_dependency_depth': self._calculate_avg_dependency_depth(doc),
                })
            except:
                features.update({
                    'spacy_entities': 0,
                    'spacy_noun_phrases': 0,
                    'spacy_avg_dependency_depth': 0,
                })
        
        return features
    
    def _calculate_flesch_reading_ease(self, sentences: int, words: int, syllables: int) -> float:
        """Calculate Flesch Reading Ease score"""
        if sentences == 0 or words == 0:
            return 0
        return 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    
    def _calculate_avg_dependency_depth(self, doc) -> float:
        """Calculate average dependency tree depth"""
        depths = []
        for sent in doc.sents:
            depths.append(max(token.head.i for token in sent))
        return sum(depths) / len(depths) if depths else 0
    
    def prepare_for_ml(self, text: str, return_tokens: bool = False):
        """
        Prepare text for machine learning models
        """
        if return_tokens:
            return self.tokenize_and_lemmatize(text)
        else:
            tokens = self.tokenize_and_lemmatize(text)
            return ' '.join(tokens)
    
    def batch_process(self, texts: List[str], n_jobs: int = -1, **kwargs) -> List[str]:
        """
        Process multiple texts efficiently
        """
        if n_jobs == 1:
            return [self.prepare_for_ml(text, **kwargs) for text in texts]
        
        try:
            from joblib import Parallel, delayed
            return Parallel(n_jobs=n_jobs)(
                delayed(self.prepare_for_ml)(text, **kwargs) for text in texts
            )
        except ImportError:
            logger.warning("joblib not available, falling back to sequential processing")
            return [self.prepare_for_ml(text, **kwargs) for text in texts]

# Singleton instance
advanced_text_preprocessor = TextPreprocessor(use_spacy=False)

def text_preprocessor(text: str) -> str:
    """
    Clean and preprocess text for fake news detection.
    Steps:
    - Lowercasing
    - Removing punctuation
    - Removing numbers
    - Removing stopwords
    """
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    
    # Remove numbers
    text = re.sub(r"\d+", "", text)
    
    # Remove stopwords
    words = text.split()
    words = [word for word in words if word not in stop_words]
    
    return " ".join(words)