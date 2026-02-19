'use client';

import { Suspense } from 'react';
import HomePage from './HomePageClient';
import ErrorBoundary from '@/components/ErrorBoundary';

export default function Page() {
  return (
    <ErrorBoundary>
      <Suspense fallback={
        <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center">
          <div className="flex items-center gap-3 text-gray-500">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8 animate-spin">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
            <span className="text-lg font-medium">Loading Airport Solar Analyzer...</span>
          </div>
        </div>
      }>
        <HomePage />
      </Suspense>
    </ErrorBoundary>
  );
}
