'use client';

import { useState } from 'react';
import ChatInterface from '@/components/ChatInterface';
import GraphView from '@/components/GraphView';
import Navigation from '@/components/Navigation';

export default function PlaygroundPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [agentId, setAgentId] = useState('test-agent');

  const handleMessageSent = () => {
    // Increment refreshKey to trigger graph refresh in GraphView
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      <Navigation />
      
      {/* Header */}
      <div className="p-4 border-b border-slate-700 bg-slate-800">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">MemGraph Playground</h1>
            <p className="text-sm text-slate-400">Interactive chat and memory visualization</p>
          </div>
          <div className="flex gap-4 items-center">
            <label className="text-sm text-slate-300 flex items-center gap-2">
              Agent ID:
              <input
                type="text"
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
                placeholder="test-agent"
                className="px-3 py-1 rounded bg-slate-700 text-white text-sm border border-slate-600 focus:outline-none focus:border-blue-500"
              />
            </label>
          </div>
        </div>
      </div>

      {/* Main Content - Split Screen */}
      <div className="flex flex-1 min-h-0">
        {/* Chat Section - 50% */}
        <div className="w-1/2 flex flex-col min-w-0">
          <ChatInterface
            agentId={agentId}
            onMessageSent={handleMessageSent}
          />
        </div>

        {/* Graph Section - 50% */}
        <div className="w-1/2 flex flex-col min-w-0">
          <GraphView
            agentId={agentId}
            refreshTrigger={refreshKey}
          />
        </div>
      </div>
    </div>
  );
}
