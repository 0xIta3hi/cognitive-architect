'use client';

import { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

interface GraphViewProps {
  agentId: string;
  refreshTrigger: number;
}

interface ApiNode {
  id: string;
  label: string;
  type?: string;
}

interface ApiEdge {
  source: string;
  target: string;
  type?: string;
  strength?: number;
}

export default function GraphView({ agentId, refreshTrigger }: GraphViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node[]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch graph data when refreshTrigger changes
  useEffect(() => {
    const fetchGraph = async () => {
      console.log('📊 Fetching graph for agent:', agentId);
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `http://localhost:8000/memories/graph?agent_id=${encodeURIComponent(agentId)}`
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          console.error('❌ Server error response:', errorData);
          throw new Error(`Failed to fetch graph: ${errorData.detail || response.statusText}`);
        }

        const data = await response.json();
        console.log('✅ Graph data received:', data);

        // Transform API nodes to ReactFlow nodes
        const apiNodes = data.nodes || [];
        const transformedNodes: Node[] = apiNodes.map((node: ApiNode, idx: number) => ({
          id: node.id,
          data: {
            label: node.label || node.id,
          },
          position: {
            x: Math.random() * 500,
            y: Math.random() * 500,
          },
          style: {
            background: '#3b82f6',
            color: '#fff',
            border: '1px solid #1e40af',
            borderRadius: '8px',
            padding: '10px',
            fontSize: '12px',
            fontWeight: 'bold',
            minWidth: '100px',
            textAlign: 'center',
          },
        }));

        // Transform API edges to ReactFlow edges
        const apiEdges = data.edges || [];
        const transformedEdges: Edge[] = apiEdges.map((edge: ApiEdge) => ({
          id: `${edge.source}-${edge.target}`,
          source: edge.source,
          target: edge.target,
          label: edge.type || '',
          animated: true,
          style: {
            stroke: `rgba(100, 116, 139, ${(edge.strength || 0.5) * 0.8 + 0.2})`,
            strokeWidth: (edge.strength || 0.5) * 3,
          },
        }));

        console.log('📍 Transformed nodes:', transformedNodes);
        console.log('🔗 Transformed edges:', transformedEdges);

        setNodes(transformedNodes);
        setEdges(transformedEdges);
      } catch (err) {
        console.error('❌ Graph fetch error:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch graph');
      } finally {
        setIsLoading(false);
      }
    };

    fetchGraph();
  }, [agentId, refreshTrigger, setNodes, setEdges]);

  return (
    <div className="flex flex-col h-full bg-slate-800 border-l border-slate-700">
      {/* Header */}
      <div className="p-4 border-b border-slate-700 z-10">
        <h2 className="text-xl font-bold text-white">Memory Graph</h2>
        <p className="text-sm text-slate-400">Agent: {agentId}</p>
        {isLoading && <p className="text-xs text-blue-400 mt-2">Loading graph...</p>}
      </div>

      {/* Error Message */}
      {error && (
        <div className="m-4 p-3 rounded bg-red-900 border border-red-700 text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Graph Container */}
      <div className="flex-1 relative">
        {nodes.length === 0 && !isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-slate-400 text-center">
              No memories yet. Add some in the chat!
            </p>
          </div>
        )}

        {nodes.length > 0 && (
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}>
            <Background />
            <Controls />
          </ReactFlow>
        )}
      </div>

      {/* Stats Footer */}
      {nodes.length > 0 && (
        <div className="border-t border-slate-700 p-4 text-sm text-slate-300 space-y-1">
          <p>Nodes: <span className="font-semibold text-blue-400">{nodes.length}</span></p>
          <p>Edges: <span className="font-semibold text-blue-400">{edges.length}</span></p>
        </div>
      )}
    </div>
  );
}
