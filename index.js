import express from 'express';
import cors from 'cors';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs/promises';
import { existsSync } from 'fs';
import { Server as SocketServer } from 'socket.io';
import http from 'http';
import bodyParser from 'body-parser';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Path to the keywords file
const KEYWORDS_FILE = join(__dirname, 'python', 'keywords.json');
const COMMERCIAL_FILE = join(__dirname, 'python', 'commercial_metrics.json');

const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: '5mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '5mb' }));

// Create HTTP server
const server = http.createServer(app);

// Set up Socket.IO
const io = new SocketServer(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Socket.IO connections
io.on('connection', (socket) => {
  console.log('Client connected');
  
  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

// Cache for storing paper results by month
let paperCache = new Map();

// Initialize default keywords if they don't exist
async function initializeKeywords() {
  try {
    if (!existsSync(KEYWORDS_FILE)) {
      const defaultKeywords = {
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
      };
      
      await fs.writeFile(
        KEYWORDS_FILE,
        JSON.stringify(defaultKeywords, null, 2),
        'utf8'
      );
      
      console.log('Created default keywords file');
    }
  } catch (error) {
    console.error('Error initializing keywords file:', error);
  }
}

// Initialize keywords
initializeKeywords();

// Helper function to run Python script
function runPythonScript(months = 1, specificMonth = null, maxWorkers = 10, maxPapers = 100) {
  return new Promise((resolve, reject) => {
    const pythonScript = join(__dirname, 'python', 'paper_analyzer.py');
    const args = ['--fields', 'machine', 'learning', '--months', months.toString(), '--max-papers', maxPapers.toString()];
    
    if (specificMonth) {
      // If a specific month is requested, set the base date for Python script
      const [year, month] = specificMonth.split('-');
      const baseDate = new Date(parseInt(year), parseInt(month) - 1, 28); // Use end of month
      args.push('--base-date', baseDate.toISOString().split('T')[0]);
    }
    
    console.log('Running Python script with args:', args);
    
    // Create the Python process
    const process = spawn('python3', [pythonScript, ...args]);
    
    let output = '';
    let errorOutput = '';
    let progressTimestamp = Date.now();
    const PROGRESS_THROTTLE_MS = 500; // Throttle progress updates to 500ms

    process.stdout.on('data', (data) => {
      output += data.toString();
    });

    process.stderr.on('data', (data) => {
      const msg = data.toString();
      errorOutput += msg;
      
      // Check for progress updates and throttle to avoid overwhelming the UI
      if (msg.includes('PROGRESS:')) {
        const now = Date.now();
        if (now - progressTimestamp > PROGRESS_THROTTLE_MS) {
          progressTimestamp = now;
          const progressMsg = msg.split('PROGRESS:')[1].trim();
          console.log(`Analysis progress: ${progressMsg}`);
          
          // Emit progress to all connected clients
          io.emit('analysisProgress', { message: progressMsg });
        }
      } else {
        console.error(`Python stderr: ${msg}`);
      }
    });

    process.on('close', (code) => {
      if (code !== 0) {
        console.error(`Python process exited with code ${code}`);
        reject(new Error(`Python script failed: ${errorOutput}`));
        return;
      }
      
      try {
        const result = JSON.parse(output);
        resolve(result);
      } catch (error) {
        console.error('Failed to parse Python output:', error);
        reject(error);
      }
    });

    process.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      reject(error);
    });
  });
}

// GET papers for a specific month
app.get('/api/papers', async (req, res) => {
  const { month, maxWorkers, maxPapers } = req.query;
  const monthKey = month ? month : getMonthKey(new Date().toISOString());
  const workers = maxWorkers ? parseInt(maxWorkers) : 10;
  const papers = maxPapers ? parseInt(maxPapers) : 20;
  
  console.log('Fetching papers for month:', monthKey, 'with max workers:', workers, 'max papers:', papers);
  
  try {
    // Check cache first
    if (paperCache.has(monthKey)) {
      console.log('Returning cached results for month:', monthKey);
      return res.json(paperCache.get(monthKey));
    }

    // If not in cache, run analysis for the specific month
    console.log('Running new analysis...');
    const results = await runPythonScript(1, monthKey, workers, papers);
    
    // Cache the results
    if (results && results[monthKey] && results[monthKey].papers) {
      paperCache.set(monthKey, results[monthKey]);
    }
    
    return res.json(results[monthKey]);
  } catch (error) {
    console.error('Error fetching papers:', error);
    res.status(500).json({ 
      error: 'Failed to fetch papers', 
      details: error.message 
    });
  }
});

// GET keywords
app.get('/api/keywords', async (req, res) => {
  try {
    // Check if keywords file exists
    if (!existsSync(KEYWORDS_FILE)) {
      await initializeKeywords();
    }
    
    // Read keywords file
    const keywordsData = await fs.readFile(KEYWORDS_FILE, 'utf8');
    const keywords = JSON.parse(keywordsData);
    
    res.json(keywords);
  } catch (error) {
    console.error('Error fetching keywords:', error);
    res.status(500).json({ 
      error: 'Failed to fetch keywords', 
      details: error.message 
    });
  }
});

// POST update keywords
app.post('/api/keywords', async (req, res) => {
  try {
    const keywords = req.body;
    
    // Validate keywords
    if (!keywords || typeof keywords !== 'object') {
      return res.status(400).json({ error: 'Invalid keywords format' });
    }
    
    // Save keywords to file
    await fs.writeFile(
      KEYWORDS_FILE, 
      JSON.stringify(keywords, null, 2),
      'utf8'
    );
    
    console.log('Keywords updated:', keywords);
    
    // Clear paper cache to force reanalysis with new keywords
    paperCache.clear();
    
    res.json({ success: true, message: 'Keywords updated successfully' });
  } catch (error) {
    console.error('Error updating keywords:', error);
    res.status(500).json({ 
      error: 'Failed to update keywords', 
      details: error.message 
    });
  }
});

// Health check endpoint for detecting server
app.head('/api/health', (req, res) => {
  res.status(200).end();
});

app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Function to get cache key for a specific month
function getMonthKey(date) {
  return date.substring(0, 7); // YYYY-MM format
}

// Add error handling for port conflicts
const PORT = process.env.PORT || 3001;
const MAX_PORT_ATTEMPTS = 10;

// Function to start server with port fallback
function startServer(port, attempt = 1) {
  try {
    const serverInstance = app.listen(port, () => {
      console.log(`Server running on port ${port}`);
      console.log('Socket.IO enabled for real-time progress updates');
      console.log(`Python script path: ${join(__dirname, 'python', 'paper_analyzer.py')}`);
    });

    // Set up Socket.IO on the server instance
    io.attach(serverInstance);

    // Handle server errors
    serverInstance.on('error', (e) => {
      if (e.code === 'EADDRINUSE') {
        if (attempt <= MAX_PORT_ATTEMPTS) {
          console.log(`Port ${port} is already in use. Trying port ${port + 1}...`);
          startServer(port + 1, attempt + 1);
        } else {
          console.error(`Failed to find an available port after ${MAX_PORT_ATTEMPTS} attempts.`);
          process.exit(1);
        }
      } else {
        console.error(`Server error: ${e.message}`);
        process.exit(1);
      }
    });

    return serverInstance;
  } catch (error) {
    console.error(`Error starting server: ${error.message}`);
    if (attempt <= MAX_PORT_ATTEMPTS) {
      console.log(`Trying port ${port + 1}...`);
      startServer(port + 1, attempt + 1);
    } else {
      console.error(`Failed to start server after ${MAX_PORT_ATTEMPTS} attempts.`);
      process.exit(1);
    }
  }
}

// Start the server with port fallback
startServer(PORT);

// Handle process termination
process.on('SIGINT', () => {
  console.log('Server shutting down...');
  process.exit(0);
}); 