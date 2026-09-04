# Quickstart: Deploy Your TEE Agent

Deploy a trustless AI agent with on-chain identity in under 15 minutes.

## What You'll Build

An AI agent that:
- Runs in Intel TDX (trusted execution environment)
- Has verifiable on-chain identity (ERC-8004)
- Signs messages with TEE-derived keys
- Executes Python/shell code securely
- Provides cryptographic attestation proofs

## Prerequisites

- [Phala Cloud account](https://cloud.phala.network)
- Wallet with Sepolia ETH (~0.01 ETH for gas)
- [Subgraph API key](https://thegraph.com/studio/) (free)
- [RedPill API key](https://redpill.ai) (for AI chat)

---

## Step 1: Fork the Template

1. Go to [github.com/Phala-Network/erc-8004-tee-agent](https://github.com/Phala-Network/erc-8004-tee-agent)
2. Click **Fork** to create your own copy
3. Clone locally to customize:
   ```bash
   git clone https://github.com/YOUR_USERNAME/erc-8004-tee-agent.git
   cd erc-8004-tee-agent
   ```

---

## Step 2: Configure Your Agent

Copy the environment template:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
# Required secrets
AGENT_SALT=my-unique-agent-salt-12345
SUBGRAPH_API_KEY=<your-graph-api-key>
REDPILL_API_KEY=<your-redpill-key>

# These are auto-set by Phala Cloud
# AGENT_DOMAIN=${DSTACK_APP_ID}-8000.${DSTACK_GATEWAY_DOMAIN}
```

**Important:** The `AGENT_SALT` determines your wallet address. Use a unique, secure value and keep it secret.

Optionally customize `agent_config.json`:

```json
{
  "metadata": {
    "name": "My TEE Agent",
    "description": "Your agent description"
  }
}
```

---

## Step 3: Commit Your Changes

```bash
git add .
git commit -m "Configure my TEE agent"
git push origin main
```

Note your commit hash:
```bash
git rev-parse HEAD
```

---

## Step 4: Deploy on Phala Cloud

1. Go to [cloud.phala.network](https://cloud.phala.network)
2. Click **Deploy New CVM**
3. Upload `docker-compose.yml` from your repository

### Configure Your Instance

| Setting | Value |
|---------|-------|
| OS | `dstack-0.5.x` or later |
| Instance | 2+ vCPU, 4GB+ RAM, 10GB+ storage |

### Set Environment Variables

Add these as **encrypted secrets**:

| Variable | Value |
|----------|-------|
| `GITHUB_REPO` | `https://github.com/YOUR_USERNAME/erc-8004-tee-agent.git` |
| `GIT_COMMIT_HASH` | Your commit hash from Step 3 |
| `AGENT_SALT` | Your unique secret salt |
| `SUBGRAPH_API_KEY` | Your Graph API key |
| `REDPILL_API_KEY` | Your RedPill API key |

Click **Deploy** and wait for provisioning (~2-3 minutes).

---

## Step 5: Access Your Agent

1. Go to **View Details** → **Networks**
2. Your agent URL: `https://<app-id>-8000.<gateway-domain>`
3. Open it in your browser

You'll see the **Dashboard** with your wallet address.

---

## Step 6: Fund Your Wallet

1. Copy your wallet address from the Dashboard
2. Send ~0.01 Sepolia ETH to this address

Get free Sepolia ETH from:
- [sepoliafaucet.com](https://sepoliafaucet.com)
- [alchemy.com/faucets/ethereum-sepolia](https://www.alchemy.com/faucets/ethereum-sepolia)

Wait for the transaction to confirm.

---

## Step 7: Register Your Agent

On the Dashboard:

1. **Step 1: Register Identity**
   - Click **Register**
   - Wait for blockchain confirmation (~15-30 seconds)

2. **Step 2: Submit Reputation**
   - Click **Submit Initial Reputation**
   - This creates your on-chain reputation entry

Your agent now has an on-chain identity!

---

## Step 8: Start Chatting

Click **Developer API** to access the chat interface.

Try these commands:
- "What's my wallet address?"
- "Generate an attestation proof"
- "Run this Python code: print('Hello from TEE!')"
- "Sign this message: Hello World"

---

## Verify Your Agent

### Check On-Chain Registration

Visit [Sepolia Etherscan](https://sepolia.etherscan.io) and search for:
- IdentityRegistry: `0x8004A818BFB912233c491871b3d84c89A494BD9e`
- ReputationRegistry: `0x8004B663056A597Dffe9eCcC1965A193B7388713`

Your agent should appear in both registries.

### Verify TEE Attestation

In the chat, ask:
```
Generate an attestation proof
```

The response includes:
- TDX quote (cryptographic proof)
- Event log (execution trace)
- Verification info

---

## Customization

### Change Agent Metadata

Edit `agent_config.json`:

```json
{
  "metadata": {
    "name": "My Custom Agent",
    "description": "What my agent does"
  },
  "capabilities": {
    "domains": ["finance", "data-analysis"],
    "skills": ["python-execution", "api-integration"]
  }
}
```

### Add Custom Tools

Modify `src/agent/chat_agent.py` to add capabilities:
- Database queries
- External API calls
- Custom computations

### Update Your Deployment

After changes:

```bash
git add . && git commit -m "Update agent"
git push origin main
```

Get new commit hash and update `GIT_COMMIT_HASH` in Phala Cloud, then redeploy.

---

## Troubleshooting

### "Agent not registered"
- Check wallet has sufficient ETH
- Verify the transaction confirmed on Etherscan

### "Subgraph query failed"
- Verify `SUBGRAPH_API_KEY` is set correctly
- Check [The Graph status](https://thegraph.com/studio/)

### "Chat not responding"
- Verify `REDPILL_API_KEY` is valid
- Check logs in Phala Cloud dashboard

### Need Help?

- [GitHub Issues](https://github.com/Phala-Network/erc-8004-tee-agent/issues)
- [Phala Discord](https://phala.com/discord)

---

## Architecture

```
Your Browser
     ↓
┌─────────────────────────────────┐
│   TEE Agent (Intel TDX)         │
│  ┌───────────────────────────┐  │
│  │   Chat Interface (AI)     │  │
│  │   - Tool calling          │  │
│  │   - Code execution        │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   TEE-Derived Wallet      │  │
│  │   - Deterministic keys    │  │
│  │   - Message signing       │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   Attestation Engine      │  │
│  │   - TDX quotes            │  │
│  │   - Verifiable proofs     │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
     ↓              ↓
┌──────────┐  ┌──────────────┐
│ Identity │  │  Reputation  │
│ Registry │  │   Registry   │
└──────────┘  └──────────────┘
   (ERC-8004 on Sepolia)
```

---

**Congratulations!** You've deployed a TEE-secured AI agent with on-chain identity.
