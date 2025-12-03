/**
 * Initialize test agents in MemGraph backend
 * 
 * Run this script to create sample agents that the frontend can use
 * Usage: node init-agents.js
 */

const http = require('http');

const BACKEND_URL = 'http://localhost:8000';

async function makeRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BACKEND_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ status: res.statusCode, data: parsed });
        } catch {
          resolve({ status: res.statusCode, data: data });
        }
      });
    });

    req.on('error', reject);

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

async function initAgents() {
  console.log('🚀 Initializing MemGraph Test Agents...\n');

  const agents = [
    {
      agent_id: 'research-agent',
      name: 'Research Assistant',
      agent_type: 'researcher',
    },
    {
      agent_id: 'code-assistant',
      name: 'Code Assistant',
      agent_type: 'developer',
    },
    {
      agent_id: 'content-writer',
      name: 'Content Writer',
      agent_type: 'writer',
    },
  ];

  for (const agent of agents) {
    try {
      console.log(`📝 Registering agent: ${agent.name} (${agent.agent_id})...`);
      const response = await makeRequest('POST', '/agents', agent);

      if (response.status === 200 || response.status === 201) {
        console.log(`   ✅ Success!\n`);
      } else {
        console.log(`   ⚠️  Status: ${response.status}`);
        console.log(`   Response:`, response.data, '\n');
      }
    } catch (error) {
      console.error(`   ❌ Error: ${error.message}\n`);
    }
  }

  // Now add some sample memories
  console.log('\n📚 Adding sample memories...\n');

  const memories = [
    {
      agent_id: 'research-agent',
      content: 'Neo4j is a graph database that stores data in nodes and relationships',
      memory_type: 'fact',
      importance: 0.9,
    },
    {
      agent_id: 'research-agent',
      content: 'Python is commonly used for AI and machine learning applications',
      memory_type: 'fact',
      importance: 0.85,
    },
    {
      agent_id: 'code-assistant',
      content: 'TypeScript provides type safety for JavaScript applications',
      memory_type: 'fact',
      importance: 0.8,
    },
    {
      agent_id: 'code-assistant',
      content: 'Next.js is a React framework for building full-stack applications',
      memory_type: 'fact',
      importance: 0.8,
    },
  ];

  for (const memory of memories) {
    try {
      console.log(`💾 Adding memory for ${memory.agent_id}...`);
      const response = await makeRequest('POST', '/memories', memory);

      if (response.status === 200 || response.status === 201) {
        console.log(`   ✅ Success!\n`);
      } else {
        console.log(`   ⚠️  Status: ${response.status}`);
        console.log(`   Response:`, response.data, '\n');
      }
    } catch (error) {
      console.error(`   ❌ Error: ${error.message}\n`);
    }
  }

  console.log('✨ Initialization complete!\n');
  console.log('You can now use these agents in the frontend:');
  console.log('  - research-agent');
  console.log('  - code-assistant');
  console.log('  - content-writer\n');
}

initAgents().catch(console.error);
