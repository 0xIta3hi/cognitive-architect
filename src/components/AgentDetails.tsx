'use client';

import { useState, useEffect } from 'react';

interface AgentStats {
  agent_id: string;
  total_memories: number;
  memory_types: Record<string, number>;
  total_relationships: number;
  average_importance: number;
}

interface AgentDetailsProps {
  agentId: string | null;
  onAgentChange: (agentId: string | null) => void;
}

export default function AgentDetails({ agentId, onAgentChange }: AgentDetailsProps) {
  const [stats, setStats] = useState<AgentStats | null>(null);
  const [agent, setAgent] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) {
      setStats(null);
      setAgent(null);
      return;
    }

    const fetchAgentDetails = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch agent details
        const agentResponse = await fetch(
          `http://localhost:8000/agents/${encodeURIComponent(agentId)}`
        );

        if (!agentResponse.ok) {
          throw new Error('Failed to fetch agent details');
        }

        const agentData = await agentResponse.json();
        setAgent(agentData);

        // Fetch agent stats
        try {
          const statsResponse = await fetch(
            `http://localhost:8000/agents/${encodeURIComponent(agentId)}/stats`
          );

          if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            setStats(statsData);
          }
        } catch (err) {
          console.error('Failed to fetch stats:', err);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load agent');
        onAgentChange(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgentDetails();
  }, [agentId, onAgentChange]);

  if (!agentId) {
    return (
      <div className="p-6 rounded-lg border border-slate-700 bg-slate-800 border-dashed">
        <p className="text-slate-400 text-center">
          Create a new agent or load an existing one to see details
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-6 rounded-lg border border-slate-700 bg-slate-800">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-700 rounded w-3/4"></div>
          <div className="h-4 bg-slate-700 rounded"></div>
          <div className="h-4 bg-slate-700 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-lg border border-slate-700 bg-slate-800">
        <div className="p-4 rounded bg-red-900 border border-red-700 text-red-200 text-sm">
          {error}
        </div>
        <button
          onClick={() => onAgentChange(null)}
          className="mt-4 w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded transition"
        >
          Clear Selection
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-lg border border-slate-700 bg-slate-800 space-y-4">
      {/* Header with close button */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-white">{agent?.name}</h2>
          <p className="text-sm text-slate-400">ID: {agent?.agent_id}</p>
        </div>
        <button
          onClick={() => onAgentChange(null)}
          className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 text-white rounded transition"
        >
          Change
        </button>
      </div>

      {/* Agent Info */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-slate-400">Type:</span>
          <span className="text-white font-semibold">
            {agent?.agent_type || 'General'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Created:</span>
          <span className="text-white font-semibold">
            {agent?.created_at
              ? new Date(agent.created_at).toLocaleDateString()
              : 'N/A'}
          </span>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-slate-700"></div>

      {/* Statistics */}
      {stats && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-white">Memory Statistics</h3>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded bg-slate-700">
              <p className="text-slate-400 text-xs">Total Memories</p>
              <p className="text-2xl font-bold text-blue-400">
                {stats.total_memories}
              </p>
            </div>

            <div className="p-3 rounded bg-slate-700">
              <p className="text-slate-400 text-xs">Relationships</p>
              <p className="text-2xl font-bold text-green-400">
                {stats.total_relationships}
              </p>
            </div>
          </div>

          {/* Memory Types Breakdown */}
          {Object.keys(stats.memory_types).length > 0 && (
            <div className="p-3 rounded bg-slate-700">
              <p className="text-slate-400 text-xs mb-2">Memory Types</p>
              <div className="space-y-1 text-sm">
                {Object.entries(stats.memory_types).map(([type, count]) => (
                  <div key={type} className="flex justify-between">
                    <span className="text-slate-300 capitalize">{type}:</span>
                    <span className="text-blue-400 font-semibold">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Average Importance */}
          <div className="p-3 rounded bg-slate-700">
            <p className="text-slate-400 text-xs mb-2">Avg. Importance</p>
            <div className="w-full bg-slate-600 rounded-full h-2">
              <div
                className="bg-yellow-500 h-2 rounded-full transition-all"
                style={{
                  width: `${Math.min(stats.average_importance * 100, 100)}%`,
                }}
              ></div>
            </div>
            <p className="text-sm text-blue-400 font-semibold mt-2">
              {(stats.average_importance * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
