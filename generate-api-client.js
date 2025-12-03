#!/usr/bin/env node

/**
 * Script to fetch OpenAPI spec from FastAPI backend and generate TypeScript SDK
 * 
 * Usage:
 *   node generate-api-client.js [--backend-url http://localhost:8000]
 * 
 * Prerequisites:
 *   npm install --save-dev @openapitools/openapi-generator-cli
 *   or use: npx @openapitools/openapi-generator-cli
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const { execSync } = require('child_process');

// Configuration
const BACKEND_URL = process.argv[2] || process.env.BACKEND_URL || 'http://localhost:8000';
const OPENAPI_ENDPOINT = `${BACKEND_URL}/openapi.json`;
const OUTPUT_DIR = path.join(__dirname, 'src/lib/api');
const OPENAPI_FILE = path.join(__dirname, 'openapi.json');

console.log('🔧 MemGraph TypeScript SDK Generator');
console.log('====================================\n');

// Step 1: Fetch OpenAPI spec
console.log(`📡 Fetching OpenAPI spec from: ${OPENAPI_ENDPOINT}`);

const fetchOpenAPI = () => {
  return new Promise((resolve, reject) => {
    const protocol = OPENAPI_ENDPOINT.startsWith('https') ? https : http;
    
    const request = protocol.get(OPENAPI_ENDPOINT, { timeout: 5000 }, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const spec = JSON.parse(data);
            fs.writeFileSync(OPENAPI_FILE, JSON.stringify(spec, null, 2));
            console.log(`✅ OpenAPI spec saved to: ${OPENAPI_FILE}`);
            resolve();
          } catch (err) {
            reject(new Error(`Failed to parse OpenAPI JSON: ${err.message}`));
          }
        } else {
          reject(new Error(`Failed to fetch OpenAPI spec. Status: ${res.statusCode}`));
        }
      });
    });
    
    request.on('error', (err) => {
      reject(new Error(
        `Cannot connect to ${OPENAPI_ENDPOINT}. ` +
        `Make sure FastAPI backend is running:\n` +
        `  python -m uvicorn memgraph.api.main:app --reload\n\n` +
        `Details: ${err.message}`
      ));
    });
    
    request.on('timeout', () => {
      request.destroy();
      reject(new Error(
        `Connection timeout. Backend not responding at ${OPENAPI_ENDPOINT}\n` +
        `Make sure FastAPI is running first.`
      ));
    });
  });
};

// Step 2: Check if openapi-typescript is installed, if not try openapi-generator-cli
const generateTypeScript = () => {
  console.log(`\n🛠️  Generating TypeScript client...`);
  
  try {
    // Try using openapi-typescript (simpler, faster)
    console.log(`   Attempting with openapi-typescript...`);
    execSync(`npx openapi-typescript ${OPENAPI_FILE} -o ${OUTPUT_DIR}/index.ts`, {
      stdio: 'inherit'
    });
    console.log(`✅ TypeScript client generated at: ${OUTPUT_DIR}/index.ts`);
  } catch (err) {
    console.log(`   openapi-typescript not found, trying openapi-generator-cli...`);
    try {
      // Fallback to openapi-generator-cli
      execSync(
        `npx @openapitools/openapi-generator-cli generate ` +
        `-i ${OPENAPI_FILE} ` +
        `-g typescript-fetch ` +
        `-o ${OUTPUT_DIR} ` +
        `--additional-properties=npmName=memgraph-api,npmVersion=1.0.0`,
        { stdio: 'inherit' }
      );
      console.log(`✅ TypeScript client generated at: ${OUTPUT_DIR}`);
    } catch (err2) {
      throw new Error(
        'Failed to generate TypeScript client. ' +
        'Install one of:\n' +
        '  npm install --save-dev openapi-typescript\n' +
        '  npm install --save-dev @openapitools/openapi-generator-cli\n' +
        `Error: ${err2.message}`
      );
    }
  }
};

// Step 3: Generate API client wrapper (if using openapi-typescript)
const generateClientWrapper = () => {
  console.log(`\n📦 Creating API client wrapper...`);
  
  const wrapperCode = `/**
 * API Client Wrapper for MemGraph
 * Auto-generated from OpenAPI spec
 * 
 * This file provides a convenient interface to interact with the MemGraph backend.
 */

import type { paths } from './index';

// Type helpers
type PathItem<T> = T extends \`\${infer P}?{}\` ? P : T;

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
    const url = new URL(endpoint.startsWith('/') ? endpoint : \`/\${endpoint}\`, baseURL);
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
        throw new Error(\`API Error [\${response.status}]: \${error.detail || response.statusText}\`);
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
      get: (agentId: string) => request(\`/agents/\${agentId}\`, 'GET'),
      stats: (agentId: string) => request(\`/agents/\${agentId}/stats\`, 'GET'),
    },

    // Memory endpoints
    memories: {
      add: (params: {
        agent_id: string;
        content: string;
        memory_type?: string;
        importance?: number;
      }) => request('/memories', 'POST', null, { headers: { 'X-Params': JSON.stringify(params) } }),
      get: (memoryId: string) => request(\`/memories/\${memoryId}\`, 'GET'),
      byAgent: (agentId: string, limit?: number) =>
        request(\`/memories/agent/\${agentId}?limit=\${limit || 10}\`, 'GET'),
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
          \`/relationships/\${memoryId}?max_depth=\${maxDepth || 2}&min_strength=\${minStrength || 0.5}\`,
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
        request(\`/sharing/\${agentId}?limit=\${limit || 10}\`, 'GET'),
    },
  };
}

export type MemGraphClient = ReturnType<typeof createMemGraphClient>;
`;

  const wrapperPath = path.join(OUTPUT_DIR, 'client.ts');
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.writeFileSync(wrapperPath, wrapperCode);
  console.log(`✅ Client wrapper created at: ${wrapperPath}`);
};

// Main execution
(async () => {
  try {
    await fetchOpenAPI();
    generateTypeScript();
    generateClientWrapper();

    console.log(`\n✨ SDK Generation Complete!`);
    console.log(`\n📍 Generated files:`);
    console.log(`   - ${OUTPUT_DIR}/index.ts (OpenAPI types)`);
    console.log(`   - ${OUTPUT_DIR}/client.ts (Client wrapper)`);
    console.log(`\n📚 Next steps:`);
    console.log(`   1. Create src/lib/memgraph.ts with the client instance`);
    console.log(`   2. Use in your Next.js components:\n`);
    console.log(`      import { api } from '@/lib/memgraph';\n`);
    console.log(`      const response = await api.agents.get('agent-id');\n`);
    console.log(`   3. Ensure FastAPI backend is running at ${BACKEND_URL}`);
  } catch (error) {
    console.error(`\n❌ Error: ${error.message}`);
    console.error(`\n📋 Setup Instructions:\n`);
    console.error(`1. Start Neo4j (if not running):`);
    console.error(`   docker run --rm -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/password neo4j\n`);
    console.error(`2. Start FastAPI backend in a new terminal:`);
    console.error(`   python -m uvicorn memgraph.api.main:app --reload\n`);
    console.error(`3. Once backend is running, try again:`);
    console.error(`   node generate-api-client.js\n`);
    process.exit(1);
  }
})();
