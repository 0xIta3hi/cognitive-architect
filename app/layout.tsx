import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'MemGraph - AI Agent Memory System',
  description: 'Manage and query AI agent memories with MemGraph',
  keywords: ['AI', 'Memory', 'Agents', 'Neo4j', 'MemGraph'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
