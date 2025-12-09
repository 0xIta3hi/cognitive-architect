'use client';

import { useState, useEffect } from 'react';
import AgentCreationForm from '@/components/AgentCreationForm';
import AgentLoader from '@/components/AgentLoader';
import AgentDetails from '@/components/AgentDetails';
import { checkHealth, fetchAgentMemories, addMemory } from '@/lib/memgraph';

const MEMORY_TYPES = [
  { value: 'fact', label: 'Fact' },
  { value: 'conversation', label: 'Conversation' },
  { value: 'experience', label: 'Experience' },
  { value: 'goal', label: 'Goal' },
  { value: 'interaction', label: 'Interaction' },
];

export default function DashboardPage() {
  const [backendStatus, setBackendStatus] = useState<'loading' | 'healthy' | 'error'>('loading');
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [memories, setMemories] = useState<any[]>([]);
  const [newMemoryContent, setNewMemoryContent] = useState('');
  const [memoryType, setMemoryType] = useState('fact');
  const [importance, setImportance] = useState(0.7);
  const [isAddingMemory, setIsAddingMemory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check backend health on mount
  useEffect(() => {
    console.log('🎯 Dashboard page mounted');
    const checkBackend = async () => {
      try {
        const health = await checkHealth();
        console.log('🏥 Backend health check:', health);
        setBackendStatus(health.healthy ? 'healthy' : 'error');
        if (!health.healthy) {
          setError('Backend is not available');
        }
      } catch (err) {
        setBackendStatus('error');
        setError(
          err instanceof Error ? err.message : 'Failed to connect to backend'
        );
        console.error('❌ Health check error:', err);
      }
    };

    checkBackend();
  }, []);

  // Load memories when agent is selected
  useEffect(() => {
    if (!selectedAgentId) {
      setMemories([]);
      return;
    }

    console.log('🔄 Loading memories for agent:', selectedAgentId);

    const loadMemories = async () => {
      try {
        setError(null);
        console.log('📡 Fetching memories...');
        const { data, error: fetchError } = await fetchAgentMemories(
          selectedAgentId,
          50
        );
        if (fetchError) {
          console.error('❌ Fetch error:', fetchError);
          setError(fetchError);
          setMemories([]);
        } else {
          console.log('✅ Loaded memories:', data);
          setMemories(data || []);
        }
      } catch (err) {
        console.error('❌ Load error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load memories');
        setMemories([]);
      }
    };

    loadMemories();
  }, [selectedAgentId]);

  const handleAddMemory = async () => {
    if (!newMemoryContent.trim() || !selectedAgentId) return;

    setIsAddingMemory(true);
    setError(null);

    try {
      const { error: addError } = await addMemory(
        selectedAgentId,
        newMemoryContent,
        memoryType,
        importance
      );

      if (addError) {
        setError(addError);
      } else {
        setNewMemoryContent('');
        setMemoryType('fact');
        setImportance(0.7);

        // Reload memories
        const { data: newMemories, error: fetchError } = await fetchAgentMemories(
          selectedAgentId,
          50
        );
        if (!fetchError) {
          setMemories(newMemories || []);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add memory');
    } finally {
      setIsAddingMemory(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      <div className="max-w-7xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-slate-300">
            Create agents, manage memories, and organize your AI knowledge graph
          </p>
        </div>

        {/* Backend Status */}
        <div className="mb-8 p-4 rounded-lg border border-slate-700 bg-slate-800">
          <div className="flex items-center gap-3">
            <div
              className={`w-3 h-3 rounded-full ${
                backendStatus === 'healthy'
                  ? 'bg-green-500'
                  : backendStatus === 'error'
                  ? 'bg-red-500'
                  : 'bg-yellow-500'
              }`}
            />
            <span className="text-lg font-semibold text-white">
              Backend Status:{' '}
              {backendStatus === 'healthy'
                ? '✓ Connected'
                : backendStatus === 'error'
                ? '✗ Disconnected'
                : '⟳ Connecting...'}
            </span>
          </div>
          {error && backendStatus === 'error' && (
            <p className="text-red-400 mt-2 text-sm">{error}</p>
          )}
        </div>

        {backendStatus !== 'healthy' && (
          <div className="mb-8 p-4 rounded-lg bg-red-900 border border-red-700 text-red-100">
            <p className="font-semibold">⚠️ Backend Not Available</p>
            <p className="text-sm mt-2">
              Make sure the FastAPI server is running:
            </p>
            <code className="block bg-slate-900 p-2 rounded mt-2 text-sm">
              python -m uvicorn memgraph.api.main:app --reload
            </code>
          </div>
        )}

        {/* Main Content - Three Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Agent Management */}
          <div className="space-y-6">
            <AgentCreationForm onAgentCreated={(id) => setSelectedAgentId(id)} />
            <AgentLoader onAgentLoaded={(id) => setSelectedAgentId(id)} />
          </div>

          {/* Middle Column - Agent Details */}
          <div>
            <AgentDetails
              agentId={selectedAgentId}
              onAgentChange={setSelectedAgentId}
            />
          </div>

          {/* Right Column - Memory Management */}
          <div className="space-y-6">
            {/* Add Memory Form */}
            {selectedAgentId && (
              <div className="p-6 rounded-lg border border-slate-700 bg-slate-800">
                <h2 className="text-2xl font-bold text-white mb-4">
                  Add Memory
                </h2>

                {error && (
                  <div className="mb-4 p-3 rounded bg-red-900 border border-red-700 text-red-200 text-sm">
                    {error}
                  </div>
                )}

                <div className="space-y-4">
                  {/* Memory Content */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">
                      Memory Content
                    </label>
                    <textarea
                      value={newMemoryContent}
                      onChange={(e) => setNewMemoryContent(e.target.value)}
                      placeholder="Enter a fact, experience, or observation..."
                      rows={4}
                      disabled={isAddingMemory}
                      className="w-full px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-blue-500 disabled:opacity-50 resize-none"
                    />
                  </div>

                  {/* Memory Type */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">
                      Type
                    </label>
                    <select
                      value={memoryType}
                      onChange={(e) => setMemoryType(e.target.value)}
                      disabled={isAddingMemory}
                      className="w-full px-4 py-2 rounded bg-slate-700 text-white border border-slate-600 focus:outline-none focus:border-blue-500 disabled:opacity-50"
                    >
                      {MEMORY_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Importance Slider */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">
                      Importance:{' '}
                      <span className="text-blue-400">
                        {(importance * 100).toFixed(0)}%
                      </span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={importance}
                      onChange={(e) => setImportance(parseFloat(e.target.value))}
                      disabled={isAddingMemory}
                      className="w-full disabled:opacity-50"
                    />
                    <p className="text-xs text-slate-400 mt-1">
                      How important is this memory?
                    </p>
                  </div>

                  {/* Submit Button */}
                  <button
                    onClick={handleAddMemory}
                    disabled={
                      isAddingMemory || !newMemoryContent.trim()
                    }
                    className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded font-semibold transition"
                  >
                    {isAddingMemory ? 'Adding Memory...' : 'Add Memory'}
                  </button>
                </div>
              </div>
            )}

            {!selectedAgentId && (
              <div className="p-6 rounded-lg border border-slate-700 bg-slate-800 border-dashed">
                <p className="text-slate-400 text-center">
                  Select or create an agent to add memories
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Memories Section */}
        {selectedAgentId && (
          <div className="mt-12">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">
                Memories ({memories.length})
              </h2>
              <p className="text-slate-400">
                All memories stored for {selectedAgentId}
              </p>
            </div>

            {memories.length === 0 ? (
              <div className="p-8 rounded-lg border border-dashed border-slate-600 bg-slate-800 text-center">
                <p className="text-slate-400">
                  No memories yet. Add one using the form above!
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {memories.map((memory, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-lg border border-slate-700 bg-slate-800 hover:border-slate-600 transition"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-sm font-semibold text-white flex-1 pr-2 line-clamp-2">
                        {memory.content}
                      </h3>
                      <span className="px-2 py-1 text-xs font-semibold rounded bg-blue-600 text-white whitespace-nowrap">
                        {memory.memory_type}
                      </span>
                    </div>

                    {/* Importance Bar */}
                    <div className="mb-3">
                      <div className="w-full bg-slate-700 rounded-full h-1.5">
                        <div
                          className="bg-yellow-500 h-1.5 rounded-full transition-all"
                          style={{
                            width: `${
                              Math.min(memory.importance * 100, 100)
                            }%`,
                          }}
                        />
                      </div>
                      <p className="text-xs text-slate-400 mt-1">
                        Importance: {(memory.importance * 100).toFixed(0)}%
                      </p>
                    </div>

                    {/* Metadata */}
                    <div className="text-xs text-slate-500 space-y-1">
                      {memory.memory_id && (
                        <p>ID: {memory.memory_id.substring(0, 8)}...</p>
                      )}
                      {memory.created_at && (
                        <p>
                          Created:{' '}
                          {new Date(memory.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
