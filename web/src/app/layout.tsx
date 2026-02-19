import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Airport Solar Analyzer | Rooftop Solar Potential Near US Airports',
  description: 'Analyze rooftop solar opportunities near major US airports using Microsoft Building Footprints and NREL solar data.',
  icons: {
    icon: '/icon.svg',
  },
  openGraph: {
    title: 'Airport Solar Analyzer',
    description: 'Discover solar energy potential near US airports',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `
          try {
            if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
              document.documentElement.classList.add('dark');
            } else {
              document.documentElement.classList.remove('dark');
            }
          } catch (_) {}
        `}} />
      </head>
      <body className={inter.className}>
        <div className="min-h-screen bg-[#f5f5f7] dark:bg-gray-900">
          {children}
        </div>
      </body>
    </html>
  );
}
