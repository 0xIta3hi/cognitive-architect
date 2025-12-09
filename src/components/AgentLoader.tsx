'use client';

import { useState } from 'react';

interface AgentLoaderProps {
  onAgentLoaded: (agentId: string) => void;
}

export default function AgentLoader({ onAgentLoaded }: AgentLoaderProps) {
  const [agentId, setAgentId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoad = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!agentId.trim()) {
      setError('Please enter an agent ID');
      return;
    }

    console.log('📦 Loading agent:', agentId.trim());
    setIsLoading(true);
    setError(null);

    try {
      const url = `http://localhost:8000/agents/${encodeURIComponent(agentId.trim())}`;
      console.log('🔗 Fetching from:', url);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Agent not found: ${agentId}`);
      }

      const data = await response.json();
      console.log('✅ Agent loaded:', data);
      onAgentLoaded(data.agent_id || data.id || agentId.trim());
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load agent';
      setError(errorMsg);
      console.error('❌ Agent load error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 rounded-lg border border-slate-700 bg-slate-800">
      <h2 className="text-2xl font-bold text-white mb-4">Load Existing Agent</h2>

      {error && (
        <div className="mb-4 p-3 rounded bg-red-900 border border-red-700 text-red-200 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleLoad} className="space-y-4">
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Agent ID
          </label>
          <input
            type="text"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            placeholder="e.g., research-agent"
            disabled={isLoading}
            className="w-full px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !agentId.trim()}
          className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded font-semibold transition"
        >
          {isLoading ? 'Loading...' : 'Load Agent'}
        </button>
      </form>
    </div>
  );
}
