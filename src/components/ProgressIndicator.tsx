import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

interface ProgressIndicatorProps {
  isVisible?: boolean;
  message?: string;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ isVisible = true, message }) => {
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!isVisible) return;
    
    // Initialize Socket.IO connection to the server
    const socket = io('https://asylum-arxiv.vercel.app');

    // Connection established
    socket.on('connect', () => {
      console.log('Connected to progress updates');
      setConnected(true);
      setProgressMessages([message || 'Connected to server. Waiting for analysis to start...']);
    });

    // Receive progress updates
    socket.on('analysisProgress', (data: { message: string }) => {
      setProgressMessages(prev => [...prev, data.message]);
    });

    // Connection lost
    socket.on('disconnect', () => {
      console.log('Disconnected from progress updates');
      setConnected(false);
    });

    // Clean up on unmount
    return () => {
      socket.disconnect();
    };
  }, [isVisible, message]);

  // If a message is provided but no socket updates have arrived yet,
  // display the message directly
  useEffect(() => {
    if (message && progressMessages.length === 0) {
      setProgressMessages([message]);
    }
  }, [message]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden p-6 flex flex-col">
        <h2 className="text-xl font-bold mb-4">Analysis Progress</h2>
        
        <div className="flex-grow overflow-y-auto border border-gray-200 rounded p-4 bg-gray-50 font-mono text-sm mb-4">
          {progressMessages.length === 0 ? (
            <p className="text-gray-500">{message || 'Waiting for progress updates...'}</p>
          ) : (
            progressMessages.map((msg, index) => (
              <div key={index} className="mb-1">
                <span className="text-green-600">→</span> {msg}
              </div>
            ))
          )}
        </div>
        
        <div className="flex items-center mt-2">
          <div className={`w-3 h-3 rounded-full mr-2 ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            {connected ? 'Connected to server' : 'Disconnected from server'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator; 