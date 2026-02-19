# ERC-8004 TEE Agent

AI agent with on-chain identity (ERC-8004), TEE attestation (Intel TDX), and chat interface.

## Features

- **TEE-Secured Execution** - Intel TDX via dstack on Phala Cloud
- **On-Chain Identity** - ERC-8004 compliant registration
- **Reputation System** - On-chain feedback and trust scores
- **Chat Interface** - Interactive AI chat with tool calling
- **Code Execution** - Run Python/shell with network access
- **Cryptographic Signing** - TEE-derived keys for message signing

## Quick Start

### Local Development

```bash
# Clone and setup
git clone https://github.com/Phala-Network/erc-8004-tee-agent.git
cd erc-8004-tee-agent
cp .env.example .env
# Edit .env with your API keys

# Install and run
pip3 install -e .
python3 deployment/local_agent_server.py
```

Open http://localhost:8000 - you'll see the dashboard.

### Production Deployment (Phala Cloud)

```bash
# Commit your code
git add . && git commit -m "Production ready"
git push origin main

# Deploy to Phala
npx phala deploy -n my-tee-agent -c docker-compose.yml -e .env
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Dashboard                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Register │→ │Reputation│→ │ Chat/Develop │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
         ↓              ↓              ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Identity   │  │ Reputation  │  │    TEE      │
│  Registry   │  │  Registry   │  │ Attestation │
└─────────────┘  └─────────────┘  └─────────────┘
    (ERC-8004)      (On-chain)      (Intel TDX)
```

**Registration Flow:**
1. **Fund Wallet** - Send ETH to your TEE-derived address
2. **Register Identity** - Mint agent NFT on IdentityRegistry
3. **Submit Reputation** - Initialize on-chain reputation entry
4. **Start Using** - Chat interface and API ready

## Project Structure

```
erc-8004-tee-agent/
├── agent_config.json          # Agent metadata (ERC-8004 format)
├── docker-compose.yml         # Production deployment
├── .env.example               # Environment template
├── entrypoint.sh              # Container startup script
├── src/agent/
│   ├── base.py               # Base agent class
│   ├── chat_agent.py         # Chat interface with tools
│   ├── code_executor.py      # Python/shell execution
│   ├── registry.py           # On-chain registry client
│   ├── tee_auth.py           # TEE key derivation
│   ├── agent_card.py         # ERC-8004 card builders
│   └── chain_config.py       # Multi-chain configuration
├── deployment/
│   └── local_agent_server.py # FastAPI server
└── static/                    # Web UI (dashboard, chat)
```

## API Endpoints

### ERC-8004 Standard
- `GET /agent.json` - Registration-v1 format
- `GET /.well-known/agent-card.json` - A2A agent card
- `GET /.well-known/agent-registration.json` - Domain verification

### Dashboard & Registration
- `GET /dashboard` - Registration dashboard
- `GET /developer` - Chat interface
- `GET /api/status` - Agent status
- `POST /api/register` - Register on-chain
- `POST /api/metadata/update` - Update on-chain metadata

### Chat Interface
- `POST /api/chat` - Send message to AI
- `POST /api/quick-action` - Execute tool directly
- `GET /api/session/{id}/history` - Get chat history

### Reputation
- `GET /api/reputation` - Get agent reputation
- `POST /api/reputation/submit-initial` - Initialize reputation

### TEE Attestation
- `GET /api/tee/attestation` - Get TEE attestation proof

## Chat Interface Tools

The AI assistant has access to these tools:

| Tool | Description |
|------|-------------|
| `get_wallet_info` | Wallet address, balance, chain info |
| `sign_message` | Sign with TEE-derived key |
| `verify_signature` | Verify signed messages |
| `generate_attestation` | Get Intel TDX attestation |
| `run_python` | Execute Python code |
| `run_shell` | Execute shell commands |
| `get_reputation` | Query agent reputation |
| `submit_feedback` | Rate other agents |

## Configuration

### Environment Variables

See [.env.example](.env.example) for all options. Key variables:

```bash
# Required
AGENT_SALT=unique-secret-salt
REDPILL_API_KEY=sk-your-key
SUBGRAPH_API_KEY=your-graph-key

# Blockchain
CHAIN_NAME=eth-sepolia
RPC_URL=https://1rpc.io/sepolia

# AI Model
ANTHROPIC_MODEL=openai/gpt-oss-120b
```

### Agent Config

Edit `agent_config.json` for agent metadata:

```json
{
  "type": "agent-registration-v1",
  "metadata": {
    "name": "My Agent",
    "description": "What my agent does"
  },
  "trust": {
    "supportedTrust": ["tee-attestation", "reputation"]
  }
}
```

## Deployed Contracts (ETH Sepolia)

| Contract | Address |
|----------|---------|
| IdentityRegistry | `0x8004A818BFB912233c491871b3d84c89A494BD9e` |
| ReputationRegistry | `0x8004B663056A597Dffe9eCcC1965A193B7388713` |

### TRON (via M2M TRC-8004 Registry)

| Contract | Address (Mainnet) | Address (Shasta) |
|----------|-------------------|-------------------|
| IdentityRegistry | `THmfi8uJuUpTfUmYLDX7UD1KaE4P6HKgqA` | `TFKNqk9bjwWp5uRiiGimqfLhVQB8jSxYi7` |
| ReputationRegistry | `TV8KWmp8qcj55sjs1NSjVxmRmZP7CYzNxH` | `TRaYogyr2qc7WgsmuVF5Js39aCmoG7vZrA` |

> TRON implementation by [M2M TRC-8004 Registry](https://m2mregistry.io). For TRON integration, use the [M2M Python SDK](https://github.com/M2M-TRC8004-Registry/trc8004-m2m-sdk).

## Tech Stack

- **TEE**: Intel TDX via Phala Cloud / dstack
- **Blockchain**: ETH Sepolia (ERC-8004)
- **Backend**: Python 3, FastAPI
- **AI**: RedPill Confidential AI (TEE-secured inference)
- **Data**: The Graph subgraph
- **Deployment**: Docker, Phala Cloud

## Documentation

- [DEV_GUIDE.md](DEV_GUIDE.md) - Developer guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [QUICKSTART.md](QUICKSTART.md) - Get started fast

## Links

- [ERC-8004 Spec](https://eips.ethereum.org/EIPS/eip-8004)
- [Phala Network](https://phala.network)
- [The Graph Subgraph](https://thegraph.com/explorer/subgraph/6wQRC7geo9XYAhckfmfo8kbMRLeWU8KQd3XsJqFKmZLT)
- [Sepolia Explorer](https://sepolia.etherscan.io)
- [M2M TRC-8004 Registry](https://m2mregistry.io) - ERC-8004 on TRON

## License

MIT
