import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useQuery } from 'react-query';
import { AuthorInfo } from '../types';

interface AuthorModalProps {
  authorName: string;
  onClose: () => void;
}

const AuthorModal: React.FC<AuthorModalProps> = ({ authorName, onClose }) => {
  const { data: author, isLoading } = useQuery<AuthorInfo>(
    ['author', authorName],
    async () => {
      const response = await fetch(`/api/authors?name=${encodeURIComponent(authorName)}`);
      if (!response.ok) throw new Error('Failed to fetch author info');
      return response.json();
    }
  );

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
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div>
                <div className="mt-3 text-center sm:mt-5">
                  <Dialog.Title as="h3" className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                    Author Profile
                  </Dialog.Title>
                  
                  {isLoading ? (
                    <div className="mt-4">Loading author information...</div>
                  ) : author ? (
                    <div className="mt-4 text-left">
                      <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                        <div className="sm:col-span-2">
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Name</dt>
                          <dd className="mt-1 text-sm text-gray-900 dark:text-white">{author.name}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">h-index</dt>
                          <dd className="mt-1 text-sm text-gray-900 dark:text-white">{author.h_index}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Citations</dt>
                          <dd className="mt-1 text-sm text-gray-900 dark:text-white">{author.citations}</dd>
                        </div>
                        <div className="sm:col-span-2">
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Affiliation</dt>
                          <dd className="mt-1 text-sm text-gray-900 dark:text-white">{author.affiliation}</dd>
                        </div>
                        <div className="sm:col-span-2">
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">External Profiles</dt>
                          <dd className="mt-1 space-x-4">
                            <a
                              href={author.profile_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                            >
                              Semantic Scholar
                            </a>
                            <a
                              href={author.linkedin_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                            >
                              LinkedIn
                            </a>
                          </dd>
                        </div>
                      </dl>
                    </div>
                  ) : (
                    <div className="mt-4 text-red-600">Failed to load author information</div>
                  )}
                </div>
              </div>
              <div className="mt-5 sm:mt-6">
                <button
                  type="button"
                  className="inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm"
                  onClick={onClose}
                >
                  Close
                </button>
              </div>
            </div>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

export default AuthorModal; 