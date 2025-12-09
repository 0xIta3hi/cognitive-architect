'use client';

import { useState } from 'react';

interface AgentCreationFormProps {
  onAgentCreated: (agentId: string) => void;
}

export default function AgentCreationForm({ onAgentCreated }: AgentCreationFormProps) {
  const [agentId, setAgentId] = useState('');
  const [name, setName] = useState('');
  const [agentType, setAgentType] = useState('general');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const agentTypes = [
    { value: 'general', label: 'General Assistant' },
    { value: 'research', label: 'Research Agent' },
    { value: 'developer', label: 'Code Assistant' },
    { value: 'writer', label: 'Content Writer' },
    { value: 'analyst', label: 'Data Analyst' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!agentId.trim() || !name.trim()) {
      setError('Agent ID and name are required');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // The backend expects query parameters, not JSON body
      const params = new URLSearchParams({
        agent_id: agentId.toLowerCase().trim(),
        name: name.trim(),
        agent_type: agentType,
      });

      console.log('Creating agent with params:', Object.fromEntries(params));

      const response = await fetch(`http://localhost:8000/agents?${params.toString()}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Error response:', errorData);
        const errorMessage = 
          typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        throw new Error(errorMessage || `Failed to create agent: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Agent created:', data);

      setSuccess(`✅ Agent "${name}" created successfully!`);
      setAgentId('');
      setName('');
      setAgentType('general');

      // Use the 'id' field from the response (Agent model uses 'id', not 'agent_id')
      const agentIdToReturn = data.id || data.agent_id || agentId.toLowerCase().trim();
      onAgentCreated(agentIdToReturn);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      console.error('Full error object:', err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 rounded-lg border border-slate-700 bg-slate-800">
      <h2 className="text-2xl font-bold text-white mb-4">Create New Agent</h2>

      {error && (
        <div className="mb-4 p-3 rounded bg-red-900 border border-red-700 text-red-200 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 rounded bg-green-900 border border-green-700 text-green-200 text-sm">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Agent ID */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Agent ID <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            placeholder="e.g., my-research-agent"
            disabled={isLoading}
            className="w-full px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          <p className="text-xs text-slate-400 mt-1">
            Lowercase letters, numbers, and hyphens only
          </p>
        </div>

        {/* Agent Name */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Display Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., My Research Assistant"
            disabled={isLoading}
            className="w-full px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          <p className="text-xs text-slate-400 mt-1">
            Human-readable name for the agent
          </p>
        </div>

        {/* Agent Type */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Agent Type
          </label>
          <select
            value={agentType}
            onChange={(e) => setAgentType(e.target.value)}
            disabled={isLoading}
            className="w-full px-4 py-2 rounded bg-slate-700 text-white border border-slate-600 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          >
            {agentTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-slate-400 mt-1">
            Choose the primary role of this agent
          </p>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || !agentId.trim() || !name.trim()}
          className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded font-semibold transition"
        >
          {isLoading ? 'Creating Agent...' : 'Create Agent'}
        </button>
      </form>

      {/* Info Box */}
      <div className="mt-6 p-4 rounded bg-blue-900 border border-blue-700 text-blue-200 text-sm space-y-2">
        <p className="font-semibold">💡 Tip:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Each agent has its own independent memory</li>
          <li>Agents can share memories through explicit grants</li>
          <li>Memories are stored in Neo4j as a knowledge graph</li>
        </ul>
      </div>
    </div>
  );
}
