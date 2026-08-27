import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalItems,
  pageSize,
  onPageChange,
}) => {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-slate-900/60 border-t border-slate-800 text-xs text-slate-400">
      <div>
        Showing{' '}
        <span className="font-semibold text-slate-200">
          {totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1}
        </span>{' '}
        to{' '}
        <span className="font-semibold text-slate-200">
          {Math.min(currentPage * pageSize, totalItems)}
        </span>{' '}
        of <span className="font-semibold text-slate-200">{totalItems}</span> events
      </div>
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 transition"
        >
          Previous
        </button>
        <span className="px-2 py-1 font-mono text-slate-300">
          {currentPage} / {totalPages}
        </span>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 transition"
        >
          Next
        </button>
      </div>
    </div>
  );
};
