# ml_core/training_pipeline/data_cleaning.py
import pandas as pd
import re
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import logging

logger = logging.getLogger(__name__)
class DataPreprocessor:
    def __init__(self):
        try:
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
        except:
            import nltk
            nltk.download('stopwords')
            nltk.download('punkt')
            nltk.download('wordnet')
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
    
    def clean_dataset(df, text_column='text', label_column='label'):
        """
        Wrapper for DataPreprocessor.preprocess_dataset()
        """
        return data_preprocessor.preprocess_dataset(df, text_column, label_column)
    
    def clean_text(self, text):
        """Clean and preprocess text data"""
        if pd.isna(text):
            return ""
            
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)
    
    def preprocess_dataset(self, df, text_column='text', label_column='label'):
        """Preprocess entire dataset"""
        logger.info("Starting dataset preprocessing...")
        
        # Clean text
        df['cleaned_text'] = df[text_column].apply(self.clean_text)
        
        # Remove empty texts
        df = df[df['cleaned_text'].str.len() > 0]
        
        # Ensure label consistency
        if label_column in df.columns:
            df = df[~df[label_column].isna()]
        
        logger.info(f"Preprocessing complete. Final dataset size: {len(df)}")
        return df

# Create instance
data_preprocessor = DataPreprocessor()