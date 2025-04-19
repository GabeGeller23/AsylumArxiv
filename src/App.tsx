import { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import PaperTable from './components/PaperTable';
import RunButton from './components/RunButton';
import Navigation from './components/Navigation';
import { Paper } from './types';
import { startOfMonth } from 'date-fns';

const queryClient = new QueryClient();

function App() {
  const [selectedDate, setSelectedDate] = useState<Date>(startOfMonth(new Date()));

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <header className="mb-8">
            <div className="flex justify-between items-center">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Top 20 Commercially Viable Papers
              </h1>
              <RunButton />
            </div>
            <p className="mt-2 text-gray-600 dark:text-gray-300">
              Discover the most commercially promising research papers from arXiv
            </p>
          </header>

          <Navigation 
            selectedDate={selectedDate} 
            onDateChange={setSelectedDate} 
          />

          <main className="mt-8">
            <PaperTable date={selectedDate} />
          </main>
        </div>
      </div>
    </QueryClientProvider>
  );
}

export default App; 