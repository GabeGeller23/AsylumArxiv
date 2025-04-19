#!/usr/bin/env python3
import argparse
import arxiv
import time
import json
import logging
import concurrent.futures
import datetime
import html
import re
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default keywords for search
DEFAULT_KEYWORDS = {
    "title_terms": [
        "machine learning", "deep learning", "neural network", "artificial intelligence", 
        "ai", "natural language processing", "nlp", "computer vision", "reinforcement learning",
        "transformer", "large language model", "llm", "generative ai", "diffusion model",
        "stable diffusion", "multimodal", "foundation model", "gpt", "attention mechanism",
        "bert", "gan", "transformer architecture", "vision transformer", "zero shot", "few shot",
        "self-supervised", "unsupervised learning", "supervised learning", "fine-tuning"
    ],
    "abstract_terms": [
        "algorithm", "framework", "optimization", "inference", "training", "fine-tuning",
        "performance", "state-of-the-art", "sota", "benchmark", "dataset", "accuracy",
        "precision", "recall", "f1", "neural", "autonomous", "prediction", "classification",
        "segmentation", "detection", "generation", "synthesis", "augmentation"
    ],
    "categories": [
        "cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE", "stat.ML"
    ]
}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Analyze real arXiv papers month-by-month')
    parser.add_argument('--fields', nargs='+', default=['machine', 'learning'], help='Search terms')
    parser.add_argument('--months', type=int, default=1, help='Number of months to analyze')
    parser.add_argument('--max-papers', type=int, default=20, help='Max papers per month')
    parser.add_argument('--batch-size', type=int, default=20, help='Concurrency batch size')
    parser.add_argument('--base-date', type=str, help='Base date (YYYY-MM-DD)')
    return parser.parse_args()

def get_month_range(base_date: Optional[str], months: int) -> List[datetime.date]:
    """Get a list of dates for the specified months"""
    if base_date:
        try:
            end_date = datetime.datetime.strptime(base_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {base_date}")
            end_date = datetime.date.today()
    else:
        end_date = datetime.date.today()
    
    dates = []
    for i in range(months):
        year = end_date.year
        month = end_date.month - i
        while month <= 0:
            month += 12
            year -= 1
        dates.append(datetime.date(year, month, 1))
    
    return dates

def construct_search_query(fields: List[str], month_date: datetime.date) -> str:
    """Construct a search query for arXiv combining title and abstract terms with categories"""
    # Use a more focused search query with fewer terms to avoid query length issues
    
    # Limit the number of terms to prevent query length issues
    max_title_terms = 10
    max_abstract_terms = 5
    
    # Add the user-provided fields to our default keywords, but limit total count
    all_title_terms = list(set(DEFAULT_KEYWORDS['title_terms'][:max_title_terms] + fields[:5]))[:max_title_terms]
    abstract_terms = DEFAULT_KEYWORDS['abstract_terms'][:max_abstract_terms]
    
    # Format the title terms for the query
    title_terms = " OR ".join([f'ti:"{term}"' for term in all_title_terms])
    
    # Format the abstract terms for the query
    abstract_terms = " OR ".join([f'abs:"{term}"' for term in abstract_terms])
    
    # Format the category filter
    category_filter = " OR ".join([f'cat:{cat}' for cat in DEFAULT_KEYWORDS['categories']])
    
    # Date range: from start of this month to start of next month
    start = month_date
    if month_date.month == 12:
        end = datetime.date(month_date.year + 1, 1, 1)
    else:
        end = datetime.date(month_date.year, month_date.month + 1, 1)

    date_filter = f'submittedDate:[{start.strftime("%Y%m%d")} TO {end.strftime("%Y%m%d")}]'
    
    # Create a simple, focused query without date filters (we'll filter results after fetching)
    query = f'(({title_terms}) OR ({abstract_terms})) AND ({category_filter}) AND {date_filter}'
    
    logger.info(f"Query: {query}")
    return query

def safe_html_decode(text: Any) -> str:
    """Safely decode HTML entities and remove control characters"""
    try:
        # Ensure we're working with a string
        if not isinstance(text, str):
            text = str(text)
            
        # First, decode HTML entities
        text = html.unescape(text)
        # Replace newlines with spaces
        text = text.replace('\n', ' ').replace('\r', '')
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Normalize spaces
        text = ' '.join(text.split())
        return text
    except Exception as e:
        logger.warning(f"Error decoding text: {e}")
        # Return a sanitized version of the original text if decoding fails
        if isinstance(text, str):
            return re.sub(r'[^\x20-\x7E]', '', text)
        else:
            return "Unknown Text"

def process_paper(paper, counter) -> Dict[str, Any]:
    """Process a paper and extract relevant information"""
    # Extract data from the arXiv result
    published = paper.published
    updated = paper.updated
    title = safe_html_decode(paper.title)
    summary = safe_html_decode(paper.summary)
    authors = [safe_html_decode(a.name if hasattr(a, 'name') else str(a)) for a in paper.authors]
    
    # Extract the main author
    first_author = authors[0] if authors else "Unknown"
    
    # Generate summary bullets using key sentences
    summary_sentences = summary.split('. ')
    bullets = [s.strip() for s in summary_sentences if len(s) > 20 and any(k in s.lower() for k in ['novel', 'propose', 'improve', 'develop', 'achieve', 'experiment', 'result'])][:3]
    
    # Format bullets
    summary_bullets = "\n".join([f"- {b}" for b in bullets])
    
    # Extract categories for tags
    tags = ','.join([cat.replace('cs.', '') for cat in paper.categories])
    
    # Compute relevance score (simplified for now)
    relevance_score = 4.0 + 0.5 * (len(authors) / 5)
    
    # Generate h-index (simulated)
    h_index = 40 + (counter % 60)  # 40-100 range
    
    # Calculate total score 
    total_score = (relevance_score * 0.7) + ((h_index / 100) * 5 * 0.3)
    
    # Format and return the processed paper data
    return {
        'title': title,
        'authors': authors,
        'first_author': first_author,
        'summary': summary,
        'published': published.strftime('%Y-%m-%d'),
        'updated': updated.strftime('%Y-%m-%d'),
        'link': paper.entry_id,
        'pdf_url': paper.pdf_url,
        'summary_bullets': summary_bullets,
        'tags': tags,
        'relevance_score': round(relevance_score, 2),
        'h_index': h_index,
        'citations': h_index * 5,  # Simulated citation count
        'author_url': f"https://scholar.google.com/scholar?q={first_author.replace(' ', '+')}",
        'linkedin_search': f"https://www.google.com/search?q=linkedin+{first_author.replace(' ', '+')}",
        'total_score': round(total_score, 2)
    }

def analyze_papers(fields: List[str], month_date: datetime.date, max_papers: int, batch_size: int) -> Dict[str, Any]:
    """Analyze papers for a specific month"""
    start_time = time.time()
    month_key = month_date.strftime('%Y-%m')
    
    logger.info(f"Analyzing {month_key}")
    print(f"PROGRESS: Starting analysis for {month_key}", file=logging.getLogger().handlers[0].stream)
    
    # Construct the search query
    query = construct_search_query(fields, month_date)
    
    # Set up the search client with increased timeout
    client = arxiv.Client(page_size=100, delay_seconds=1, num_retries=3)
    
    # Configure the search query
    search = arxiv.Search(
        query=query,
        max_results=max_papers * 5,  # Get more results for better filtering
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # Fetch results
    all_results = list(client.results(search))
    
    # Create start and end dates for the month
    year = month_date.year
    month = month_date.month
    
    # Create start and end dates for the month
    if month == 12:
        next_month_year = year + 1
        next_month = 1
    else:
        next_month_year = year
        next_month = month + 1
    
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{next_month_year}-{next_month:02d}-01"
    
    # Filter results by date
    results = [
        paper for paper in all_results
        if datetime.date.fromisoformat(start_date) <= paper.published.date() < datetime.date.fromisoformat(end_date)
    ]
    
    logger.info(f"Found {len(results)} papers for {month_key} after date filtering")
    print(f"PROGRESS: Found {len(results)} papers for {month_key} after date filtering", file=logging.getLogger().handlers[0].stream)
    
    # Process papers in parallel
    processed_papers = []
    
    # Get the appropriate batch size based on the number of results
    actual_batch_size = min(batch_size, len(results))
    
    # Process papers in batches
    with concurrent.futures.ThreadPoolExecutor(max_workers=actual_batch_size) as executor:
        # Submit all tasks
        future_to_paper = {executor.submit(process_paper, paper, i): paper 
                          for i, paper in enumerate(results[:max_papers])}
        
        # Process results as they complete
        for i, future in enumerate(concurrent.futures.as_completed(future_to_paper)):
            try:
                data = future.result()
                processed_papers.append(data)
                
                # Log progress
                if (i + 1) % 5 == 0 or (i + 1) == len(future_to_paper):
                    progress_percent = ((i + 1) / len(future_to_paper)) * 100
                    print(f"PROGRESS: Processed {i + 1}/{len(future_to_paper)} papers ({progress_percent:.1f}%)", 
                          file=logging.getLogger().handlers[0].stream)
            except Exception as e:
                logger.error(f"Error processing paper: {e}")
    
    # Sort papers by total score
    processed_papers.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Limit to max_papers
    processed_papers = processed_papers[:max_papers]
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    logger.info(f"Processed {len(processed_papers)} papers in {processing_time:.2f} seconds")
    
    # Return results with performance metrics
    return {
        'papers': processed_papers,
        'performance': {
            'processing_time': processing_time,
            'papers_found': len(results),
            'papers_processed': len(processed_papers),
            'average_time_per_paper': processing_time / max(1, len(processed_papers))
        }
    }

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Get the date range
    dates = get_month_range(args.base_date, args.months)
    
    # Initialize results dictionary
    results = {}
    
    # Analyze papers for each month
    for date in dates:
        month_key = date.strftime('%Y-%m')
        results[month_key] = analyze_papers(args.fields, date, args.max_papers, args.batch_size)
    
    # Add performance data
    results['_performance'] = {
        'total_time': sum(month['performance']['processing_time'] for month in results.values() if '_performance' not in month),
        'total_papers': sum(len(month['papers']) for month in results.values() if '_performance' not in month),
    }
    
    # Output results as JSON
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main() 