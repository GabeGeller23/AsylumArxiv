import arxiv
import json
import sys
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
from pathlib import Path
import concurrent.futures
from functools import partial
import time
import re
import requests
import logging
import threading
from functools import lru_cache
from memory_profiler import profile as memory_profile
import asyncio
import traceback
from collections import defaultdict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import gc  # Add garbage collector
from urllib.parse import quote_plus
import aiohttp
import random
import urllib.parse
import hashlib
import csv
import unicodedata
from tqdm import tqdm
from collections import Counter

# Set up paths
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
KEYWORDS_FILE = SCRIPT_DIR / "keywords.json"
COMMERCIAL_FILE = SCRIPT_DIR / "commercial_metrics.json"
HINDEX_CACHE_FILE = SCRIPT_DIR / "hindex_cache.json"

# Thread-local storage for API session reuse
thread_local = threading.local()

# Increase timeout for API requests
API_TIMEOUT = 10  # Increase from default 5 seconds to 10 seconds
API_SEMAPHORE = threading.Semaphore(10)  # Increase from 5 to 10 concurrent requests

# Global cache for papers to avoid redundant API calls
PAPER_CACHE = {}
PAPER_CACHE_LOCK = threading.Lock()

# Global cache for keywords and commercial metrics
KEYWORDS_CACHE = None
KEYWORDS_CACHE_LOCK = threading.Lock()
COMMERCIAL_METRICS_CACHE = None
COMMERCIAL_METRICS_CACHE_LOCK = threading.Lock()

# Global constants
CACHE_DIR = os.path.expanduser("~/.cache/arxiv-papers")
KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")
COMMERCIAL_METRICS_PATH = os.path.join(os.path.dirname(__file__), "commercial_metrics.json")
HINDEX_CACHE_PATH = os.path.join(CACHE_DIR, "hindex_cache.json")
SESSION = None

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger()

# Set up cache directory
os.makedirs(CACHE_DIR, exist_ok=True)

# Simple debug function
def debug_print(msg):
    print(msg, file=sys.stderr)

# Print progress updates
def progress_update(msg):
    print(f"PROGRESS: {msg}", file=sys.stderr)
    sys.stderr.flush()

# Use a more robust session creation with retries
def get_session():
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        thread_local.session = session
    return thread_local.session

# Load commercial metrics data
def load_commercial_metrics():
    global COMMERCIAL_METRICS_CACHE
    try:
        with COMMERCIAL_METRICS_CACHE_LOCK:
            if COMMERCIAL_METRICS_CACHE is not None:
                return COMMERCIAL_METRICS_CACHE
        
        if COMMERCIAL_FILE.exists():
            with open(COMMERCIAL_FILE, 'r') as f:
                metrics = json.load(f)
                with COMMERCIAL_METRICS_CACHE_LOCK:
                    COMMERCIAL_METRICS_CACHE = metrics
                return metrics
        else:
            # Default commercial metrics if file doesn't exist
            commercial_metrics = {
                "patent_keywords": {
                    "novel": 3,
                    "method": 2, 
                    "system": 2,
                    "apparatus": 3,
                    "device": 2,
                    "improving": 2,
                    "improved": 2,
                    "enhancement": 2,
                    "innovative": 3,
                    "invention": 4,
                    "approach": 1,
                    "solution": 2,
                    "technical": 1,
                    "prototype": 3,
                    "implementation": 2
                },
                "industry_keywords": {
                    "industry": 2,
                    "commercial": 3,
                    "enterprise": 2,
                    "business": 2,
                    "market": 2,
                    "product": 3,
                    "production": 2,
                    "manufacturing": 3,
                    "deployment": 2,
                    "real-world": 2,
                    "cost-effective": 3,
                    "application": 1,
                    "scalable": 2,
                    "practical": 2,
                    "startup": 3
                },
                "market_sectors": {
                    "healthcare": 3,
                    "finance": 3,
                    "fintech": 4,
                    "energy": 3,
                    "transportation": 3,
                    "robotics": 4,
                    "security": 3,
                    "cybersecurity": 4,
                    "agriculture": 3,
                    "retail": 2,
                    "manufacturing": 3,
                    "education": 2,
                    "autonomous": 4,
                    "sustainable": 3,
                    "renewable": 3
                },
                "prominent_authors": {
                    "Yoshua Bengio": 115, 
                    "Geoffrey Hinton": 130,
                    "Yann LeCun": 125,
                    "Andrew Ng": 100,
                    "Fei-Fei Li": 95,
                    "Ian Goodfellow": 85,
                    "Andrej Karpathy": 70,
                    "Jeff Dean": 90,
                    "Demis Hassabis": 65,
                    "Kaiming He": 80
                }
            }
            # Save default metrics
            with open(COMMERCIAL_FILE, 'w') as f:
                json.dump(commercial_metrics, f, indent=2)
            with COMMERCIAL_METRICS_CACHE_LOCK:
                COMMERCIAL_METRICS_CACHE = commercial_metrics
            return commercial_metrics
    except Exception as e:
        debug_print(f"Error loading commercial metrics: {str(e)}")
        return {
            "patent_keywords": {},
            "industry_keywords": {},
            "market_sectors": {},
            "prominent_authors": {}
        }

# Load H-index cache to avoid recalculating
def load_hindex_cache():
    try:
        if HINDEX_CACHE_FILE.exists():
            with open(HINDEX_CACHE_FILE, 'r') as f:
                return json.load(f)
        else:
            # Initialize empty cache
            with open(HINDEX_CACHE_FILE, 'w') as f:
                json.dump({}, f)
            return {}
    except Exception as e:
        debug_print(f"Error loading H-index cache: {str(e)}")
        return {}

# Save H-index cache
def save_hindex_cache(cache):
    try:
        with open(HINDEX_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        debug_print(f"Error saving H-index cache: {str(e)}")

# Load keywords from JSON file
@lru_cache(maxsize=100)
def load_keywords():
    global KEYWORDS_CACHE
    try:
        with KEYWORDS_CACHE_LOCK:
            if KEYWORDS_CACHE is not None:
                return KEYWORDS_CACHE
        
        if KEYWORDS_FILE.exists():
            with open(KEYWORDS_FILE, 'r') as f:
                keywords = json.load(f)
                with KEYWORDS_CACHE_LOCK:
                    KEYWORDS_CACHE = keywords
                return keywords
        else:
            # Default keywords if file doesn't exist
            default_keywords = {
                "machine learning": 5,
                "deep learning": 5,
                "neural network": 4,
                "artificial intelligence": 4,
                "ai": 4, 
                "computer vision": 3,
                "natural language processing": 3,
                "nlp": 3,
                "healthcare": 3,
                "finance": 3,
                "autonomous": 3,
                "robotics": 3
            }
            # Save default keywords
            with open(KEYWORDS_FILE, 'w') as f:
                json.dump(default_keywords, f, indent=2)
            with KEYWORDS_CACHE_LOCK:
                KEYWORDS_CACHE = default_keywords
            return default_keywords
    except Exception as e:
        debug_print(f"Error loading keywords: {str(e)}")
        return {
            "machine learning": 5, 
            "deep learning": 5,
            "neural network": 4
        }

# Load keywords and commercial metrics when module is imported
KEYWORDS = load_keywords()
COMMERCIAL_METRICS = load_commercial_metrics()
HINDEX_CACHE = load_hindex_cache()

# Use LRU cache for calculate_score to avoid repetitive calculations
def calculate_score(text, keywords=None):
    """
    Calculate a relevance score based on keywords found in the text.
    Returns a dictionary with the score and matched tags.
    """
    # If keywords not provided, load from file
    if keywords is None:
        try:
            with open(KEYWORDS_PATH, 'r') as f:
                keywords = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load keywords: {str(e)}")
            return {"score": 0, "tags": []}
    
    matched_tags = []
    total_score = 0
    
    for keyword, weight in keywords.items():
        # Use word boundary regex to match whole words only
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        matches = re.findall(pattern, text.lower())
        
        if matches:
            # Count the number of matches for this keyword
            count = len(matches)
            # Add the keyword to matched tags
            matched_tags.append(keyword)
            # Add weighted score based on count and importance
            total_score += count * weight
    
    # Normalize score to 0-5 scale
    max_possible_score = 10  # Calibrate this based on your keyword weights
    normalized_score = min(5, (total_score / max_possible_score) * 5)
    
    return {
        "score": normalized_score,
        "tags": matched_tags
    }

# Optimize calculations with caching
@lru_cache(maxsize=1024)
def calculate_patent_potential(text):
    """Calculate patent potential score based on patent-related keywords"""
    if not text:
        return {"score": 0, "tags": []}
    
    text = text.lower()
    score = 0
    matched_tags = []
    
    for keyword, value in COMMERCIAL_METRICS["patent_keywords"].items():
        # Use word boundary to match whole words
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text):
            score += value
            matched_tags.append(keyword)
    
    return {"score": score, "tags": matched_tags}

@lru_cache(maxsize=1024)
def calculate_industry_potential(text):
    """Calculate industry application potential based on industry-related keywords"""
    if not text:
        return {"score": 0, "tags": []}
    
    text = text.lower()
    score = 0
    matched_tags = []
    
    # Check industry keywords
    for keyword, value in COMMERCIAL_METRICS["industry_keywords"].items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text):
            score += value
            matched_tags.append(keyword)
    
    # Check market sector keywords
    for keyword, value in COMMERCIAL_METRICS["market_sectors"].items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text):
            score += value
            matched_tags.append(keyword)
    
    return {"score": score, "tags": matched_tags}

def estimate_author_impact(authors):
    """Estimate author impact based on known prominent authors"""
    if not authors:
        return {"score": 0, "prominent_authors": []}
    
    score = 0
    prominent_authors = []
    
    for author in authors:
        # Check if author is in our prominent authors list
        for known_author, h_index in COMMERCIAL_METRICS["prominent_authors"].items():
            if known_author.lower() in author.lower():
                score += min(h_index / 10, 10)  # Scale down h-index, cap at 10
                prominent_authors.append(known_author)
                break
    
    return {"score": score, "prominent_authors": prominent_authors}

# Optimized function to fetch author information with better error handling
def get_author_info(authors, prominent_authors=None):
    """
    Look up author information and calculate author scores.
    
    Args:
        authors: List of author names or Author objects
        prominent_authors: Dictionary of known prominent authors with h-indices
        
    Returns:
        Dictionary with author information and scores
    """
    # Handle case with no authors
    if not authors:
        return {"author_score": 0, "authors": []}
        
    # Convert authors to strings if needed
    author_names = []
    for author in authors:
        if hasattr(author, 'name'):
            author_names.append(author.name)
        else:
            author_names.append(str(author))
    
    if not author_names:
        return {"author_score": 0, "authors": []}
    
    # Get the first author for score calculation
    first_author = author_names[0] if author_names else ""
    
    # Use the cache for h-index lookups
    author_score = 0
    max_h_index = 0
    authors_info = []
    
    # First check if first author is prominent
    if prominent_authors and first_author in prominent_authors:
        h_index = prominent_authors[first_author]
        max_h_index = h_index
        author_score = min(5, (h_index / 100) * 5)  # Normalize to 0-5 scale
    else:
        # Try to look up the first author online
        try:
            with API_SEMAPHORE:
                if first_author in HINDEX_CACHE:
                    author_data = HINDEX_CACHE[first_author]
                    if author_data:
                        max_h_index = author_data.get("h_index", 0)
                        author_score = min(5, (max_h_index / 100) * 5)
                else:
                    # Only look up if not in cache
                    author_data = lookup_author(first_author)
                    if author_data:
                        max_h_index = author_data.get("h_index", 0)
                        author_score = min(5, (max_h_index / 100) * 5)
                        HINDEX_CACHE[first_author] = author_data
        except Exception as e:
            logging.error(f"Error fetching author info for {first_author}: {str(e)}")
            # If lookup fails, use a reasonable default based on co-authors
            if len(author_names) > 3:
                author_score = 2.5  # Middle score for papers with many authors
            else:
                author_score = 1.5  # Lower default for papers with few authors
    
    return {
        "author_score": author_score,
        "authors": author_names,
        "h_index": max_h_index
    }

# Optimized lookup author function with timeout
def lookup_author(author_name):
    """Look up author information from Semantic Scholar API"""
    if not author_name:
        return None
        
    # Check cache first
    if author_name in HINDEX_CACHE:
        return HINDEX_CACHE[author_name]
    
    try:
        # Use a session with retries
        session = get_session()
        # Properly encode the author name using urllib.parse.quote
        encoded_name = urllib.parse.quote(author_name)
        url = f"https://api.semanticscholar.org/graph/v1/author/search?query={encoded_name}&limit=1"
        
        response = session.get(url, timeout=API_TIMEOUT)
        if response.status_code != 200:
            return None
            
        data = response.json()
        if not data or "data" not in data or not data["data"]:
            return None
            
        author = data["data"][0]
        author_id = author.get("authorId")
        
        if not author_id:
            return None
            
        # Get detailed author information
        detail_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}?fields=hIndex,paperCount,citationCount"
        detail_response = session.get(detail_url, timeout=API_TIMEOUT)
        
        if detail_response.status_code != 200:
            return None
            
        author_data = detail_response.json()
        h_index = author_data.get("hIndex", 0)
        
        result = {
            "name": author_data.get("name", author_name),
            "h_index": h_index,
            "paper_count": author_data.get("paperCount", 0),
            "citations": author_data.get("citationCount", 0),
            "profile_url": f"https://www.semanticscholar.org/author/{author_id}",
            "linkedin_url": f"https://www.google.com/search?q=linkedin+{urllib.parse.quote(author_name)}"
        }
        
        # Update cache
        HINDEX_CACHE[author_name] = result
        
        return result
    except Exception as e:
        logging.error(f"Error looking up author {author_name}: {str(e)}")
        return None

# Cache for author h-index values to reduce API calls
HINDEX_CACHE = {}
CACHE_FILE = "author_cache.json"

# Load existing h-index cache if available
try:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            HINDEX_CACHE = json.load(f)
except Exception as e:
    logging.warning(f"Could not load h-index cache: {str(e)}")
    HINDEX_CACHE = {}

def save_hindex_cache(cache):
    """Save the h-index cache to a file"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        logging.warning(f"Could not save h-index cache: {str(e)}")

def get_author_info_single(author, prominent_authors=None):
    """
    Get information about a single author, checking prominent authors list first,
    then cache, then querying the API as needed.
    
    Args:
        author: Author name or object with a name attribute
        prominent_authors (dict, optional): Dictionary of prominent authors with h-index values
        
    Returns:
        dict: Author information including name and h-index
    """
    # Extract author name from different possible formats
    if hasattr(author, 'name'):
        author_name = author.name
    elif isinstance(author, dict) and "name" in author:
        author_name = author["name"]
    else:
        author_name = str(author)
    
    # Check if author is in the prominent authors list
    if prominent_authors and author_name in prominent_authors:
        h_index = prominent_authors[author_name]
        return {
            "name": author_name,
            "h_index": h_index,
            "paper_count": 100,  # Reasonable default for prominent authors
            "prominent": True
        }
    
    # Check if author is in our cache
    if author_name in HINDEX_CACHE:
        return HINDEX_CACHE[author_name]
    
    # If not found, query the Semantic Scholar API
    try:
        url = f"https://api.semanticscholar.org/graph/v1/author/search?query={author_name}&fields=name,hIndex,paperCount"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if "data" in data and len(data["data"]) > 0:
            # Get the first (most relevant) result
            result = data["data"][0]
            author_data = {
                "name": result.get("name", author_name),
                "h_index": result.get('hIndex', 0),
                "paper_count": result.get('paperCount', 0)
            }
            
            # Cache the result
            HINDEX_CACHE[author_name] = author_data
            
            # Save cache periodically
            if len(HINDEX_CACHE) % 20 == 0:
                save_hindex_cache(HINDEX_CACHE)
                
            return author_data
        else:
            # No results found, create a placeholder
            author_data = {"name": author_name, "h_index": 0, "paper_count": 0}
            HINDEX_CACHE[author_name] = author_data
            return author_data
            
    except Exception as e:
        logging.error(f"Error fetching author info for {author_name}: {str(e)}")
        # Return a placeholder for the author with zero values
        return {"name": author_name, "h_index": 0, "paper_count": 0}

def get_author_info(authors, prominent_authors=None):
    """
    Get information about paper authors, checking prominent authors list and 
    Semantic Scholar API as needed. Process authors concurrently for efficiency.
    
    Args:
        authors: List of author names or objects
        prominent_authors (dict, optional): Dictionary of prominent authors with h-index values
        
    Returns:
        dict: Author information including list of authors and overall score
    """
    # Handle empty authors case
    if not authors:
        return {"authors": [], "author_score": 0}
    
    # Limit to first 5 authors for efficiency
    authors_to_process = authors[:5]
    author_infos = []
    
    # Process authors concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_author = {
            executor.submit(get_author_info_single, author, prominent_authors): author 
            for author in authors_to_process
        }
        
        for future in concurrent.futures.as_completed(future_to_author):
            try:
                author_info = future.result()
                author_infos.append(author_info)
            except Exception as e:
                author = future_to_author[future]
                logging.error(f"Error processing author {author}: {str(e)}")
                author_infos.append({"name": str(author), "h_index": 0, "paper_count": 0})
    
    # Calculate author score based on h-index values
    h_indices = [a.get("h_index", 0) for a in author_infos]
    total_h_index = sum(h_indices)
    
    # Normalize author score to 0-5 scale
    author_score = 0
    if total_h_index > 0:
        # Log scaling to handle very high h-indices
        import math
        author_score = min(5, math.log(1 + total_h_index) * 1.5)
    
    return {
        "authors": author_infos,
        "author_score": author_score
    }

@lru_cache(maxsize=100)
def tag_and_score_cached(text_lower, keyword, pattern):
    """Cached version of keyword matching for tag_and_score"""
    return bool(re.search(pattern, text_lower))

def tag_and_score(text, keywords=None):
    """
    Tags text with keywords and calculates a score.
    This is a wrapper around calculate_score that can be used by other functions.
    """
    result = calculate_score(text, keywords)
    return result["tags"], result["score"]

def commercial_evaluation(paper_or_text, commercial_metrics=None):
    """Evaluate the commercial potential of a paper or text"""
    if commercial_metrics is None:
        commercial_metrics = COMMERCIAL_METRICS
        
    result = {
        "patent_potential": 0,
        "industry_relevance": 0,
        "market_sectors": [],
        "total_commercial": 0
    }
    
    # Handle both Paper objects and raw text
    if hasattr(paper_or_text, 'title') and hasattr(paper_or_text, 'summary'):
        text = paper_or_text.title + " " + paper_or_text.summary
    else:
        text = paper_or_text
        
    text_lower = text.lower()
    
    # Patent potential evaluation
    patent_keywords = commercial_metrics.get("patent_keywords", {})
    patent_tags = []
    patent_score = 0
    
    for keyword, score in patent_keywords.items():
        if keyword.lower() in text_lower:
            patent_tags.append(keyword)
            patent_score += score
    
    # Industry relevance evaluation  
    industry_keywords = commercial_metrics.get("industry_keywords", {})
    industry_tags = []
    industry_score = 0
    
    for keyword, score in industry_keywords.items():
        if keyword.lower() in text_lower:
            industry_tags.append(keyword)
            industry_score += score
    
    # Market sector evaluation
    market_sectors = commercial_metrics.get("market_sectors", {})
    sector_matches = []
    
    for sector, score in market_sectors.items():
        if sector.lower() in text_lower:
            sector_matches.append(sector)
    
    # Normalize scores between 0-5
    max_patent_score = 15  # Adjust as needed
    max_industry_score = 15  # Adjust as needed
    
    normalized_patent = min(5, patent_score / max_patent_score * 5)
    normalized_industry = min(5, industry_score / max_industry_score * 5)
    
    # Calculate total commercial score (patent + industry + sectors)
    total_commercial = normalized_patent + normalized_industry + min(5, len(sector_matches))
    
    # Update result
    result.update({
        "patent_potential": normalized_patent,
        "industry_relevance": normalized_industry,
        "market_sectors": sector_matches,
        "total_commercial": total_commercial
    })
    
    return result

# Optimized paper processing to focus on the most important calculations
def process_paper(paper, keywords, prominent_authors, counts, paper_index):
    """
    Process a single paper: Extract info, calculate scores, handle exceptions.
    
    Args:
        paper: Paper object from arxiv
        keywords: Keywords dictionary for relevance scoring
        prominent_authors: Dictionary of prominent authors
        counts: Dictionary for tracking paper counts
        paper_index: Index of paper being processed
        
    Returns:
        dict: Processed paper information with scores
    """
    try:
        # Extract basic paper information
        paper_info = {
            "title": paper.title,
            "summary": paper.summary,
            "authors": [str(author) for author in paper.authors],
            "published": paper.published.strftime("%Y-%m-%d"),
            "updated": paper.updated.strftime("%Y-%m-%d"),
            "link": paper.entry_id,
            "pdf": f"http://arxiv.org/pdf/{paper.entry_id.split('/')[-1]}.pdf",
            "doi": paper.doi,
            "primary_category": paper.primary_category,
            "categories": paper.categories
        }
        
        # Calculate relevance score
        relevance_result = calculate_score(paper.title + " " + paper.summary, keywords)
        relevance_score = relevance_result["score"]
        paper_info["tags"] = ",".join(relevance_result["tags"])
        
        # Get author information - this can be slow, so we handle errors gracefully
        try:
            author_result = get_author_info(paper.authors, prominent_authors)
            paper_info["first_author"] = str(paper.authors[0]) if paper.authors else ""
            author_score = author_result.get("author_score", 0)
            paper_info["h_index"] = author_result.get("h_index", 0)
        except Exception as e:
            logging.error(f"Author lookup failed: {str(e)}")
            # Default values if author lookup fails
            paper_info["first_author"] = str(paper.authors[0]) if paper.authors else ""
            author_score = 2.0  # Default mid-range score
            paper_info["h_index"] = 30  # Default reasonable h-index
            
        # Calculate total score (weighted average of relevance and author scores)
        total_score = (relevance_score * 0.7) + (author_score * 0.3)
        
        # Add scores to paper info
        paper_info["relevance_score"] = round(relevance_score, 2)
        paper_info["author_score"] = round(author_score, 2)
        paper_info["total_score"] = round(total_score, 2)
        
        # Extract summary bullets
        bullet_points = []
        for line in paper.summary.split('\n'):
            line = line.strip()
            if line:
                bullet_points.append(line)
        paper_info["summary_bullets"] = '\n'.join(bullet_points)
        
        # Add author fields
        paper_info["affiliation"] = ""  # Skip for performance
        paper_info["citations"] = 0  # Skip for performance
        paper_info["author_url"] = ""  # Skip for performance
        # Use string replacement instead of quote_plus
        first_author = str(paper.authors[0]) if paper.authors else ""
        paper_info["linkedin_search"] = f"https://www.google.com/search?q=linkedin+{first_author.replace(' ', '+')}"
        
        if "counts" in counts:
            counts["processed"] += 1
            
        return paper_info
    except Exception as e:
        logging.error(f"Error processing paper {paper_index}: {str(e)}")
        if "counts" in counts:
            counts["errors"] += 1
        return None

def process_papers_batch(papers, keywords, commercial_metrics, max_workers=15):
    """Process a batch of papers in parallel"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Extract prominent authors from commercial metrics
        prominent_authors = commercial_metrics.get("prominent_authors", {}) if commercial_metrics else {}
        # Create counts dictionary to be shared across calls
        counts = {"processed": 0, "errors": 0}
        
        def process_paper_wrapper(index_paper):
            index, paper = index_paper
            try:
                return process_paper(paper, keywords, prominent_authors, counts, index)
            except Exception as e:
                logging.error(f"Error in process_paper_wrapper: {str(e)}")
                traceback.print_exc()
                return None
        
        # Add index to each paper for better error reporting
        indexed_papers = list(enumerate(papers))
        return list(filter(None, executor.map(process_paper_wrapper, indexed_papers)))

# Optimize the main analysis function for speed
def analyze_papers(fields, categories=None, months_back=3, max_papers=20, base_date=None):
    """
    Analyze papers from arXiv for specified months, optimized for speed.
    
    Args:
        fields (list): List of fields to search in paper titles
        categories (list, optional): List of categories to filter papers by.
        months_back (int, optional): Number of months to go back in time. 
        max_papers (int, optional): Maximum number of papers per month.
        base_date (datetime, optional): Base date to calculate months from.
    
    Returns:
        dict: Results organized by month with papers and performance metrics
    """
    from collections import defaultdict
    import time
    
    # Initialize results structure
    results = defaultdict(lambda: {"papers": [], "performance": {}})
    
    # Initialize performance metrics
    performance = {
        "total_time": 0,
        "papers_processed": 0,
        "papers_found": 0,
        "errors": 0,
        "start_time": time.time()
    }
    
    # Set up base date
    if base_date is None:
        base_date = datetime.now()
        
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Configure arxiv client with improved settings
    client = arxiv.Client(
        page_size=100,
        delay_seconds=1,  # Reduce delay to speed up
        num_retries=10    # More retries for reliability
    )
    
    # Set up prominent authors for get_author_info
    try:
        with open(COMMERCIAL_FILE, 'r') as f:
            commercial_metrics = json.load(f)
            prominent_authors = commercial_metrics.get("prominent_authors", {})
    except Exception:
        prominent_authors = {}
    
    # Process each month
    for month in range(months_back):
        month_start = base_date - relativedelta(months=month+1)
        month_end = base_date - relativedelta(months=month)
        
        # Format as YYYYMMDD for arxiv date filter
        start_date = month_start.strftime("%Y%m%d")
        end_date = month_end.strftime("%Y%m%d")
        month_key = month_start.strftime("%Y-%m")
        
        logging.info(f"Analyzing month: {month_key} ({start_date} to {end_date})")
        
        # Construct the query
        title_query = " AND ".join([f"ti:{field}" for field in fields])
        category_filter = " OR ".join([f"cat:{cat}" for cat in categories]) if categories else ""
        date_filter = f"submittedDate:[{start_date}0000 TO {end_date}2359]"
        
        query = f"({title_query})"
        if category_filter:
            query += f" AND ({category_filter})"
        query += f" AND {date_filter}"
        
        logging.info(f"Query: {query}")
        
        # Set up search parameters
        search = arxiv.Search(
            query=query,
            max_results=max_papers,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        month_start_time = time.time()
        month_papers = []
        
        try:
            # Process papers in smaller batches to prevent memory issues
            paper_count = 0
            for paper in client.results(search):
                logging.info(f"Processing paper {paper_count+1}: {paper.title}")
                paper_data = process_paper(paper, KEYWORDS, prominent_authors, {"processed": 0, "errors": 0}, paper_count)
                if paper_data:
                    month_papers.append(paper_data)
                    performance["papers_processed"] += 1
                    paper_count += 1
                
                # Limit to max_papers per month
                if paper_count >= max_papers:
                    logging.info(f"Reached maximum papers limit ({max_papers}) for {month_key}")
                    break
                
                # Run garbage collection every 10 papers to manage memory
                if paper_count % 10 == 0:
                    gc.collect()
                    
            logging.info(f"Processed {paper_count} papers for {month_key}")
                    
        except Exception as e:
            logging.error(f"Error processing month {month_key}: {str(e)}")
            traceback.print_exc()
            performance["errors"] += 1
        
        # Sort papers by total score
        month_papers.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Update results for this month
        results[month_key]["papers"] = month_papers
        results[month_key]["performance"] = {
            "processing_time": round(time.time() - month_start_time, 2),
            "papers_found": len(month_papers)
        }
        
        performance["papers_found"] += len(month_papers)
        logging.info(f"Processed {len(month_papers)} papers for {month_key} in {results[month_key]['performance']['processing_time']} seconds")
        
        # Force garbage collection between months
        gc.collect()
    
    # Update total performance metrics
    performance["total_time"] = round(time.time() - performance["start_time"], 2)
    performance["average_time_per_paper"] = round(performance["total_time"] / max(performance["papers_processed"], 1), 2)
    
    # Add performance metrics to results
    results["performance"] = performance
    
    return dict(results)

# Optionally profile the function to identify memory bottlenecks
# Uncomment to run with memory profiling
# analyze_papers = memory_profile(analyze_papers)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Analyze arXiv papers')
    parser.add_argument('--fields', type=str, nargs='+',
                        help='List of fields to search for')
    parser.add_argument('--months', type=int, default=3,
                        help='Number of months to analyze (default: 3)')
    parser.add_argument('--max-papers', type=int, default=20,
                        help='Maximum papers to return per month (default: 20)')
    parser.add_argument('--batch-size', type=int, default=50,
                        help='Batch size for parallel processing (default: 50)')
    parser.add_argument('--base-date', type=str,
                        help='Base date for analysis in YYYY-MM-DD format (default: today)')
    
    args = parser.parse_args()
    
    try:
        base_date = None
        if args.base_date:
            base_date = datetime.strptime(args.base_date, '%Y-%m-%d')
            
        results = analyze_papers(
            fields=args.fields,
            months_back=args.months,
            max_papers=args.max_papers,
            base_date=base_date
        )
        
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        debug_print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 