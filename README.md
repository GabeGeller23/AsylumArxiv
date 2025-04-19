# Viable Papers

A web application for discovering the 20 most commercially viable research papers each month from arXiv.

## Features

- Shows the top 20 most commercially viable papers for each month
- Automatically scores papers based on commercial viability metrics
- Allows toggling keyword highlighting in paper titles and abstracts
- Authors displayed with proper comma separation
- Detailed view of each paper with full abstract and metadata
- Customizable keywords with importance weights

## Getting Started

### Prerequisites

- Node.js 16.x or higher
- npm or yarn

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/viable-papers.git
cd viable-papers
```

2. Install dependencies for frontend
```bash
npm install
```

3. Install dependencies for server
```bash
cd server
npm install
```

### Running the application

1. Start the server first
```bash
cd server
npm start
```

The server will find an available port starting from 3001.

2. In a new terminal, start the frontend
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Usage

- View papers by month using the navigation controls
- Click "Analyze Papers" to fetch and analyze new papers
- Toggle keyword highlighting with the "Highlighting" button
- Click "Keyword Settings" to customize important keywords
- Click on any paper to view its full details
- See authors, abstract, and commercial viability scores for each paper

## How it works

The application:
1. Fetches recent papers from arXiv
2. Analyzes them for commercial viability using:
   - Keyword relevance scoring
   - Author impact metrics (h-index)
   - Industry-specific signals
3. Presents the top 20 most viable papers per month
4. Highlights important keywords to quickly identify relevance

## License

MIT 