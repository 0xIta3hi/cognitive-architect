/**
 * MemGraph API Client Configuration for Next.js
 * 
 * This file initializes and exports the MemGraph API client instance
 * for use throughout your Next.js application.
 * 
 * Usage in components:
 *   import { api } from '@/lib/memgraph';
 *   const agent = await api.agents.get('agent-id');
 */

/**
 * Base URL for the MemGraph backend
 * - Production: from environment variable
 * - Development: localhost:8000
 */
const getBaseURL = () => {
  if (typeof window === 'undefined') {
    // Server-side (Next.js API routes, getServerSideProps, etc.)
    return (
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.MEMGRAPH_API_URL ||
      'http://localhost:8000'
    );
  }
  // Client-side
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000'
  );
};

// Import the generated client
import { createMemGraphClient } from './api/client';
import type { MemGraphClient } from './api/client';

/**
 * Initialize the API client with configuration
 */
const api: MemGraphClient = createMemGraphClient({
  baseURL: getBaseURL(),
  timeout: 30000,
  headers: {
    'User-Agent': 'MemGraph-Next.js-Client/1.0.0',
  },
});

export { api };
export type { MemGraphClient } from './api/client';

/**
 * Helper hook for React components (if using React Query or SWR)
 * 
 * Example usage with SWR:
 *   const { data, error, isLoading } = useSWR(
 *     ['agent', agentId],
 *     () => api.agents.get(agentId),
 *     { revalidateOnFocus: false }
 *   );
 */
export function useMemGraphAPI() {
  return api;
}

/**
 * Helper function to fetch agent with error handling
 */
export async function fetchAgent(agentId: string) {
  try {
    const agent = await api.agents.get(agentId);
    return { data: agent, error: null };
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : 'Failed to fetch agent',
    };
  }
}

/**
 * Helper function to fetch agent memories
 */
export async function fetchAgentMemories(agentId: string, limit = 10) {
  try {
    const params = new URLSearchParams({
      limit: String(limit),
    });

    const response = await fetch(
      `http://localhost:8000/memories/agent/${encodeURIComponent(agentId)}?${params.toString()}`,
      { method: 'GET' }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(
        typeof errorData.detail === 'string'
          ? errorData.detail
          : JSON.stringify(errorData.detail)
      );
    }

    const memories = await response.json();
    return { data: memories, error: null };
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : 'Failed to fetch memories',
    };
  }
}

/**
 * Helper function to retrieve context
 */
export async function retrieveContext(
  agentId: string,
  query: string,
  limit = 5,
  minImportance = 0.5
) {
  try {
    const params = new URLSearchParams({
      agent_id: agentId,
      query: query,
      limit: String(limit),
      min_importance: String(minImportance),
    });

    const response = await fetch(`http://localhost:8000/memories/retrieve?${params.toString()}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(
        typeof errorData.detail === 'string'
          ? errorData.detail
          : JSON.stringify(errorData.detail)
      );
    }

    const context = await response.json();
    return { data: context, error: null };
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : 'Failed to retrieve context',
    };
  }
}

/**
 * Helper function to add a memory
 */
export async function addMemory(
  agentId: string,
  content: string,
  memoryType = 'fact',
  importance = 0.7
) {
  try {
    // Use query parameters instead of JSON body
    const params = new URLSearchParams({
      agent_id: agentId,
      content: content,
      memory_type: memoryType,
      importance: String(importance),
    });

    const response = await fetch(`http://localhost:8000/memories?${params.toString()}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(
        typeof errorData.detail === 'string'
          ? errorData.detail
          : JSON.stringify(errorData.detail)
      );
    }

    const memory = await response.json();
    return { data: memory, error: null };
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : 'Failed to add memory',
    };
  }
}

/**
 * Health check function
 * Useful for detecting if backend is available
 */
export async function checkHealth() {
  try {
    const result = await api.health();
    return { healthy: true, data: result, error: null };
  } catch (error) {
    return {
      healthy: false,
      data: null,
      error: error instanceof Error ? error.message : 'Backend unavailable',
    };
  }
}
