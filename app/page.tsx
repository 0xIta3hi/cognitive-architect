'use client';

import { useState, useEffect } from 'react';
import { checkHealth, fetchAgent, addMemory, fetchAgentMemories } from '@/lib/memgraph';

export default function Home() {
  const [status, setStatus] = useState<'loading' | 'healthy' | 'error'>('loading');
  const [agent, setAgent] = useState<any>(null);
  const [memories, setMemories] = useState<any[]>([]);
  const [newMemory, setNewMemory] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [agentId, setAgentId] = useState('research-agent');

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const health = await checkHealth();
        if (health.healthy) {
          setStatus('healthy');
          // Load initial agent
          loadAgent('research-agent');
        } else {
          setStatus('error');
          setError('Backend is not available');
        }
      } catch (err) {
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Failed to connect to backend');
      }
    };

    checkBackend();
  }, []);

  const loadAgent = async (id: string) => {
    try {
      setError(null);
      const { data, error: fetchError } = await fetchAgent(id);
      if (fetchError) {
        setError(fetchError);
        setAgent(null);
      } else {
        setAgent(data);
        // Also load memories for this agent
        const { data: mems, error: memsError } = await fetchAgentMemories(id);
        if (!memsError) {
          setMemories(mems || []);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agent');
    }
  };

  const handleLoadAgent = () => {
    if (agentId.trim()) {
      loadAgent(agentId);
    }
  };

  const handleCreateAgent = async () => {
    if (!agentId.trim()) return;

    try {
      setError(null);
      // Call POST /agents endpoint to register a new agent
      const response = await fetch('http://localhost:8000/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          name: agentId.replace('-', ' ').toUpperCase(),
          agent_type: 'general',
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create agent: ${response.statusText}`);
      }

      // Load the newly created agent
      await loadAgent(agentId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
    }
  };

  const handleAddMemory = async () => {
    if (!newMemory.trim() || !agent) return;

    try {
      setError(null);
      const { data, error: addError } = await addMemory(
        agent.agent_id,
        newMemory,
        'fact',
        0.8
      );

      if (addError) {
        setError(addError);
      } else {
        setNewMemory('');
        // Reload memories
        loadAgent(agent.agent_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add memory');
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">MemGraph Dashboard</h1>
          <p className="text-slate-300">AI Agent Memory Management System</p>
        </div>

        {/* Status Card */}
        <div className="mb-8 p-6 rounded-lg border border-slate-700 bg-slate-800">
          <div className="flex items-center gap-3 mb-2">
            <div
              className={`w-3 h-3 rounded-full ${
                status === 'healthy'
                  ? 'bg-green-500'
                  : status === 'error'
                  ? 'bg-red-500'
                  : 'bg-yellow-500'
              }`}
            />
            <span className="text-lg font-semibold text-white">
              Backend Status: {status === 'healthy' ? '✓ Connected' : status === 'error' ? '✗ Disconnected' : '⟳ Connecting...'}
            </span>
          </div>
          {error && <p className="text-red-400 mt-2">{error}</p>}
        </div>

        {status === 'healthy' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Agent Loader */}
            <div className="p-6 rounded-lg border border-slate-700 bg-slate-800">
              <h2 className="text-2xl font-bold text-white mb-4">Load or Create Agent</h2>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  placeholder="Enter agent ID (e.g., research-agent)"
                  className="flex-1 px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleLoadAgent}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold transition"
                >
                  Load
                </button>
                <button
                  onClick={handleCreateAgent}
                  className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-semibold transition"
                >
                  Create
                </button>
              </div>

              {agent && (
                <div className="mt-4 p-4 rounded bg-slate-700 border border-slate-600">
                  <h3 className="text-xl font-semibold text-white mb-2">{agent.name}</h3>
                  <div className="space-y-1 text-sm text-slate-300">
                    <p>
                      <span className="text-slate-400">ID:</span> {agent.agent_id}
                    </p>
                    <p>
                      <span className="text-slate-400">Type:</span> {agent.agent_type}
                    </p>
                    <p>
                      <span className="text-slate-400">Created:</span> {new Date(agent.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Add Memory */}
            {agent && (
              <div className="p-6 rounded-lg border border-slate-700 bg-slate-800">
                <h2 className="text-2xl font-bold text-white mb-4">Add Memory</h2>
                <textarea
                  value={newMemory}
                  onChange={(e) => setNewMemory(e.target.value)}
                  placeholder="Enter a new memory or fact..."
                  rows={4}
                  className="w-full px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-blue-500 resize-none"
                />
                <button
                  onClick={handleAddMemory}
                  disabled={!newMemory.trim()}
                  className="mt-4 w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded font-semibold transition"
                >
                  Save Memory
                </button>
              </div>
            )}
          </div>
        )}

        {/* Memories List */}
        {status === 'healthy' && agent && memories.length > 0 && (
          <div className="mt-8 p-6 rounded-lg border border-slate-700 bg-slate-800">
            <h2 className="text-2xl font-bold text-white mb-4">
              Memories ({memories.length})
            </h2>
            <div className="space-y-3">
              {memories.map((memory, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded bg-slate-700 border border-slate-600 hover:border-slate-500 transition"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-semibold text-white">{memory.content}</h3>
                    <span className="px-2 py-1 text-xs font-semibold rounded bg-blue-600 text-white">
                      {memory.memory_type}
                    </span>
                  </div>
                  <div className="flex gap-4 text-sm text-slate-400">
                    <span>Importance: {(memory.importance * 100).toFixed(0)}%</span>
                    <span>{new Date(memory.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {status === 'healthy' && agent && memories.length === 0 && (
          <div className="mt-8 p-6 rounded-lg border border-dashed border-slate-600 bg-slate-900 text-center">
            <p className="text-slate-400">No memories found for this agent. Add one above!</p>
          </div>
        )}

        {/* Documentation */}
        <div className="mt-12 p-6 rounded-lg border border-slate-700 bg-slate-800">
          <h2 className="text-2xl font-bold text-white mb-4">Quick Start</h2>
          <div className="space-y-3 text-slate-300 text-sm">
            <p>
              <span className="text-slate-400 font-semibold">1. Register an Agent:</span> Create a new agent
              using the MemGraph API
            </p>
            <p>
              <span className="text-slate-400 font-semibold">2. Add Memories:</span> Store facts, context, and
              relationships
            </p>
            <p>
              <span className="text-slate-400 font-semibold">3. Retrieve Context:</span> Query memories for
              relevant information
            </p>
            <p className="mt-4">
              📚 Check <code className="bg-slate-900 px-2 py-1 rounded">src/lib/memgraph.ts</code> for more
              API methods
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
