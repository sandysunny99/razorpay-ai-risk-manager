import React from 'react';

interface SkeletonProps {
  width?: string;
  height?: string;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '16px',
  className = '',
}) => {
  return (
    <div
      className={`animate-pulse rounded bg-slate-800/60 ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
};

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="w-full space-y-3 p-4 bg-slate-900/50 rounded-xl border border-slate-800">
      <div className="flex gap-4 border-b border-slate-800 pb-3">
        <Skeleton width="20%" height="20px" />
        <Skeleton width="30%" height="20px" />
        <Skeleton width="25%" height="20px" />
        <Skeleton width="25%" height="20px" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 py-2">
          <Skeleton width="20%" height="16px" />
          <Skeleton width="30%" height="16px" />
          <Skeleton width="25%" height="16px" />
          <Skeleton width="25%" height="16px" />
        </div>
      ))}
    </div>
  );
};

export const KPICardSkeleton: React.FC = () => {
  return (
    <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/70 backdrop-blur-md space-y-3">
      <Skeleton width="40%" height="14px" />
      <Skeleton width="60%" height="32px" />
      <Skeleton width="80%" height="12px" />
    </div>
  );
};
