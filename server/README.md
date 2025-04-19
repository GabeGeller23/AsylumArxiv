# Viable Papers - Server

This is the server component of the Viable Papers application, which helps analyze and rank arXiv papers based on their commercial viability and relevance.

## Setup

### Prerequisites
- Node.js 16+ 
- Python 3.9+
- npm or yarn

### Installation

1. Install Node.js dependencies:
```bash
npm install
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
npm start
```

By default, the server will run on port 3001.

## API Endpoints

- `GET /api/papers?month=YYYY-MM` - Get papers for a specific month
- `POST /api/analyze` - Trigger analysis for multiple months
- `GET /api/authors?name=AuthorName` - Get information about a specific author
- `GET /api/keywords` - Get current keyword weights
- `POST /api/keywords` - Update keyword weights

## Performance Optimization

The paper analysis process has been optimized with:

1. Concurrent processing using ThreadPoolExecutor
2. Connection pooling for API requests
3. Caching of author information
4. Batched processing to reduce memory usage
5. LRU caching for repetitive calculations

## Python Script Parameters

The `analyze_papers.py` script can be run directly with these parameters:

```bash
python analyze_papers.py --fields machine learning --months 3 --max-papers 100 --batch-size 20 --base-date 2024-04-15
```

Parameters:
- `--fields`: Keywords to search for in paper titles
- `--months`: Number of months to analyze
- `--max-papers`: Maximum papers to return per month
- `--batch-size`: Batch size for parallel processing
- `--base-date`: Base date for analysis (YYYY-MM-DD format)

## Troubleshooting

- If the server fails to start, check if port 3001 is already in use
- If Python script execution fails, check if all dependencies are installed
- For slow performance, try increasing the batch size and reducing max papers 