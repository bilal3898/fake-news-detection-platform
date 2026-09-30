# data_ingestion/url_content_extractor.py

import requests
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import time
from datetime import datetime
import re


from newspaper import Article, ArticleException
from bs4 import BeautifulSoup
from readability import Document

from backend.utils.config import get_settings
from backend.services.preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)
settings = get_settings()

class URLContentExtractor:
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.session = requests.Session()
        
        # Rotate between different user agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.session.headers.update({
            'User-Agent': self.user_agents[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1'
        })
        self.timeout = 15
    
    def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extract main content from a URL using multiple methods
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                logger.warning(f"Invalid URL format: {url}")
                return {"error": "Invalid URL", "url": url}
            
            logger.info(f"Attempting to extract content from: {url}")
            
            # Rotate user agent for this request
            import random
            current_ua = random.choice(self.user_agents)
            
            # Enhanced headers for better compatibility
            self.session.headers.update({
                'User-Agent': current_ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8,en-GB;q=0.7,en;q=0.6',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            })
            
            # Try newspaper3k first (best for news articles)
            try:
                logger.debug(f"Trying newspaper3k extraction for {url}")
                result = self._extract_with_newspaper(url)
                if result and result.get("text") and len(result["text"].strip()) > 10:
                    logger.info(f"Successfully extracted {len(result['text'].strip())} chars using newspaper3k")
                    result["extraction_method"] = "newspaper3k"
                    return result
                elif result:
                    logger.debug(f"Newspaper3k returned text but too short: {len(result.get('text', '').strip())} chars")
            except Exception as e:
                logger.warning(f"Newspaper3k extraction failed for {url}: {e}")
            
            # Fallback to readability-lxml (good for general web pages)
            try:
                logger.debug(f"Trying readability extraction for {url}")
                result = self._extract_with_readability(url)
                if result and result.get("text") and len(result["text"].strip()) > 10:
                    logger.info(f"Successfully extracted {len(result['text'].strip())} chars using readability")
                    result["extraction_method"] = "readability"
                    return result
                elif result:
                    logger.debug(f"Readability returned text but too short: {len(result.get('text', '').strip())} chars")
            except Exception as e:
                logger.warning(f"Readability extraction failed for {url}: {e}")
            
            # Fallback to BeautifulSoup (more lenient)
            try:
                logger.debug(f"Trying BeautifulSoup extraction for {url}")
                result = self._extract_with_bs4(url)
                if result and result.get("text") and len(result["text"].strip()) > 10:
                    logger.info(f"Successfully extracted {len(result['text'].strip())} chars using BeautifulSoup")
                    result["extraction_method"] = "beautifulsoup"
                    return result
                elif result:
                    logger.debug(f"BeautifulSoup returned text but too short: {len(result.get('text', '').strip())} chars")
            except Exception as e:
                logger.warning(f"BeautifulSoup extraction failed for {url}: {e}")
            
            # Try a more lenient extraction with lower threshold
            try:
                logger.debug(f"Trying lenient BeautifulSoup extraction for {url}")
                result = self._extract_with_bs4_lenient(url)
                if result and result.get("text") and len(result["text"].strip()) > 10:
                    logger.info(f"Successfully extracted {len(result['text'].strip())} chars using lenient method")
                    result["extraction_method"] = "beautifulsoup_lenient"
                    return result
                elif result:
                    logger.debug(f"Lenient method returned text but too short: {len(result.get('text', '').strip())} chars")
            except Exception as e:
                logger.warning(f"Lenient extraction failed for {url}: {e}")
            
            # Last resort: try to get any text from the page
            try:
                logger.debug(f"Trying fallback text extraction for {url}")
                result = self._extract_any_text(url)
                if result and result.get("text") and len(result["text"].strip()) > 10:
                    logger.info(f"Successfully extracted {len(result['text'].strip())} chars using fallback method")
                    result["extraction_method"] = "fallback_any_text"
                    return result
                elif result:
                    logger.debug(f"Fallback returned text but too short: {len(result.get('text', '').strip())} chars")
            except Exception as e:
                logger.warning(f"Fallback text extraction failed for {url}: {e}")
            
            # Try structured data extraction for JavaScript-heavy sites
            try:
                logger.debug(f"Trying structured data extraction for {url}")
                result = self._extract_with_structured_data(url)
                logger.debug(f"Structured data result: {result}")
                if result and result.get("text") and len(result["text"].strip()) > 10:
                    logger.info(f"Successfully extracted {len(result['text'].strip())} chars using structured data")
                    result["extraction_method"] = "structured_data"
                    return result
                elif result:
                    logger.debug(f"Structured data returned text but too short: {len(result.get('text', '').strip())} chars")
            except Exception as e:
                logger.warning(f"Structured data extraction failed for {url}: {e}")
            
            # Final attempt with different user agent and cookies
            try:
                logger.debug(f"Trying extraction with different user agent for {url}")
                result = self._extract_with_different_ua(url)
                if result and result.get("text") and len(result["text"].strip()) > 10:
                    logger.info(f"Successfully extracted {len(result['text'].strip())} chars using different UA")
                    result["extraction_method"] = "different_ua"
                    return result
            except Exception as e:
                logger.warning(f"Different UA extraction failed for {url}: {e}")
            
            # Last resort: aggressive text extraction
            try:
                logger.debug(f"Trying aggressive text extraction for {url}")
                result = self._extract_aggressive(url)
                if result and result.get("text") and len(result["text"].strip()) > 10:
                    logger.info(f"Successfully extracted {len(result['text'].strip())} chars using aggressive method")
                    result["extraction_method"] = "aggressive"
                    return result
            except Exception as e:
                logger.warning(f"Aggressive extraction failed for {url}: {e}")
            
            logger.error(f"All extraction methods failed for {url}")
            logger.error(f"Final error state - checking each method:")
            
            # Debug each method one more time
            try:
                logger.debug(f"Final check - structured data method:")
                final_result = self._extract_with_structured_data(url)
                logger.debug(f"Final structured data result: {final_result}")
                if final_result and final_result.get('text') and len(final_result['text'].strip()) > 10:
                    logger.info(f"Final structured data SUCCESS: {len(final_result['text'].strip())} chars")
                    final_result["extraction_method"] = "structured_data_final"
                    return final_result
            except Exception as e:
                logger.error(f"Final structured data check failed: {e}")
            
            return {"error": "Unable to extract readable content from this URL. The page may require JavaScript, be behind a paywall, or have restricted access. Please try copying the text directly or use a different URL.", "url": url}
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {"error": str(e), "url": url}
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _extract_with_newspaper(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content using newspaper3k with enhanced configuration
        """
        try:
            # Configure newspaper with better settings for problematic sites
            article = Article(
                url, 
                fetch_images=False, 
                request_timeout=self.timeout,
                language='en'
            )
            
            # Set custom user agent for newspaper
            article.config.browser_user_agent = self.session.headers.get('User-Agent')
            article.config.request_timeout = self.timeout
            article.config.number_threads = 1
            
            # Download with retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    article.download()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)
            
            article.parse()
            
            if not article.text or len(article.text.strip()) < 10:
                logger.debug(f"Newspaper3k: Text too short ({len(article.text.strip()) if article.text else 0} chars)")
                return None
            
            # Apply additional text cleaning
            cleaned_text = self._clean_extracted_text(article.text)
            
            return {
                "title": self._clean_extracted_text(article.title) if article.title else "",
                "text": cleaned_text,
                "authors": article.authors,
                "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                "top_image": article.top_image,
                "images": list(article.images),
                "movies": list(article.movies),
                "keywords": article.keywords,
                "summary": article.summary,
                "source": urlparse(url).netloc,
                "url": url,
                "extraction_time": time.time()
            }
        except ArticleException as e:
            logger.debug(f"Newspaper3k failed for {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error with newspaper3k for {url}: {e}")
            return None
    
    def _extract_with_readability(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content using readability-lxml with enhanced error handling
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Check if content is HTML
            content_type = response.headers.get('Content-Type', '').lower()
            if 'html' not in content_type:
                logger.debug(f"Content type is not HTML: {content_type}")
                return None
            
            # Try readability extraction
            doc = Document(response.content)
            title = doc.title()
            content = doc.summary()
            
            # Clean HTML tags from content
            soup = BeautifulSoup(content, 'html.parser')
            clean_text = soup.get_text(separator='\n', strip=True)
            
            # Remove extra whitespace and clean
            clean_text = self._clean_extracted_text(clean_text)
            
            if not clean_text or len(clean_text.strip()) < 10:
                logger.debug(f"Readability: Text too short ({len(clean_text.strip()) if clean_text else 0} chars)")
                return None
            
            return {
                "title": self._clean_extracted_text(title) if title else "",
                "text": clean_text,
                "source": urlparse(url).netloc,
                "url": url,
                "extraction_time": time.time()
            }
        except Exception as e:
            logger.debug(f"Readability failed for {url}: {e}")
            return None
    
    def _extract_with_bs4(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content using BeautifulSoup with enhanced selectors
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Check if content is HTML
            content_type = response.headers.get('Content-Type', '').lower()
            if 'html' not in content_type:
                logger.debug(f"Content type is not HTML: {content_type}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'iframe', 'noscript']):
                element.decompose()
            
            # Enhanced selectors for main content areas including MSN-specific ones
            selectors = [
                # MSN specific selectors
                '.article-body',
                '.article-content',
                '.story-body',
                '.story-content',
                '[data-module="articleBody"]',
                '[data-testid="article-body"]',
                '[data-testid="article-content"]',
                '.contentarea',
                '.articlepage',
                '.newsarticle',
                
                # General content selectors
                'article',
                'main',
                '[role="main"]',
                '.content',
                '.main-content',
                '#content',
                '#main',
                '.post-content',
                '.entry-content',
                '.article-content',
                '.story-body',
                '.article-body',
                '.post-body',
                '.news-content',
                '.article-main',
                '[class*="content"]',
                '[id*="content"]',
                '.story-content',
                '.post-story',
                
                # Additional fallback selectors
                '.article-text',
                '.story-text',
                '.news-text',
                '.post-text',
                '[data-testid*="content"]',
                '[data-module*="article"]',
                '.section-content',
                '.page-content'
            ]
            
            main_content = None
            for selector in selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    # Check if this content has substantial text
                    text = main_content.get_text(separator='\n', strip=True)
                    if len(text.strip()) > 100:  # Only use if substantial content
                        break
                    else:
                        main_content = None
            
            if not main_content:
                main_content = soup.body
            
            text = main_content.get_text(separator='\n', strip=True)
            lines = (line.strip() for line in text.splitlines())
            clean_text = '\n'.join(line for line in lines if line and len(line) > 3)
            clean_text = self._clean_extracted_text(clean_text)
            
            title = soup.find('title')
            title_text = self._clean_extracted_text(title.get_text()) if title else ""
            
            if not clean_text or len(clean_text.strip()) < 10:
                logger.debug(f"BeautifulSoup: Text too short ({len(clean_text.strip()) if clean_text else 0} chars)")
                return None
            
            return {
                "title": title_text,
                "text": clean_text,
                "source": urlparse(url).netloc,
                "url": url,
                "extraction_time": time.time()
            }
        except Exception as e:
            logger.debug(f"BeautifulSoup failed for {url}: {e}")
            return None
    
    def _extract_with_bs4_lenient(self, url: str) -> Optional[Dict[str, Any]]:
        """
        More lenient BeautifulSoup extraction with lower threshold
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Try to parse even if content type is not explicitly HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'iframe']):
                element.decompose()
            
            # Get all text from body
            if soup.body:
                text = soup.body.get_text(separator='\n', strip=True)
                lines = (line.strip() for line in text.splitlines())
                clean_text = '\n'.join(line for line in lines if line and len(line) > 3)
                
                title = soup.find('title')
                title_text = title.get_text() if title else ""
                
                if clean_text and len(clean_text.strip()) > 10:
                    return {
                        "title": title_text,
                        "text": clean_text,
                        "source": urlparse(url).netloc,
                        "url": url,
                        "extraction_time": time.time()
                    }
            
            return None
        except Exception as e:
            logger.debug(f"BeautifulSoup lenient failed for {url}: {e}")
            return None
    
    def _extract_any_text(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Last resort: extract any readable text from the page
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove all script and style elements
            for script in soup(["script", "style", "noscript", "iframe", "object", "embed"]):
                script.decompose()
            
            # Get all text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            if text and len(text.strip()) > 10:
                return {
                    "title": title_text,
                    "text": text,
                    "source": urlparse(url).netloc,
                    "url": url,
                    "extraction_time": time.time()
                }
            
            return None
        except Exception as e:
            logger.debug(f"Fallback text extraction failed for {url}: {e}")
            return None
    
    def _extract_with_structured_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content from structured data and meta tags for JavaScript-heavy sites
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to extract from JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    
                    # Handle different structured data formats
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') in ['NewsArticle', 'Article', 'BlogPosting']:
                                title = item.get('headline', '')
                                content = item.get('articleBody', '') or item.get('text', '')
                                if content and len(content.strip()) > 50:
                                    return {
                                        "title": self._clean_extracted_text(title),
                                        "text": self._clean_extracted_text(content),
                                        "source": urlparse(url).netloc,
                                        "url": url,
                                        "extraction_time": time.time()
                                    }
                    elif isinstance(data, dict) and data.get('@type') in ['NewsArticle', 'Article', 'BlogPosting']:
                        title = data.get('headline', '')
                        content = data.get('articleBody', '') or data.get('text', '')
                        if content and len(content.strip()) > 50:
                            return {
                                "title": self._clean_extracted_text(title),
                                "text": self._clean_extracted_text(content),
                                "source": urlparse(url).netloc,
                                "url": url,
                                "extraction_time": time.time()
                            }
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # Try meta tags as fallback
            title = soup.find('title')
            title_text = self._clean_extracted_text(title.get_text()) if title else ""
            
            # Try multiple meta tag sources
            meta_sources = [
                ('og:description', 'property'),
                ('description', 'name'),
                ('twitter:description', 'name'),
                ('og:title', 'property'),
                ('twitter:title', 'name')
            ]
            
            content = ""
            for attr_value, attr_name in meta_sources:
                if 'description' in attr_value:
                    meta_tag = soup.find('meta', attrs={attr_name: attr_value})
                    if meta_tag and meta_tag.get('content'):
                        desc = self._clean_extracted_text(meta_tag['content'])
                        if len(desc.strip()) > 20:  # Meaningful description
                            content = desc
                            break
                elif 'title' in attr_value and not title_text:
                    meta_tag = soup.find('meta', attrs={attr_name: attr_value})
                    if meta_tag and meta_tag.get('content'):
                        title_text = self._clean_extracted_text(meta_tag['content'])
            
            # If we have some content, return it
            if content and len(content.strip()) > 20:
                return {
                    "title": title_text,
                    "text": content,
                    "source": urlparse(url).netloc,
                    "url": url,
                    "extraction_time": time.time()
                }
            
            # If no meta description, try to extract from URL path
            try:
                from urllib.parse import unquote
                parsed_url = urlparse(url)
                path_parts = unquote(parsed_url.path).split('/')
                
                # Look for news article in path
                if 'news' in path_parts:
                    news_index = path_parts.index('news')
                    if news_index + 1 < len(path_parts):
                        # Get the article slug
                        article_slug = path_parts[news_index + 1]
                        # Remove article ID if present
                        if '/ar-' in article_slug:
                            article_slug = article_slug.split('/ar-')[0]
                        # Convert to readable title
                        potential_title = article_slug.replace('-', ' ').replace('_', ' ').title()
                        if len(potential_title) > 10:
                            return {
                                "title": potential_title,
                                "text": f"Content from {parsed_url.netloc}. This page appears to require JavaScript to load properly. Please visit the URL directly or copy and paste the article text for analysis.",
                                "source": parsed_url.netloc,
                                "url": url,
                                "extraction_time": time.time()
                            }
                elif len(path_parts) > 1:
                    # Try to construct a title from the URL
                    potential_title = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                    if len(potential_title) > 10:
                        return {
                            "title": potential_title,
                            "text": f"Content from {parsed_url.netloc}. This page appears to require JavaScript to load properly. Please visit the URL directly or copy and paste the article text for analysis.",
                            "source": parsed_url.netloc,
                            "url": url,
                            "extraction_time": time.time()
                        }
            except:
                pass
            
            # Final fallback - provide helpful message
            # Try to extract title from URL path for news sites
            title_text = ""
            try:
                from urllib.parse import unquote
                parsed_url = urlparse(url)
                path_parts = unquote(parsed_url.path).split('/')
                
                # Look for news article in path
                if 'news' in path_parts:
                    news_index = path_parts.index('news')
                    if news_index + 1 < len(path_parts):
                        # Get the article slug
                        article_slug = path_parts[news_index + 1]
                        # Remove article ID if present
                        if '/ar-' in article_slug:
                            article_slug = article_slug.split('/ar-')[0]
                        # Convert to readable title
                        title_text = article_slug.replace('-', ' ').replace('_', ' ').title()
                elif len(path_parts) > 1:
                    # Try to construct a title from the URL
                    potential_title = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                    if len(potential_title) > 10:
                        title_text = potential_title
            except Exception as e:
                logger.debug(f"URL title extraction failed: {e}")
            
            return {
                "title": title_text or f"Content from {urlparse(url).netloc}",
                "text": f"This page from {urlparse(url).netloc} requires JavaScript to display properly. The content could not be extracted automatically. Please copy and paste the article text directly for analysis.",
                "source": urlparse(url).netloc,
                "url": url,
                "extraction_time": time.time()
            }
        except Exception as e:
            logger.debug(f"Structured data extraction failed for {url}: {e}")
            return None
    
    def _extract_aggressive(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Aggressive extraction method that tries multiple approaches to get any meaningful content
        """
        try:
            # Try with different user agents and headers
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]
            
            for ua in user_agents:
                try:
                    headers = {
                        'User-Agent': ua,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove all script and style elements
                    for script in soup(["script", "style", "meta", "link", "noscript"]):
                        script.decompose()
                    
                    # Try to find any paragraph tags with substantial content
                    paragraphs = soup.find_all('p')
                    if paragraphs:
                        texts = []
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if len(text) > 20:  # Only keep meaningful paragraphs
                                texts.append(text)
                        
                        if texts and len(' '.join(texts)) > 50:
                            content = ' '.join(texts)
                            title = soup.find('title')
                            title_text = title.get_text(strip=True) if title else ""
                            
                            return {
                                "title": self._clean_extracted_text(title_text),
                                "text": self._clean_extracted_text(content),
                                "source": urlparse(url).netloc,
                                "url": url,
                                "extraction_time": time.time()
                            }
                    
                    # If no paragraphs, try div elements with text content
                    divs = soup.find_all('div')
                    for div in divs:
                        text = div.get_text(strip=True)
                        if len(text) > 100:  # Look for substantial content
                            # Check if it looks like article content (has sentences)
                            sentences = text.split('. ')
                            if len(sentences) > 3:  # At least 3 sentences
                                title = soup.find('title')
                                title_text = title.get_text(strip=True) if title else ""
                                
                                return {
                                    "title": self._clean_extracted_text(title_text),
                                    "text": self._clean_extracted_text(text),
                                    "source": urlparse(url).netloc,
                                    "url": url,
                                    "extraction_time": time.time()
                                }
                    
                except Exception as e:
                    logger.debug(f"Aggressive extraction with UA {ua} failed: {e}")
                    continue
            
            return None
        except Exception as e:
            logger.debug(f"Aggressive extraction failed for {url}: {e}")
            return None
    
    def extract_and_preprocess(self, url: str) -> Dict[str, Any]:
        """
        Extract content and preprocess for ML
        """
        result = self.extract_content(url)
        
        if "error" in result:
            return result
        
        # Preprocess text for ML
        if result.get("text"):
            result["processed_text"] = self.preprocessor.clean_text(result["text"])
        
        # Add metadata
        result["processing_time"] = datetime.utcnow().isoformat()
        result["text_length"] = len(result.get("text", ""))
        result["processed_text_length"] = len(result.get("processed_text", ""))
        
        return result
    
    def batch_extract(self, urls: list, max_workers: int = 5) -> list:
        """
        Extract content from multiple URLs in parallel
        """
        from concurrent.futures import ThreadPoolExecutor
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.extract_content, url): url for url in urls}
            
            for future in future_to_url:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "url": future_to_url[future]})
        
        return results

    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        """
        if not text:
            return ""
        
        # Remove common unwanted patterns
        text = re.sub(r'\s+', ' ', text)  # Multiple whitespace to single space
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r'^\s+|\s+$', '', text)  # Trim leading/trailing whitespace
        
        # Remove common boilerplate text
        boilerplate_patterns = [
            r'click here to.*?\.',
            r'share this.*?\.',
            r'follow us on.*?\.',
            r'subscribe to.*?\.',
            r'read more.*?\.',
            r'\[.*?\]',  # Remove bracketed content
            r'\(.*?\)',  # Remove parenthetical content if short
        ]
        
        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text)  # Clean up again
        text = text.strip()
        
        return text
    
    def _extract_with_different_ua(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Final attempt with different user agent and cookies
        """
        try:
            # Create a new session with different configuration
            new_session = requests.Session()
            
            # Use a mobile user agent for better compatibility
            mobile_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            
            new_session.headers.update({
                'User-Agent': mobile_ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            response = new_session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove all unwanted elements
            for element in soup(["script", "style", "noscript", "iframe", "object", "embed", "nav", "footer", "aside", "header"]):
                element.decompose()
            
            # Get all text from body
            if soup.body:
                text = soup.body.get_text(separator=' ', strip=True)
                text = self._clean_extracted_text(text)
                
                title = soup.find('title')
                title_text = self._clean_extracted_text(title.get_text()) if title else ""
                
                if text and len(text.strip()) > 10:
                    return {
                        "title": title_text,
                        "text": text,
                        "source": urlparse(url).netloc,
                        "url": url,
                        "extraction_time": time.time()
                    }
            
            return None
        except Exception as e:
            logger.debug(f"Different UA extraction failed for {url}: {e}")
            return None

# Singleton instance
url_extractor = URLContentExtractor()