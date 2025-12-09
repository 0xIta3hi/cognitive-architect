import Link from 'next/link';

export default function Navigation() {
  return (
    <nav className="bg-slate-800 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="text-xl font-bold text-white hover:text-blue-400 transition">
            MemGraph
          </Link>
          
          <div className="flex gap-4">
            <Link
              href="/"
              className="px-4 py-2 rounded text-slate-300 hover:text-white hover:bg-slate-700 transition"
            >
              Dashboard
            </Link>
            <Link
              href="/playground"
              className="px-4 py-2 rounded text-slate-300 hover:text-white hover:bg-slate-700 transition"
            >
              Playground
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 rounded text-slate-300 hover:text-white hover:bg-slate-700 transition"
            >
              API Docs
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}
