import { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';

const API_URL = 'https://asylum-arxiv.vercel.app';

const RunButton = () => {
  const [isRunning, setIsRunning] = useState(false);
  const queryClient = useQueryClient();

  const { mutate, isError } = useMutation(
    async () => {
      const response = await fetch(`${API_URL}/api/analyze`, { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ months: 3, maxPapers: 20 })
      });
      
      if (!response.ok) throw new Error('Analysis failed');
      return response.json();
    },
    {
      onMutate: () => {
        setIsRunning(true);
      },
      onSuccess: () => {
        // We'll let the socket.io updates handle the completion notification
        // The PaperTable component will update when it gets socket notifications
      },
      onError: (error) => {
        console.error('Analysis error:', error);
        alert('Analysis failed. Please check the console for details.');
        setIsRunning(false);
      },
      onSettled: () => {
        // We don't want to automatically set isRunning to false
        // Since the actual analysis might still be running on the server
        // The socket.io updates will handle this
        queryClient.invalidateQueries('papers');
      }
    }
  );

  return (
    <button
      onClick={() => mutate()}
      disabled={isRunning}
      className={`
        inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white
        ${isRunning
          ? 'bg-indigo-400 cursor-not-allowed'
          : 'bg-indigo-600 hover:bg-indigo-700'
        }
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
      `}
    >
      {isRunning ? (
        <>
          <svg
            className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Analyzing Papers...
        </>
      ) : (
        'Analyze Papers'
      )}
    </button>
  );
};

export default RunButton; 