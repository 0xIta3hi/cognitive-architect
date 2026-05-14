'use client';

import { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  MiniMap,
  Panel,
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

// Force-directed layout algorithm for better spacing
function forceDirectedLayout(nodes: ApiNode[], edges: ApiEdge[], spacing: number = 400) {
  const positions: { [key: string]: { x: number; y: number } } = {};
  
  // Initialize with circular layout
  nodes.forEach((node, idx) => {
    const angle = (idx / nodes.length) * 2 * Math.PI;
    positions[node.id] = {
      x: Math.cos(angle) * spacing,
      y: Math.sin(angle) * spacing,
    };
  });
  
  return positions;
}

export default function GraphView({ agentId, refreshTrigger }: GraphViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node[]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nodeSpacing, setNodeSpacing] = useState(400);
  const [showMiniMap, setShowMiniMap] = useState(true);

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

        // Get layout positions using force-directed algorithm
        const apiNodes = data.nodes || [];
        const apiEdges = data.edges || [];
        const positions = forceDirectedLayout(apiNodes, apiEdges, nodeSpacing);

        // Transform API nodes to ReactFlow nodes with better styling
        const transformedNodes: Node[] = apiNodes.map((node: ApiNode) => ({
          id: node.id,
          data: {
            label: node.label || node.id,
          },
          position: positions[node.id] || { x: Math.random() * 1200, y: Math.random() * 1200 },
          style: {
            background: '#3b82f6',
            color: '#fff',
            border: '2px solid #1e40af',
            borderRadius: '12px',
            padding: '12px 16px',
            fontSize: '13px',
            fontWeight: 'bold',
            minWidth: '120px',
            textAlign: 'center',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            cursor: 'pointer',
            transition: 'all 0.2s',
          },
        }));

        // Transform API edges to ReactFlow edges
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
  }, [agentId, refreshTrigger, nodeSpacing, setNodes, setEdges]);

  return (
    <div className="flex flex-col h-full bg-slate-800 border-l border-slate-700">
      {/* Header with Controls */}
      <div className="p-4 border-b border-slate-700 z-10 space-y-3">
        <div>
          <h2 className="text-xl font-bold text-white">Memory Graph</h2>
          <p className="text-sm text-slate-400">Agent: {agentId}</p>
          {isLoading && <p className="text-xs text-blue-400 mt-2">Loading graph...</p>}
        </div>

        {/* Graph Size Controls */}
        {nodes.length > 0 && (
          <div className="bg-slate-700 p-3 rounded space-y-2">
            <label className="block text-xs font-semibold text-slate-300">
              Graph Spacing: <span className="text-blue-400">{nodeSpacing}px</span>
            </label>
            <input
              type="range"
              min="200"
              max="1000"
              step="50"
              value={nodeSpacing}
              onChange={(e) => setNodeSpacing(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
              title="Increase spacing to make graph bigger and spread nodes apart"
            />
            <p className="text-xs text-slate-400">
              Move slider right to expand graph and improve visibility
            </p>

            {/* Display Options */}
            <div className="flex items-center gap-3 pt-2 border-t border-slate-600">
              <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showMiniMap}
                  onChange={(e) => setShowMiniMap(e.target.checked)}
                  className="w-4 h-4 accent-blue-500"
                />
                Mini Map
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="m-4 p-3 rounded bg-red-900 border border-red-700 text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Graph Container */}
      <div className="flex-1 relative bg-slate-900">
        {nodes.length === 0 && !isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-slate-400 text-center">
              No memories yet. Add some in the chat!
            </p>
          </div>
        )}

        {nodes.length > 0 && (
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}>
            <Background color="#334155" gap={16} />
            <Controls />
            {showMiniMap && (
              <MiniMap 
                nodeColor="#3b82f6" 
                style={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155'
                }}
              />
            )}
            {/* Instructions Panel */}
            <Panel position="bottom-right" className="bg-slate-700 text-slate-100 p-3 rounded text-xs max-w-xs">
              <p className="font-semibold mb-2">🎮 Controls:</p>
              <ul className="space-y-1 text-slate-300">
                <li>• Drag to pan the graph</li>
                <li>• Scroll to zoom in/out</li>
                <li>• Drag nodes to reposition</li>
                <li>• Use spacing slider for layout</li>
              </ul>
            </Panel>
          </ReactFlow>
        )}
      </div>

      {/* Stats Footer */}
      {nodes.length > 0 && (
        <div className="border-t border-slate-700 p-4 bg-slate-800">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-slate-400 text-xs mb-1">Nodes</p>
              <p className="text-xl font-bold text-blue-400">{nodes.length}</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs mb-1">Edges</p>
              <p className="text-xl font-bold text-blue-400">{edges.length}</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs mb-1">Spacing</p>
              <p className="text-xl font-bold text-green-400">{nodeSpacing}px</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
