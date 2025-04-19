import React, { useState, useEffect } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';

interface KeywordSettingsProps {
  onClose: () => void;
  onSuccess: () => void;
}

const DEFAULT_KEYWORDS = {
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

const KeywordSettings: React.FC<KeywordSettingsProps> = ({ onClose, onSuccess }) => {
  const [keywords, setKeywords] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newKeyword, setNewKeyword] = useState('');
  const [newWeight, setNewWeight] = useState(3);
  const [apiUrl, setApiUrl] = useState<string>('http://localhost:3003');

  useEffect(() => {
    fetchKeywords();
  }, []);

  const fetchKeywords = async () => {
    try {
      setLoading(true);
      
      console.log(`Fetching keywords from ${apiUrl}/api/keywords`);
      const response = await fetch(`${apiUrl}/api/keywords`);
      
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error(`Expected JSON response but got ${contentType}`);
      }
      
      const data = await response.json();
      
      // Check if we received valid data
      if (data && typeof data === 'object' && Object.keys(data).length > 0) {
        setKeywords(data);
      } else {
        // Use default keywords if server returned empty or invalid data
        console.warn('Received empty keywords from server, using defaults');
        setKeywords(DEFAULT_KEYWORDS);
      }
    } catch (err: any) {
      console.error('Failed to fetch keywords:', err.message);
      setError(`Failed to fetch keywords: ${err.message}`);
      setKeywords(DEFAULT_KEYWORDS); // Use defaults on error
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      
      // If keywords are empty, use defaults
      const keywordsToSave = Object.keys(keywords).length > 0 ? keywords : DEFAULT_KEYWORDS;
      
      const response = await fetch(`${apiUrl}/api/keywords`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(keywordsToSave)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      
      onSuccess();
    } catch (err: any) {
      setError(`Failed to save keywords: ${err.message}`);
      setLoading(false);
    }
  };

  const updateKeyword = (key: string, value: number) => {
    setKeywords({
      ...keywords,
      [key]: value
    });
  };

  const deleteKeyword = (key: string) => {
    const newKeywords = { ...keywords };
    delete newKeywords[key];
    setKeywords(newKeywords);
  };

  const addKeyword = () => {
    if (newKeyword && newKeyword.trim() && !keywords[newKeyword]) {
      setKeywords({
        ...keywords,
        [newKeyword]: newWeight
      });
      setNewKeyword('');
      setNewWeight(3);
    }
  };

  // Helper to ensure we always have keywords
  const ensureKeywords = () => {
    if (Object.keys(keywords).length === 0) {
      setKeywords(DEFAULT_KEYWORDS);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex justify-between items-center border-b border-gray-200 dark:border-gray-700 p-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Keyword Settings</h2>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>
        
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 dark:bg-red-900 dark:border-red-600 dark:text-red-100">
            {error}
          </div>
        )}
        
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="flex justify-center items-center h-40">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-12 gap-4 font-medium text-sm text-gray-500 dark:text-gray-400 pb-2 border-b border-gray-200 dark:border-gray-700">
                <div className="col-span-6">Keyword</div>
                <div className="col-span-4">Weight (1-10)</div>
                <div className="col-span-2">Actions</div>
              </div>
              
              {Object.entries(keywords).length === 0 ? (
                <div className="py-4 text-center text-gray-500 dark:text-gray-400">
                  <p>No keywords found. Add some below or click Save to use defaults.</p>
                </div>
              ) : (
                Object.entries(keywords).map(([keyword, weight]) => (
                  <div key={keyword} className="grid grid-cols-12 gap-4 items-center py-2 border-b border-gray-100 dark:border-gray-700">
                    <div className="col-span-6 text-gray-900 dark:text-gray-100 font-medium">
                      {keyword}
                    </div>
                    <div className="col-span-4">
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={weight}
                        onChange={(e) => updateKeyword(keyword, parseInt(e.target.value))}
                        className="w-full"
                      />
                      <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {weight}/10
                      </div>
                    </div>
                    <div className="col-span-2">
                      <button 
                        onClick={() => deleteKeyword(keyword)}
                        className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))
              )}
              
              <div className="grid grid-cols-12 gap-4 items-center pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="col-span-6">
                  <input
                    type="text"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    placeholder="New keyword"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div className="col-span-4">
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={newWeight}
                    onChange={(e) => setNewWeight(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {newWeight}/10
                  </div>
                </div>
                <div className="col-span-2">
                  <button 
                    onClick={addKeyword}
                    disabled={!newKeyword.trim()}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 disabled:bg-indigo-400 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <PlusIcon className="h-4 w-4 mr-1" />
                    Add
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="flex justify-end space-x-3 bg-gray-50 dark:bg-gray-700 px-4 py-3 border-t border-gray-200 dark:border-gray-600">
          <button 
            onClick={() => {
              ensureKeywords();
              onClose();
            }} 
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button 
            onClick={() => {
              ensureKeywords();
              handleSave();
            }} 
            disabled={loading}
            className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400"
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default KeywordSettings; 