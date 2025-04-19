import { format, subMonths, addMonths, startOfMonth } from 'date-fns';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/solid';

interface NavigationProps {
  selectedDate: Date;
  onDateChange: (date: Date) => void;
}

const Navigation: React.FC<NavigationProps> = ({ selectedDate, onDateChange }) => {
  const goToPreviousMonth = () => {
    onDateChange(startOfMonth(subMonths(selectedDate, 1)));
  };

  const goToNextMonth = () => {
    onDateChange(startOfMonth(addMonths(selectedDate, 1)));
  };

  const goToCurrentMonth = () => {
    onDateChange(startOfMonth(new Date()));
  };

  return (
    <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 pb-5">
      <div className="flex-1 flex justify-between sm:hidden">
        <button
          onClick={goToPreviousMonth}
          className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
        >
          Previous
        </button>
        <button
          onClick={goToNextMonth}
          className="ml-3 inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
        >
          Next
        </button>
      </div>
      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {format(selectedDate, 'MMMM yyyy')}
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Viewing commercially viable papers for this month
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={goToPreviousMonth}
            className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            <ChevronLeftIcon className="h-5 w-5 mr-1" />
            Previous Month
          </button>
          <button
            onClick={goToCurrentMonth}
            className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            Current Month
          </button>
          <button
            onClick={goToNextMonth}
            className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            Next Month
            <ChevronRightIcon className="h-5 w-5 ml-1" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Navigation; 