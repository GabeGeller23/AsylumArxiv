import { Fragment, useEffect, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Paper } from '../types';
import { XMarkIcon } from '@heroicons/react/24/outline';
import HighlightedText from './HighlightedText';

interface PaperDetailProps {
  paper: Paper;
  onClose: () => void;
  keywords?: string[];
  highlightEnabled?: boolean;
}

const PaperDetail: React.FC<PaperDetailProps> = ({ 
  paper, 
  onClose,
  keywords = [],
  highlightEnabled = false
}) => {
  const [isReady, setIsReady] = useState(false);

  // Delay rendering of highlighted content for performance
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsReady(true);
    }, 50);
    
    return () => clearTimeout(timer);
  }, []);

  return (
    <Transition.Root show={true} as={Fragment}>
      <Dialog as="div" className="fixed z-10 inset-0 overflow-y-auto" onClose={onClose}>
        <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Dialog.Overlay className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
          </Transition.Child>

          <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
            &#8203;
          </span>

          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enterTo="opacity-100 translate-y-0 sm:scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 translate-y-0 sm:scale-100"
            leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          >
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
              <div className="absolute top-0 right-0 pt-4 pr-4">
                <button
                  type="button"
                  className="bg-white dark:bg-gray-800 rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  onClick={onClose}
                >
                  <span className="sr-only">Close</span>
                  <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                </button>
              </div>
              
              <div className="px-4 pt-5 pb-4 sm:p-6">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                    <Dialog.Title as="h3" className="text-xl leading-6 font-bold text-gray-900 dark:text-white">
                      {isReady ? (
                        <HighlightedText 
                          text={paper.title}
                          keywords={keywords}
                          highlightEnabled={highlightEnabled}
                        />
                      ) : paper.title}
                    </Dialog.Title>
                    
                    <div className="flex flex-wrap justify-between items-center mt-2">
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        {typeof paper.authors === 'string' 
                          ? paper.authors 
                          : Array.isArray(paper.authors) 
                            ? paper.authors.join(', ') 
                            : ''}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Published: {paper.published}
                      </p>
                    </div>
                    
                    {/* Commercial Viability Metrics */}
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mt-4">
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Commercial Viability Metrics</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow">
                          <div className="text-xs text-gray-500 dark:text-gray-400">Relevance Score</div>
                          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{paper.relevance_score?.toFixed(1) || 'N/A'}</div>
                          <div className="text-xs text-gray-400 mt-1">Based on keyword matching</div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow">
                          <div className="text-xs text-gray-500 dark:text-gray-400">Author Impact</div>
                          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">h-{paper.h_index || 'N/A'}</div>
                          <div className="text-xs text-gray-400 mt-1">h-index: {paper.h_index || 'N/A'}</div>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow">
                          <div className="text-xs text-gray-500 dark:text-gray-400">Total Score</div>
                          <div className="text-2xl font-bold text-green-600 dark:text-green-400">{paper.total_score?.toFixed(1) || 'N/A'}</div>
                          <div className="text-xs text-gray-400 mt-1">Combined commercial viability</div>
                        </div>
                      </div>
                    </div>

                    {/* Abstract */}
                    <div className="mt-6">
                      <h4 className="text-base font-medium text-gray-900 dark:text-white">Abstract</h4>
                      <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">
                        {isReady ? (
                          <HighlightedText 
                            text={paper.summary}
                            keywords={keywords}
                            highlightEnabled={highlightEnabled}
                          />
                        ) : paper.summary}
                      </p>
                    </div>

                    {/* Key Points */}
                    {paper.summary_bullets && (
                      <div className="mt-6">
                        <h4 className="text-base font-medium text-gray-900 dark:text-white">Key Points</h4>
                        <ul className="mt-2 list-disc pl-5 space-y-1">
                          {paper.summary_bullets.split('\n').map((bullet, index) => {
                            const trimmed = bullet.trim();
                            if (!trimmed) return null;
                            return (
                              <li key={index} className="text-sm text-gray-700 dark:text-gray-300">
                                {isReady ? (
                                  <HighlightedText 
                                    text={trimmed}
                                    keywords={keywords}
                                    highlightEnabled={highlightEnabled}
                                  />
                                ) : trimmed}
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    )}

                    {/* Tags */}
                    {paper.tags && (
                      <div className="mt-6">
                        <h4 className="text-base font-medium text-gray-900 dark:text-white">Tags</h4>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {paper.tags.split(',').map((tag, i) => (
                            <span 
                              key={i} 
                              className="inline-block px-3 py-1 bg-blue-500 text-white text-xs font-medium rounded-full"
                            >
                              {tag.trim()}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Links */}
                    <div className="mt-8 pt-5 border-t border-gray-200 dark:border-gray-700">
                      <div className="flex flex-wrap gap-4">
                        <a
                          href={paper.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          View on arXiv
                        </a>
                        {paper.author_url && (
                          <a
                            href={paper.author_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-indigo-900 dark:text-indigo-200"
                          >
                            Author Profile
                          </a>
                        )}
                        {paper.linkedin_search && (
                          <a
                            href={paper.linkedin_search}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-900 dark:text-blue-200"
                          >
                            Find on LinkedIn
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

export default PaperDetail; 