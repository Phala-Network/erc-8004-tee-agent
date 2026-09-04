# Developer Guide: Building ERC-8004 TEE Agents

This guide walks you through developing, testing, and deploying ERC-8004 compliant TEE agents using VibeVM for local development and Phala CVM for production deployment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Workflow](#development-workflow)
- [Local Development with VibeVM](#local-development-with-vibevm)
- [Customizing Your Agent](#customizing-your-agent)
- [Testing & Debugging](#testing--debugging)
- [Preparing for Production](#preparing-for-production)
- [Deployment to Phala CVM](#deployment-to-phala-cvm)

---

## Prerequisites

- **VibeVM** installed and running ([VibeVM Repository](https://github.com/Phala-Network/VibeVM))
- **Git** for version control
- **GitHub account** for hosting your agent repository
- **ETH Sepolia ETH** for on-chain registration (minimum 0.001 ETH)
- Basic knowledge of Python, FastAPI, and Docker

---

## Development Workflow

The recommended developer experience follows these steps:

```
1. Fork/Template → 2. Clone to VibeVM → 3. Local Development → 4. Test & Iterate → 5. Production Deploy
```

### Step-by-Step Overview

1. **Fork this repository** or use it as a template on GitHub
2. **Start your VibeVM** environment
3. **Clone your repository** into VibeVM
4. **Develop and test** locally like a normal development environment
5. **See registration process** in action within VibeVM
6. **Make edits and commit** to your repository
7. **Prepare for production** by finalizing `entrypoint.sh` and configuration
8. **Deploy to Phala** using `docker-compose.yml`

---

## Local Development with VibeVM

### 1. Create Your Repository

```bash
# Option A: Use as template (recommended)
# Go to GitHub and click "Use this template"

# Option B: Fork the repository
git clone https://github.com/YOUR_USERNAME/erc-8004-tee-agent.git
cd erc-8004-tee-agent
```

### 2. Set Up VibeVM

Start your VibeVM environment following the [VibeVM documentation](https://github.com/Phala-Network/VibeVM).

### 3. Clone Repository into VibeVM

Within your VibeVM environment:

```bash
git clone https://github.com/YOUR_USERNAME/erc-8004-tee-agent.git
cd erc-8004-tee-agent
```

### 4. Configure Local Environment

```bash
# Copy the local development environment template
cp .env.local.example .env

# Edit .env with your preferences
nano .env
```

**Key configurations for local development:**

```bash
AGENT_DOMAIN=localhost:8000
AGENT_SALT=local-dev-salt-change-me-123  # Change this!
RPC_URL=https://1rpc.io/sepolia
CHAIN_ID=11155111
```

### 5. Install Dependencies

```bash
# Install Python dependencies
pip3 install -e .
```

### 6. Run the Agent Locally

```bash
# Start the agent server
python3 deployment/local_agent_server.py
```

Your agent should now be running at `http://localhost:8000`

### 7. Test the Registration Process

Open your browser and navigate to:

- **Home**: `http://localhost:8000` - Funding page with QR code
- **Dashboard**: `http://localhost:8000/dashboard` - Registration interface
- **Agent Card**: `http://localhost:8000/agent.json` - ERC-8004 endpoint
- **Status**: `http://localhost:8000/api/status` - Agent status

**Test the complete flow:**

1. View your TEE-derived wallet address
2. Fund the wallet with ETH Sepolia ETH (use a faucet)
3. Register on-chain via `/api/register` endpoint
4. Submit TEE attestation via `/api/tee/register`
5. Verify agent is active at `/agent.json`

---

## Customizing Your Agent

### Agent Configuration (`agent_config.json`)

This file defines your agent's metadata and capabilities:

```json
{
  "name": "Your Agent Name",
  "description": "What your agent does",
  "image": "https://your-domain.com/agent-image.png",
  "supportedTrust": ["tee-attestation"],
  "endpoints": {
    "a2a": {
      "enabled": true,
      "version": "0.3.0"
    },
    "mcp": {
      "enabled": false,
      "endpoint": "",
      "capabilities": {},
      "version": "2025-06-18"
    }
  },
  "evmChains": [
    {"name": "Ethereum", "chainId": 1},
    {"name": "Ethereum-Sepolia", "chainId": 11155111}
  ]
}
```

### Adding Custom Endpoints

#### Enable MCP (Model Context Protocol)

```json
"mcp": {
  "enabled": true,
  "endpoint": "https://your-agent.com/mcp",
  "capabilities": {
    "tools": true,
    "resources": true
  },
  "version": "2025-06-18"
}
```

#### Add Additional Chains

```json
"evmChains": [
  {"name": "Ethereum", "chainId": 1},
  {"name": "Polygon", "chainId": 137},
  {"name": "Arbitrum", "chainId": 42161}
]
```

### Modifying Agent Logic

The core agent logic is in the `src/agent/` directory:

- **`tee_auth.py`** - TEE key derivation and authentication
- **`tee_verifier.py`** - TEE attestation and verification
- **`agent_card.py`** - ERC-8004 agent card builders
- **`registry.py`** - On-chain registry interactions
- **`base.py`** - Base agent functionality

Edit these files to customize your agent's behavior.

### Custom API Endpoints

Add custom endpoints in `deployment/local_agent_server.py`:

```python
@app.post("/api/custom-endpoint")
async def custom_endpoint(request: Request):
    """Your custom logic here"""
    return {"status": "success", "data": "..."}
```

---

## Testing & Debugging

### Local Testing

```bash
# Run the server with debug logging
python3 deployment/local_agent_server.py

# Test API endpoints
curl http://localhost:8000/api/status
curl http://localhost:8000/agent.json
curl http://localhost:8000/.well-known/agent-card.json
```

### Testing A2A Protocol

```bash
# Submit a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "task-request",
    "from": "did:example:123",
    "to": "did:example:agent",
    "task": {
      "type": "example-task",
      "parameters": {}
    }
  }'

# Check task status
curl http://localhost:8000/tasks/{task_id}
```

### Debugging TEE Integration

In VibeVM, TEE capabilities are simulated. Check logs for TEE-related operations:

```bash
# Watch logs for TEE operations
tail -f /var/log/agent.log  # Adjust path as needed
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Wallet generation fails | Ensure `AGENT_SALT` is set in `.env` |
| TEE attestation fails | In VibeVM, this is expected (simulated). Works in production CVM |
| Registration fails | Ensure wallet has sufficient ETH Sepolia ETH (0.001 ETH) |
| Port already in use | Change `AGENT_PORT` in `.env` or stop conflicting service |

---

## Preparing for Production

Before deploying to Phala CVM, ensure your agent is production-ready.

### 1. Final Testing

Test all functionality thoroughly in VibeVM:

- ✅ Wallet generation works
- ✅ On-chain registration succeeds
- ✅ All API endpoints respond correctly
- ✅ Agent card (`/agent.json`) is properly formatted
- ✅ A2A protocol endpoints are functional

### 2. Review `entrypoint.sh`

Ensure `entrypoint.sh` has the correct build and deploy steps:

```bash
#!/bin/bash
set -e

echo "🔧 Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip

echo "📦 Installing Python packages..."
pip3 install -e .

echo "🚀 Starting ERC-8004 TEE Agent..."
exec python3 deployment/local_agent_server.py
```

Add any additional setup steps your agent requires (e.g., downloading models, initializing databases, etc.).

### 3. Commit Production Code

```bash
# Stage all changes
git add .

# Commit with a clear message
git commit -m "Production-ready agent with [feature descriptions]"

# Push to your repository
git push origin main
```

**Note the commit hash** - you'll need this for deployment:

```bash
git rev-parse HEAD
# Example output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

### 4. Update `agent_config.json`

Ensure production URLs and metadata are set:

```json
{
  "name": "Production Agent Name",
  "description": "Production description",
  "image": "https://your-cdn.com/agent-image.png",
  ...
}
```

---

## Deployment to Phala CVM

### Prerequisites

- Production-ready code committed to GitHub
- Commit hash from your production commit
- Phala account on [phala.com](https://phala.com)
- ETH Sepolia ETH for agent funding

### Deployment Steps

#### 1. Configure Production Environment

Copy `.env.example` as reference for required secrets:

```bash
# Required secrets to set on Phala:
GITHUB_REPO=https://github.com/YOUR_USERNAME/YOUR_REPO.git
GIT_COMMIT_HASH=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
AGENT_SALT=your-unique-production-salt-here
```

#### 2. Upload `docker-compose.yml`

The `docker-compose.yml` file in this repository is configured for production deployment. It will:

1. Clone your GitHub repository
2. Check out the specific commit hash
3. Install dependencies
4. Run `entrypoint.sh` to start your agent

#### 3. Set Secrets on Phala

On [phala.com](https://phala.com), configure your CVM with these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `GITHUB_REPO` | `https://github.com/YOU/REPO.git` | Your forked repository URL |
| `GIT_COMMIT_HASH` | `a1b2c3d4...` | Production commit hash |
| `AGENT_SALT` | `secure-random-salt` | Unique salt for key derivation |

**Optional configurations:**

| Variable | Default | Description |
|----------|---------|-------------|
| `RPC_URL` | `https://1rpc.io/sepolia` | Blockchain RPC endpoint |
| `CHAIN_ID` | `11155111` | ETH Sepolia chain ID |
| `UPDATE_CODE` | `true` | Pull latest code on restart |

#### 4. Choose CVM Configuration

Select your TEE configuration on Phala:

- **CPU**: Minimum 2 cores recommended
- **Memory**: Minimum 4GB recommended
- **Storage**: Minimum 10GB
- **TEE Type**: Intel TDX

#### 5. Launch CVM

Click "Deploy" on Phala. The CVM will:

1. ✅ Pull Ubuntu image
2. ✅ Clone your repository
3. ✅ Check out the commit hash
4. ✅ Install dependencies
5. ✅ Start the agent

Monitor the logs to ensure successful startup.

#### 6. Note Your Agent URL

Your agent will be accessible at:

```
https://{DSTACK_APP_ID}-8000.{DSTACK_GATEWAY_DOMAIN}
```

Phala will provide this URL in your CVM dashboard.

#### 7. Fund Your Agent

1. Navigate to your agent URL
2. View the wallet address (derived from `AGENT_SALT`)
3. Fund with ETH Sepolia ETH (minimum 0.001 ETH)
4. Use the QR code or copy the address

#### 8. Register On-Chain

Navigate to `/dashboard` on your agent URL and:

1. Click "Register Agent"
2. Wait for transaction confirmation
3. Submit TEE attestation
4. Verify registration success

#### 9. Validate TEE Attestation

The agent will automatically submit TEE attestation to the verifier contract. Check the status at `/api/status`:

```bash
curl https://your-agent-url.phala.network/api/status
```

Expected response:

```json
{
  "registered": true,
  "teeVerified": true,
  "wallet": "0x...",
  "domain": "your-agent-url.phala.network"
}
```

#### 10. Interact with Your Agent

Your agent is now live! Test the endpoints:

- `https://your-agent-url.phala.network/agent.json` - ERC-8004 endpoint
- `https://your-agent-url.phala.network/.well-known/agent-card.json` - Agent card
- `https://your-agent-url.phala.network/api/status` - Status
- `https://your-agent-url.phala.network/tasks` - A2A task submission

---

## Advanced Configuration

### Custom Entrypoint

If your agent requires additional setup (e.g., downloading ML models, setting up databases), modify `entrypoint.sh`:

```bash
#!/bin/bash
set -e

echo "🔧 Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip wget

echo "📦 Installing Python packages..."
pip3 install -e .

echo "🤖 Downloading ML model..."
wget https://example.com/model.bin -O /app/model.bin

echo "💾 Initializing database..."
python3 scripts/init_db.py

echo "🚀 Starting ERC-8004 TEE Agent..."
exec python3 deployment/local_agent_server.py
```

### Environment-Specific Logic

Detect environment and adjust behavior:

```python
import os

ENV_MODE = os.getenv("ENV_MODE", "production")

if ENV_MODE == "development":
    # Use mock TEE for local testing
    from src.agent.mock_tee import MockTEE as TEE
else:
    # Use real TEE in production
    from src.agent.tee_auth import TEEAuth as TEE
```

---

## Troubleshooting

### Deployment Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| CVM fails to start | Invalid `docker-compose.yml` | Validate YAML syntax |
| Repository clone fails | Private repo or wrong URL | Ensure repo is public or add SSH key |
| Commit not found | Wrong commit hash | Verify with `git rev-parse HEAD` |
| Dependencies fail | Missing system packages | Add to `entrypoint.sh` |

### Runtime Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent not responding | Port configuration | Ensure `AGENT_PORT=80` in production |
| TEE attestation fails | CVM not properly configured | Check Phala CVM settings |
| Registration fails | Insufficient funds | Fund wallet with more ETH |
| RPC errors | Wrong RPC URL | Verify `RPC_URL` and `CHAIN_ID` |

### Debugging Production

Access CVM logs on Phala dashboard to debug issues:

```bash
# Example log output
🔄 Cloning repository from https://github.com/...
✅ Checked out commit a1b2c3d4...
✅ Repository initialized successfully
🚀 Starting agent from entrypoint.sh...
🔧 Installing dependencies...
📦 Installing Python packages...
🚀 Starting ERC-8004 TEE Agent...
```

---

## Additional Resources

- **ERC-8004 Specification**: [EIP-8004](https://eips.ethereum.org/EIPS/eip-8004)
- **VibeVM Documentation**: [GitHub](https://github.com/Phala-Network/VibeVM)
- **Phala Network**: [phala.network](https://phala.network)
- **ETH Sepolia Faucet**: [sepoliafaucet.com](https://sepoliafaucet.com)
- **A2A Protocol**: Agent-to-Agent communication standard

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/erc-8004-tee-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/erc-8004-tee-agent/discussions)
- **Phala Discord**: [discord.gg/phala](https://phala.com/discord)

---

Happy building! 🚀
