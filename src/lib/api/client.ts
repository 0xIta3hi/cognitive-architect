/**
 * API Client Wrapper for MemGraph
 * Auto-generated from OpenAPI spec
 * 
 * This file provides a convenient interface to interact with the MemGraph backend.
 */

import type { paths } from './index';

// Type helpers
type PathItem<T> = T extends `${infer P}?{}` ? P : T;

/**
 * MemGraph API Client Configuration
 */
export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

/**
 * Initialize MemGraph API Client
 * 
 * @param config - Client configuration
 * @returns API client instance
 */
export function createMemGraphClient(config: ApiClientConfig) {
  const baseURL = config.baseURL || 'http://localhost:8000';
  const timeout = config.timeout || 30000;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...config.headers,
  };

  /**
   * Make API request
   */
  async function request<T = any>(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    body?: any,
    options?: { headers?: Record<string, string> }
  ): Promise<T> {
    const url = new URL(endpoint.startsWith('/') ? endpoint : `/${endpoint}`, baseURL);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url.toString(), {
        method,
        headers: {
          ...defaultHeaders,
          ...options?.headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(`API Error [${response.status}]: ${error.detail || response.statusText}`);
      }

      return await response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  return {
    request,
    
    // Health & Info endpoints
    health: () => request('/health', 'GET'),
    root: () => request('/', 'GET'),

    // Agent endpoints
    agents: {
      register: (params: { agent_id: string; name: string; agent_type?: string }) =>
        request('/agents', 'POST', null, { headers: { 'X-Params': JSON.stringify(params) } }),
      get: (agentId: string) => request(`/agents/${agentId}`, 'GET'),
      stats: (agentId: string) => request(`/agents/${agentId}/stats`, 'GET'),
    },

    // Memory endpoints
    memories: {
      add: (params: {
        agent_id: string;
        content: string;
        memory_type?: string;
        importance?: number;
      }) => request('/memories', 'POST', null, { headers: { 'X-Params': JSON.stringify(params) } }),
      get: (memoryId: string) => request(`/memories/${memoryId}`, 'GET'),
      byAgent: (agentId: string, limit?: number) =>
        request(`/memories/agent/${agentId}?limit=${limit || 10}`, 'GET'),
      retrieve: (params: {
        agent_id: string;
        query: string;
        limit?: number;
        min_importance?: number;
      }) => request('/memories/retrieve', 'POST', params),
    },

    // Context endpoints
    contexts: {
      create: (params: { name: string; summary?: string }) =>
        request('/contexts', 'POST', null, { headers: { 'X-Params': JSON.stringify(params) } }),
    },

    // Relationship endpoints
    relationships: {
      create: (params: {
        from_memory_id: string;
        to_memory_id: string;
        relation_type: string;
        strength?: number;
      }) => request('/relationships', 'POST', params),
      relatedMemories: (memoryId: string, maxDepth?: number, minStrength?: number) =>
        request(
          `/relationships/${memoryId}?max_depth=${maxDepth || 2}&min_strength=${minStrength || 0.5}`,
          'GET'
        ),
    },

    // Sharing endpoints
    sharing: {
      grantAccess: (params: {
        from_agent_id: string;
        to_agent_id: string;
        memory_ids: string;
        permission: string;
      }) => request('/sharing/grant', 'POST', params),
      sharedMemories: (agentId: string, limit?: number) =>
        request(`/sharing/${agentId}?limit=${limit || 10}`, 'GET'),
    },
  };
}

export type MemGraphClient = ReturnType<typeof createMemGraphClient>;
