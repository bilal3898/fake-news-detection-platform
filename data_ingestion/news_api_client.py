# data_ingestion/news_api_client.py

import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
from urllib.parse import urlparse
import json
import pandas as pd

from backend.utils.config import get_settings
from backend.database.mongo_connection import get_database
from backend.services.preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)
settings = get_settings()

class NewsAPIClient:
    def __init__(self):
        self.api_key = settings.NEWS_API_KEY

        if not self.api_key:
            logger.warning("⚠️ NEWS_API_KEY not found! Please set it in your .env file.")

        self.base_url = "https://newsapi.org/v2"
        self.headers = {
            "X-Api-Key": self.api_key,
            "User-Agent": "FakeNewsDetection/1.0"
        }

        self.preprocessor = TextPreprocessor()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_top_headlines(self, 
                         country: str = "us",
                         category: Optional[str] = None,
                         page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get top headlines from News API
        """
        if not self.api_key:
            logger.warning("News API key not configured")
            return []
        
        try:
            params = {
                "country": country,
                "pageSize": page_size
            }
            
            if category:
                params["category"] = category
            
            response = self.session.get(
                f"{self.base_url}/top-headlines",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            processed_articles = []
            for article in articles:
                processed_article = self._process_article(article)
                if processed_article:
                    processed_articles.append(processed_article)
            
            logger.info(f"Fetched {len(processed_articles)} articles from News API")
            return processed_articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news from News API: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing News API response: {e}")
            return []

    def save_to_dataset(news_data, dataset_type='external'):
        """Save collected news to dataset directory"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'../dataset/{dataset_type}/news_{timestamp}.csv'
        
        df = pd.DataFrame(news_data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    
    def get_everything(self,
                      query: str,
                      from_date: Optional[str] = None,
                      to_date: Optional[str] = None,
                      language: str = "en",
                      sort_by: str = "publishedAt",
                      page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get all articles matching query from News API
        """
        if not self.api_key:
            logger.warning("News API key not configured")
            return []
        
        try:
            if not from_date:
                from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            if not to_date:
                to_date = datetime.now().strftime("%Y-%m-%d")
            
            params = {
                "q": query,
                "from": from_date,
                "to": to_date,
                "language": language,
                "sortBy": sort_by,
                "pageSize": page_size
            }
            
            response = self.session.get(
                f"{self.base_url}/everything",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            processed_articles = []
            for article in articles:
                processed_article = self._process_article(article)
                if processed_article:
                    processed_articles.append(processed_article)
            
            logger.info(f"Fetched {len(processed_articles)} articles for query: {query}")
            return processed_articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news from News API: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing News API response: {e}")
            return []
    
    def _process_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and clean article data
        """
        try:
            if not article.get("title") or not article.get("url"):
                return None
            
            # Extract domain from URL
            domain = urlparse(article["url"]).netloc
            
            processed_article = {
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "url": article["url"],
                "source": article.get("source", {}).get("name", domain),
                "domain": domain,
                "published_at": article.get("publishedAt"),
                "author": article.get("author", ""),
                "image_url": article.get("urlToImage", ""),
                "language": "en",
                "category": "news",
                "ingestion_time": datetime.utcnow().isoformat(),
                "processed_text": self._prepare_text_for_processing(article)
            }
            
            return processed_article
            
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None
    
    def _prepare_text_for_processing(self, article: Dict[str, Any]) -> str:
        """
        Combine article fields and preprocess for ML
        """
        text_parts = []
        
        if article.get("title"):
            text_parts.append(article["title"])
        if article.get("description"):
            text_parts.append(article["description"])
        if article.get("content"):
            # News API sometimes truncates content with [+X chars]
            content = article["content"].split('[')[0]
            text_parts.append(content)
        
        full_text = " ".join(text_parts)
        return self.preprocessor.clean_text(full_text)
    
    def save_to_database(self, articles: List[Dict[str, Any]]):
        """
        Save articles to MongoDB
        """
        if not articles:
            return
        
        try:
            db = get_database()
            if db:
                collection = db.news_articles
                result = collection.insert_many(articles)
                logger.info(f"Saved {len(result.inserted_ids)} articles to database")
        except Exception as e:
            logger.error(f"Error saving articles to database: {e}")
    
    def fetch_and_store_news(self, 
                           query: Optional[str] = None,
                           country: str = "us",
                           category: Optional[str] = None):
        """
        Complete pipeline: fetch news and store in database
        """
        if query:
            articles = self.get_everything(query=query, page_size=50)
        else:
            articles = self.get_top_headlines(country=country, category=category, page_size=50)
        
        self.save_to_database(articles)
        return articles

# Singleton instance
news_api_client = NewsAPIClient()