# Production Deployment Checklist

Complete guide for deploying your ERC-8004 TEE Agent to Phala Network CVM.

## Pre-Deployment Checklist

### 1. Code Preparation

- [ ] **Test thoroughly in VibeVM**
  - Agent starts successfully
  - All endpoints respond correctly
  - Registration flow works end-to-end
  - TEE simulation functions properly

- [ ] **Update `agent_config.json`**
  - [ ] Production agent name and description
  - [ ] Correct image URL (if applicable)
  - [ ] Enabled endpoints are configured
  - [ ] Production chain IDs are listed
  - [ ] Trust models are accurate

- [ ] **Verify `entrypoint.sh`**
  - [ ] All required system dependencies listed
  - [ ] Python package installation included
  - [ ] Custom setup steps added (models, databases, etc.)
  - [ ] Server start command is correct

- [ ] **Review source code**
  - [ ] No hardcoded secrets or API keys
  - [ ] Production-ready error handling
  - [ ] Logging configured appropriately
  - [ ] No development/debug code remaining

### 2. Repository Setup

- [ ] **Commit production code**
  ```bash
  git add .
  git commit -m "Production ready: [describe changes]"
  git push origin main
  ```

- [ ] **Record commit hash**
  ```bash
  git rev-parse HEAD
  # Save this hash - you'll need it for deployment
  ```

- [ ] **Ensure repository is public** (or add SSH key to Phala)

- [ ] **Tag release** (optional but recommended)
  ```bash
  git tag -a v1.0.0 -m "Production release v1.0.0"
  git push origin v1.0.0
  ```

### 3. Environment Configuration

- [ ] **Prepare secrets** (do NOT commit these)
  - [ ] `GITHUB_REPO`: Your repository URL
  - [ ] `GIT_COMMIT_HASH`: Production commit hash from step 2
  - [ ] `AGENT_SALT`: Unique, secure random string (save this securely!)

- [ ] **Generate AGENT_SALT**
  ```bash
  # Generate a secure random salt
  openssl rand -hex 32
  # Save this securely - you'll need it to recover your agent wallet
  ```

- [ ] **Verify contract addresses** in `.env.example`
  - ETH Sepolia (testnet):
    - `IDENTITY_REGISTRY_ADDRESS`: 0x8004A818BFB912233c491871b3d84c89A494BD9e
    - `REPUTATION_REGISTRY_ADDRESS`: 0x8004B663056A597Dffe9eCcC1965A193B7388713
    - `TEE_REGISTRY_ADDRESS`: 0x034675a9541445087Cd73B2120d6c8AF7F2056E3
    - `TEE_VERIFIER_ADDRESS`: 0x27F8C122618b05420c2f67A9464415586C30D18B

### 4. Funding Preparation

- [ ] **Acquire ETH Sepolia ETH**
  - Use [Sepolia Faucet](https://sepoliafaucet.com) or [Alchemy Faucet](https://sepoliafaucet.com)
  - Minimum: 0.001 ETH (recommended: 0.01 ETH for multiple operations)

- [ ] **Have wallet ready** to send ETH to agent's derived address

---

## Deployment Process

### Step 1: Access Phala Cloud

1. [ ] Go to [phala.com](https://phala.com)
2. [ ] Log in or create account
3. [ ] Navigate to CVM deployment section

### Step 2: Configure CVM

**Resource Configuration:**

- [ ] **CPU**: Select at least 2 cores
- [ ] **Memory**: Select at least 4GB RAM
- [ ] **Storage**: Select at least 10GB
- [ ] **TEE Type**: Intel TDX (required)

**Region Selection:**

- [ ] Choose region closest to your target users
- [ ] Note: TEE attestation requires compatible infrastructure

### Step 3: Upload Configuration

- [ ] **Upload `docker-compose.yml`** from this repository
  - The file is already configured for production
  - No modifications should be needed

### Step 4: Set Environment Variables

Configure these in Phala's secret management:

**Required Secrets:**

| Variable | Value | Example |
|----------|-------|---------|
| `GITHUB_REPO` | Your repository URL | `https://github.com/username/erc-8004-tee-agent.git` |
| `GIT_COMMIT_HASH` | Production commit hash | `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0` |
| `AGENT_SALT` | Your secure salt | `64-character-hex-string-from-openssl` |

**Optional Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `RPC_URL` | `https://1rpc.io/sepolia` | Blockchain RPC endpoint |
| `CHAIN_ID` | `11155111` | ETH Sepolia chain ID |
| `UPDATE_CODE` | `true` | Pull latest code on restart |
| `IDENTITY_REGISTRY_ADDRESS` | `0x8004A...BD9e` | Identity registry contract |
| `REPUTATION_REGISTRY_ADDRESS` | `0x8004B...8713` | Reputation registry contract |
| `TEE_REGISTRY_ADDRESS` | `0x03467...56E3` | TEE registry contract |
| `TEE_VERIFIER_ADDRESS` | `0x27F8C...D18B` | TEE verifier contract |

- [ ] All required secrets are set
- [ ] Optional variables configured if needed
- [ ] Double-check for typos in values

### Step 5: Launch CVM

- [ ] Click "Deploy" or "Launch CVM"
- [ ] Wait for initialization (typically 2-5 minutes)
- [ ] Monitor deployment logs for errors

**Expected log sequence:**

```
🔄 Cloning repository from https://github.com/...
✅ Checked out commit a1b2c3d4...
✅ Repository initialized successfully
🚀 Starting agent from entrypoint.sh...
🔧 Installing dependencies...
📦 Installing Python packages...
🚀 Starting ERC-8004 TEE Agent...
```

### Step 6: Note Agent URL

- [ ] **Save your agent URL** provided by Phala
  - Format: `https://{DSTACK_APP_ID}-8000.{DSTACK_GATEWAY_DOMAIN}`
  - Example: `https://abc123-8000.phala.network`

- [ ] **Test agent is accessible**
  ```bash
  curl https://your-agent-url.phala.network/api/status
  ```

---

## Post-Deployment Setup

### Step 1: Get Agent Wallet Address

- [ ] Navigate to your agent URL in browser
- [ ] Note the displayed wallet address (derived from `AGENT_SALT`)
- [ ] Or fetch via API:
  ```bash
  curl https://your-agent-url.phala.network/api/wallet
  ```

### Step 2: Fund Agent Wallet

- [ ] Send ETH Sepolia ETH to the agent's wallet address
  - Minimum: 0.001 ETH
  - Recommended: 0.01 ETH

- [ ] Verify transaction confirmed on [Sepolia Explorer](https://sepolia.etherscan.io)

- [ ] Check balance:
  ```bash
  curl https://your-agent-url.phala.network/api/wallet
  ```

### Step 3: Register Agent On-Chain

- [ ] Navigate to `/dashboard` on your agent URL
  - Or use API: `POST https://your-agent-url.phala.network/api/register`

- [ ] Click "Register Agent" button

- [ ] Wait for transaction confirmation

- [ ] Verify registration:
  ```bash
  curl https://your-agent-url.phala.network/api/status
  # Should show: "registered": true
  ```

### Step 4: Submit TEE Attestation

- [ ] Navigate to TEE registration interface
  - Or use API: `POST https://your-agent-url.phala.network/api/tee/register`

- [ ] Click "Register TEE" or trigger automatic submission

- [ ] Wait for attestation verification

- [ ] Verify TEE status:
  ```bash
  curl https://your-agent-url.phala.network/api/status
  # Should show: "teeVerified": true
  ```

### Step 5: Validate Deployment

Run complete validation:

- [ ] **Agent card is accessible**
  ```bash
  curl https://your-agent-url.phala.network/agent.json
  ```
  - Should return valid ERC-8004 JSON

- [ ] **A2A endpoints work**
  ```bash
  curl https://your-agent-url.phala.network/.well-known/agent-card.json
  ```

- [ ] **Status shows all systems operational**
  ```bash
  curl https://your-agent-url.phala.network/api/status
  ```
  - `registered: true`
  - `teeVerified: true`
  - `balance: > 0`

- [ ] **Test task submission** (if applicable)
  ```bash
  curl -X POST https://your-agent-url.phala.network/tasks \
    -H "Content-Type: application/json" \
    -d '{
      "type": "task-request",
      "from": "did:example:test",
      "task": {"type": "test"}
    }'
  ```

---

## Troubleshooting

### Deployment Issues

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| CVM fails to start | Invalid `docker-compose.yml` | Validate YAML syntax, check logs |
| Repository clone fails | Private repo or wrong URL | Ensure repo is public or add SSH key |
| Commit not found | Incorrect `GIT_COMMIT_HASH` | Verify with `git rev-parse HEAD` |
| Dependencies fail to install | Missing system packages | Add to `entrypoint.sh` |
| Container restarts repeatedly | Runtime error in code | Check Phala logs, test in VibeVM |

### Runtime Issues

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Agent URL not accessible | Port misconfiguration | Ensure `AGENT_PORT=80` in production |
| Wallet generation fails | `AGENT_SALT` not set | Set secret on Phala |
| Registration fails | Insufficient funds | Fund wallet with more ETH Sepolia ETH |
| TEE attestation fails | CVM not properly configured | Verify CVM has Intel TDX enabled |
| RPC errors | Wrong RPC URL or chain ID | Verify `RPC_URL` and `CHAIN_ID` match |
| Contract call fails | Wrong contract addresses | Verify addresses for target network |

### Getting Help

If you encounter issues:

1. **Check Phala CVM logs** - Most issues are visible in logs
2. **Test locally in VibeVM** - Reproduce issue in development
3. **Review configuration** - Double-check all secrets and variables
4. **Search issues** - Check repository issues for similar problems
5. **Ask for help**:
   - [GitHub Issues](https://github.com/YOUR_USERNAME/erc-8004-tee-agent/issues)
   - [Phala Discord](https://phala.com/discord)

---

## Post-Launch Checklist

### Monitoring

- [ ] Set up uptime monitoring for agent URL
- [ ] Monitor wallet balance for transaction fees
- [ ] Check logs periodically for errors
- [ ] Verify TEE attestation remains valid

### Maintenance

- [ ] Plan for code updates (set `UPDATE_CODE=true` and update `GIT_COMMIT_HASH`)
- [ ] Monitor blockchain for registry contract updates
- [ ] Keep ETH Sepolia ETH balance funded
- [ ] Document any custom maintenance procedures

### Documentation

- [ ] Document your agent's URL
- [ ] Save `AGENT_SALT` securely (needed for recovery)
- [ ] Record `GIT_COMMIT_HASH` used in production
- [ ] Note any custom configuration changes

---

## Updating Your Agent

When you need to deploy updates:

1. [ ] Make changes and test in VibeVM
2. [ ] Commit to GitHub and get new commit hash
3. [ ] Update `GIT_COMMIT_HASH` secret on Phala
4. [ ] Restart CVM (if `UPDATE_CODE=true`, will pull automatically)
5. [ ] Verify new version deployed
6. [ ] Test all functionality

**Important:** Changing `AGENT_SALT` will generate a new wallet address. Only change if you intend to create a new agent identity.

---

## Security Best Practices

- [ ] **Never commit secrets** - Use Phala's secret management
- [ ] **Secure `AGENT_SALT`** - Store in password manager, backup securely
- [ ] **Use production RPC** - Consider using private RPC for mainnet
- [ ] **Monitor wallet** - Set up alerts for unusual activity
- [ ] **Regular updates** - Keep dependencies updated for security patches
- [ ] **Code review** - Review all changes before production deployment
- [ ] **Test thoroughly** - Always test in VibeVM before deploying

---

## Success Criteria

Your deployment is successful when:

✅ Agent URL is accessible
✅ `/agent.json` returns valid ERC-8004 data
✅ Agent is registered on-chain (`registered: true`)
✅ TEE is verified (`teeVerified: true`)
✅ Wallet has sufficient balance
✅ All configured endpoints are functional
✅ A2A protocol accepts task submissions
✅ TEE attestation is cryptographically valid
✅ Agent responds to requests within expected timeframes

---

## Next Steps

After successful deployment:

1. **Register with discovery services** - List your agent in ERC-8004 registries
2. **Monitor performance** - Track request latency, success rates
3. **Optimize costs** - Monitor CVM resource usage, adjust if needed
4. **Build integrations** - Connect your agent to other ERC-8004 agents
5. **Gather feedback** - Monitor usage patterns, improve functionality
6. **Scale** - Deploy additional instances if needed

---

**Congratulations!** 🎉 Your ERC-8004 TEE Agent is now live in production!

For ongoing support, see [DEV_GUIDE.md](DEV_GUIDE.md) or reach out via [GitHub Issues](https://github.com/YOUR_USERNAME/erc-8004-tee-agent/issues).
