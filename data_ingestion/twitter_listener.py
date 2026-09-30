# data_ingestion/twitter_listener.py

import tweepy
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import json

from backend.utils.config import get_settings
from backend.database.mongo_connection import get_database
from backend.services.preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)
settings = get_settings()

class TwitterListener:
    def __init__(self):
        self.auth = None
        self.api = None
        self.preprocessor = TextPreprocessor()
        self.initialize_api()
    
    def initialize_api(self):
        """
        Initialize Twitter API client
        """
        try:
            # Twitter API v2 requires Bearer Token for academic research access
            auth = tweepy.OAuth2BearerHandler(settings.TWITTER_BEARER_TOKEN)
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            logger.info("Twitter API initialized successfully")
        except Exception as e:
            logger.warning(f"Twitter API not configured: {e}")
    
    def search_tweets(self, 
                     query: str,
                     max_results: int = 100,
                     since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for tweets containing specific keywords
        """
        if not self.api:
            logger.warning("Twitter API not initialized")
            return []
        
        try:
            tweets = []
            
            for tweet in tweepy.Cursor(
                self.api.search_tweets,
                q=query,
                tweet_mode="extended",
                since_id=since_id,
                result_type="recent",
                lang="en"
            ).items(max_results):
                
                processed_tweet = self._process_tweet(tweet)
                if processed_tweet:
                    tweets.append(processed_tweet)
            
            logger.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
            
        except tweepy.TweepError as e:
            logger.error(f"Twitter API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return []
    
    def get_trending_news(self, 
                         woied: int = 23424977,  # USA WOEID
                         max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get trending topics and search for related news
        """
        if not self.api:
            return []
        
        try:
            trends = self.api.get_place_trends(woied)
            trending_topics = [trend['name'] for trend in trends[0]['trends'][:10]]
            
            news_tweets = []
            for topic in trending_topics:
                # Filter out hashtags and non-news topics
                if not topic.startswith('#') and len(topic.split()) > 1:
                    tweets = self.search_tweets(topic, max_results=10)
                    news_tweets.extend(tweets)
            
            return news_tweets[:max_results]
            
        except Exception as e:
            logger.error(f"Error getting trending news: {e}")
            return []
    
    def _process_tweet(self, tweet) -> Optional[Dict[str, Any]]:
        """
        Process and clean tweet data
        """
        try:
            # Get full text (handles both extended and regular tweets)
            if hasattr(tweet, 'full_text'):
                text = tweet.full_text
            else:
                text = tweet.text
            
            # Remove URLs and mentions
            clean_text = re.sub(r'http\S+|@\S+', '', text).strip()
            
            if len(clean_text) < 20:  # Minimum length for meaningful content
                return None
            
            processed_tweet = {
                "id": tweet.id_str,
                "text": clean_text,
                "full_text": text,
                "user": tweet.user.screen_name,
                "user_followers": tweet.user.followers_count,
                "retweet_count": tweet.retweet_count,
                "favorite_count": tweet.favorite_count,
                "created_at": tweet.created_at.isoformat(),
                "language": tweet.lang,
                "is_retweet": hasattr(tweet, 'retweeted_status'),
                "processed_text": self.preprocessor.clean_text(clean_text),
                "source": "twitter",
                "url": f"https://twitter.com/user/status/{tweet.id}"
            }
            
            return processed_tweet
            
        except Exception as e:
            logger.error(f"Error processing tweet: {e}")
            return None
    
    def save_to_database(self, tweets: List[Dict[str, Any]]):
        """
        Save tweets to MongoDB
        """
        if not tweets:
            return
        
        try:
            db = get_database()
            if db:
                collection = db.tweets
                # Avoid duplicates
                for tweet in tweets:
                    collection.update_one(
                        {"id": tweet["id"]},
                        {"$set": tweet},
                        upsert=True
                    )
                logger.info(f"Saved/updated {len(tweets)} tweets to database")
        except Exception as e:
            logger.error(f"Error saving tweets to database: {e}")
    
    def stream_news_keywords(self, keywords: List[str]):
        """
        Stream tweets containing news keywords (requires elevated access)
        """
        if not self.api:
            return
        
        class NewsStreamListener(tweepy.Stream):
            def __init__(self, listener):
                super().__init__()
                self.listener = listener
            
            def on_data(self, data):
                try:
                    tweet = json.loads(data)
                    processed_tweet = self.listener._process_tweet(tweet)
                    if processed_tweet:
                        self.listener.save_to_database([processed_tweet])
                except Exception as e:
                    logger.error(f"Error processing stream data: {e}")
                return True
            
            def on_error(self, status):
                logger.error(f"Twitter stream error: {status}")
                return True
        
        stream_listener = NewsStreamListener(self)
        stream_listener.filter(track=keywords, threaded=True)

# Singleton instance
twitter_listener = TwitterListener()