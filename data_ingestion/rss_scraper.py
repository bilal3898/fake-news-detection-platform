# data_ingestion/rss_scraper.py

import feedparser
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from backend.utils.config import get_settings
from backend.database.mongo_connection import get_database
from backend.services.preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)
settings = get_settings()

class RSSScraper:
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # Common RSS feeds for news
        self.default_feeds = [
            "http://rss.cnn.com/rss/edition.rss",
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://feeds.reuters.com/reuters/topNews",
            "https://www.theguardian.com/world/rss",
            "https://www.hindustantimes.com/feeds/rss/news.xml"
        ]
    
    def parse_feed(self, feed_url: str, max_entries: int = 50) -> List[Dict[str, Any]]:
        """
        Parse RSS feed and extract articles
        """
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries[:max_entries]:
                processed_article = self._process_feed_entry(entry, feed_url)
                if processed_article:
                    articles.append(processed_article)
            
            logger.info(f"Parsed {len(articles)} articles from {feed_url}")
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            return []
    
    def _process_feed_entry(self, entry, feed_url: str) -> Optional[Dict[str, Any]]:
        """
        Process individual RSS feed entry
        """
        try:
            if not entry.get("title") or not entry.get("link"):
                return None
            
            # Get full content if available
            content = self._get_full_content(entry.get("link"))
            
            processed_article = {
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "content": content,
                "url": entry.get("link", ""),
                "source": entry.get("source", {}).get("title", "") if hasattr(entry, "source") else "",
                "domain": urlparse(entry.get("link", "")).netloc,
                "published_at": self._parse_date(entry.get("published", "")),
                "author": entry.get("author", ""),
                "feed_url": feed_url,
                "ingestion_time": datetime.utcnow().isoformat(),
                "processed_text": self._prepare_text_for_processing(entry, content)
            }
            
            return processed_article
            
        except Exception as e:
            logger.error(f"Error processing feed entry: {e}")
            return None
    
    def _get_full_content(self, url: str) -> str:
        """
        Fetch full article content from URL
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                element.decompose()
            
            # Try to find main content
            main_content = soup.find('article') or soup.find('main') or soup.body
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
                lines = (line.strip() for line in text.splitlines())
                return '\n'.join(line for line in lines if line)
            
            return soup.get_text(separator='\n', strip=True)
            
        except Exception as e:
            logger.warning(f"Could not fetch full content from {url}: {e}")
            return ""
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse various date formats from RSS feeds
        """
        try:
            if hasattr(date_str, 'parsed'):
                return date_str.parsed.isoformat()
            
            # Try common date formats
            for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            return None
        except:
            return None
    
    def _prepare_text_for_processing(self, entry, content: str) -> str:
        """
        Combine article fields and preprocess for ML
        """
        text_parts = []
        
        if entry.get("title"):
            text_parts.append(entry["title"])
        if entry.get("summary"):
            text_parts.append(entry["summary"])
        if content:
            text_parts.append(content)
        
        full_text = " ".join(text_parts)
        return self.preprocessor.clean_text(full_text)
    
    def scrape_multiple_feeds(self, feed_urls: Optional[List[str]] = None, max_per_feed: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape multiple RSS feeds
        """
        feeds = feed_urls or self.default_feeds
        all_articles = []
        
        for feed_url in feeds:
            try:
                articles = self.parse_feed(feed_url, max_per_feed)
                all_articles.extend(articles)
                time.sleep(1)  # Be polite to servers
            except Exception as e:
                logger.error(f"Error scraping feed {feed_url}: {e}")
                continue
        
        logger.info(f"Total articles scraped: {len(all_articles)}")
        return all_articles
    
    def save_to_database(self, articles: List[Dict[str, Any]]):
        """
        Save articles to MongoDB
        """
        if not articles:
            return
        
        try:
            db = get_database()
            if db:
                collection = db.rss_articles
                # Avoid duplicates based on URL
                for article in articles:
                    collection.update_one(
                        {"url": article["url"]},
                        {"$set": article},
                        upsert=True
                    )
                logger.info(f"Saved/updated {len(articles)} RSS articles to database")
        except Exception as e:
            logger.error(f"Error saving RSS articles to database: {e}")
    
    def scheduled_scraping(self):
        """
        Method to be called by scheduled task
        """
        logger.info("Starting scheduled RSS scraping")
        articles = self.scrape_multiple_feeds()
        self.save_to_database(articles)
        return articles

# Singleton instance
rss_scraper = RSSScraper()