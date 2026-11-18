# SovRoute × CrewAI — Bitcoin & EVM Pre-Flight Security Guardrail

Production-ready integration connecting **CrewAI** agents to **SovRoute**'s sovereign Bitcoin Core v31.1 & EVM forensics MCP server (`https://node.sovroute.com/mcp`) over **Streamable HTTP**.

## Why This Matters
AI agents handling payments or treasury operations shouldn't guess fee rates, mempool congestion, 0-conf Replace-By-Fee (RBF) risks, or malicious EVM delegations. SovRoute acts as a **deterministic pre-flight guardrail** across **7 read-only & zero-broadcast tools**:

1. **Live Fee & Mempool Oracle** (`get_bitcoin_smart_fees`, `get_mempool_entropy`, `verify_block_header`)
2. **Next-Block Miner Template X-Ray** (`get_next_block_xray`)
3. **0-Conf RBF Double-Spend Shield** (`check_rbf_fraud_shield`)
4. **Zero-Broadcast Consensus Simulator** (`simulate_raw_transaction`)
5. **EIP-7702 AuthTx Drainer Shield** (`inspect_eip7702_authorization`)

## Option A: CrewAI 1.x Native 1-Line DSL (Recommended)
No extra adapter boilerplate or wallet required:

```python
from crewai import Agent

security_analyst = Agent(
    role="Bitcoin & EVM Pre-Flight Security Analyst",
    goal="Verify transaction safety before accepting 0-conf payments or signing EVM delegations.",
    backstory="Deterministic blockchain risk officer backed by bare-metal Bitcoin Core v31.1 and opcode forensics.",
    mcps=["https://node.sovroute.com/mcp"],  # All 7 deterministic safety tools
)
```

## Option B: Full Demo Script (`MCPServerAdapter`)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1. Smoke-Test MCP Connection (No LLM Key Required)
```bash
python main.py --verify-mcp
```

### 2. Run Full CrewAI Security Analyst Agent
Set `OPENAI_API_KEY` in your shell or `.env`, then run:
```bash
python main.py --txid 2fbddb2c398026ca1d43b08570e7dc64acdb091702585f9f9b605963185b9c9d
```

## Sample Live Output (Mainnet)
Tested with `crewai 1.15.41` + `MCPServerAdapter` (`streamable-http`) against `https://node.sovroute.com/mcp`:

```markdown
# Pre-Flight Security Report

### Network Fees
- Fastest Fee Rate: 1 sat/vB | Half Hour: 1 sat/vB | Hourly: 1 sat/vB
- Congestion Level: HIGH

### Mempool State
- Unconfirmed Transaction Count: 45,924
- Total Mempool Size: 27,845,929 bytes | Total Fee Pool: 4,398,987 satoshis
- Minimum Fee Rate: 0.1 sat/vB | Median Fee Rate: 1 sat/vB

### Next-Block Inclusion Analysis
- Candidate Block Height: 976430 (Block Fill: 99.8%)
- Transaction Rank in Next Block: 753 (85.41 percentile)
- Fee Rate for Transaction: 1.06 sat/vB | Cutoff Fee Rate: 0.1 sat/vB
- Verdict on Inclusion: GUARANTEED_NEXT_BLOCK

### RBF/Consensus Findings
- BIP-125 Replace-By-Fee: Enabled (Risk Level: HIGH_RISK_RBF_ENABLED)
- Recommendation: Transaction can be replaced, wait for 1 block confirmation before accepting payment.

### Final Verdict
HOLD: Due to the high risk associated with the BIP-125 RBF status, it is advised to delay acceptance or broadcasting of this transaction until it receives confirmation.
```

## Evaluation Quota & Pay-Per-Call Pricing
No account, subscription, or API key exists on SovRoute — everything settles **purely per request**:
* **Evaluation Sandbox:** `https://node.sovroute.com/mcp` allows **15 free `tools/call` executions per 24h per IP** (handshakes & `tools/list` are unlimited) so CrewAI developers can test with zero wallet setup.
* **Production Pay-Per-Call (No Subscriptions):** Once the 15-call evaluation quota is reached, `/mcp` returns an **HTTP `402 Payment Required`** challenge (or use `@aipp/sovereign-node-mcp` stdio client / REST endpoints at `https://node.sovroute.com/openapi.json`):
  * **Lightning Network (L402):** `1–5 sats` per call (`Authorization: L402 <macaroon>:<preimage>`)
  * **Base L2 USDC (x402 v2):** `$0.001–$0.005` per call (`Payment-Signature: <base64_eip3009_payload>`)
