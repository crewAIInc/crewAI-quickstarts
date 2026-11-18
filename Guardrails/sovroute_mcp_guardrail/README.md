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

---

## Technical Evidence & Verification

### Official Infrastructure
| Resource | Location |
| :--- | :--- |
| Official website | https://sovroute.com |
| Live node | https://node.sovroute.com |
| Remote MCP endpoint | `https://node.sovroute.com/mcp` |
| OpenAPI 3.1 specification | https://node.sovroute.com/openapi.json |
| MCP configuration | https://node.sovroute.com/mcp-config.json |
| CrewAI Quickstarts PR | https://github.com/crewAIInc/crewAI-quickstarts/pull/10 |
| Standalone demonstration | https://github.com/sovroutecore/sovroute-crewai-guardrail |

### 1. Architecture
SovRoute exposes seven deterministic, read-only and non-broadcast blockchain intelligence tools through a Remote Streamable HTTP MCP endpoint (`https://node.sovroute.com/mcp`), backed by a bare-metal Bitcoin Core v31.1 fullnode and deterministic EVM authorization inspection:

```text
CrewAI Application -> CrewAI Agent -> Remote Streamable HTTP (POST /mcp)
  -> SovRoute MCP Node -> Bitcoin Core RPC / EVM Inspection -> Deterministic Tool Results -> Agent Security Assessment
```

* **Read-only security tooling:** None of the seven exposed tools sign transactions, hold user funds, or expose wallet spending functions.
* **Non-broadcast validation:** `simulate_raw_transaction` runs `testmempoolaccept` locally on Bitcoin Core without broadcasting over P2P.
* **Compatibility note:** Verified on `crewai 1.15.41` using both `Agent(..., mcps=["https://node.sovroute.com/mcp"])` and `crewai_tools.MCPServerAdapter` (`streamable-http` transport).

### 2. Security Tool Guarantees & Limitations
* `get_bitcoin_smart_fees` / `get_mempool_entropy` / `verify_block_header`: Point-in-time observations of the node's synced chain and mempool state.
* `get_next_block_xray`: Inspects the live `getblocktemplate` candidate block (`GUARANTEED_NEXT_BLOCK` / `QUEUED_FOR_LATER`). **Important:** `GUARANTEED_NEXT_BLOCK` is a candidate-template estimate at snapshot time and is **not** a guarantee of miner selection or confirmation.
* `check_rbf_fraud_shield`: Inspects BIP-125 replaceability signaling. `HIGH_RISK_RBF_ENABLED` is a replaceability risk indicator, not proof of fraud.
* `simulate_raw_transaction`: Non-broadcast transaction validation via Bitcoin Core's `testmempoolaccept` RPC (`broadcastedToNetwork: false`). Passing `testmempoolaccept` does not guarantee future mempool acceptance or block confirmation.
* `inspect_eip7702_authorization`: Inspects `chainId` (including `chainId=0` cross-chain replay consideration), EVM opcodes, and function selectors. Matches are indicators for review, not conclusive proof of malicious behavior.

### 3. Live Mainnet Demonstration (Snapshot UTC: `2026-11-18T11:57:35Z`)
* **Bitcoin Transaction ID:** `2fbddb2c398026ca1d43b08570e7dc64acdb091702585f9f9b605963185b9c9d`
* **Command:** `python main.py --txid 2fbddb2c398026ca1d43b08570e7dc64acdb091702585f9f9b605963185b9c9d`
* **Snapshot Block Height:** `976429` (Candidate block template: `976430`, `99.8%` full)
* **Key Finding:** Economically competitive for next-block inclusion (`1.06 sat/vB`, rank `753`, `85.41` percentile vs. `0.1 sat/vB` template cutoff), **yet flagged `HOLD`** because BIP-125 RBF is enabled (`HIGH_RISK_RBF_ENABLED`). Demonstrates separating inclusion probability from payment finality.
* **Raw Transaction Non-Broadcast Test (`--raw-tx-hex`):** Verified with a 444-hex-char signed transaction (`txid: 2e3ab2d6293da56a84277c5d57df6679db7da8d5e734830fe97c5b21641df30d`) sampled from the public Bitcoin mainnet mempool (contains zero private keys or project wallet data). `testmempoolaccept` evaluated consensus acceptance without P2P broadcast.

### 4. Verification & Test Suites (Project-Run Results)

#### Suite A — Core, MCP HTTP & Exhaustive Scenarios
* `sovroute` Core Protocol Suite (`npm test`): **377/377 PASS**
* `sovereign-node-engine` MCP HTTP & Exhaustive Suite (`npx tsx --test tests/mcp-http.test.ts tests/exhaustive-scenarios.test.ts`): **8/8 PASS** (`5/5` exhaustive cross-rail/retry-voucher scenarios + `3/3` `/mcp` Streamable HTTP, `X-Sandbox-Limit: 15`, and `HTTP 402` Pay-Per-Call gate tests).

```text
✔ SCENARIO 1: Bitcoin Forensics & BOLT-11 Parser Boundary Matrix
✔ SCENARIO 2: Full Route, Alias, Discovery Spec, Content Negotiation & CORS Preflight Matrix
✔ SCENARIO 3: On-Chain RPC Verification Edge Cases & Self-Transfer Attack
✔ SCENARIO 4: SUB-LIG /v1/omni/pay-lightning 500/503 Failure & 25-sat Retry Voucher Recovery
✔ SCENARIO 5: Cross-Endpoint Tier Downgrade Redemption & AutonomousL402Agent / MCP Self-Healing
▶ Hosted Remote Streamable HTTP MCP (/mcp)
  ✔ responds to initialize and lists exactly 7 deterministic read-only tools (excludes pay_lightning_invoice and ML prototype)
  ✔ executes get_bitcoin_smart_fees within 15/day sandbox and rejects malformed txid in check_rbf_fraud_shield
  ✔ returns 405 on GET /mcp and requires 402 Pay-Per-Call on tools/call when sandbox is disabled
ℹ tests 8 | pass 8 | fail 0
```

#### Suite B — Live Mainnet L402 Lightning Payment Verification
Executed directly against `https://node.sovroute.com` using Phoenixd Mainnet (`npx tsx scripts/verify-live-forensics-l402.ts`, **8/8 PASS**, `11,440ms`, `14,365 -> 14,333 sats`, `32 sats` total spent including routing fees, redacted preimages):

```text
TEST 1: GET /v1/chain/btc/next-block-xray (3 sats)   -> PASS (1892ms, Preimage: 019a731954a6846f...)
TEST 2: GET /v1/chain/btc/rbf-shield/:txid (5 sats)  -> PASS (1277ms, Preimage: 01eb878f28b35d3d...)
TEST 3: POST /v1/chain/btc/simulate-tx (5 sats)      -> PASS (1834ms, Preimage: 13b5d4c22a9d2fb7..., broadcastedToNetwork: false)
TEST 4: GET /v1/chain/btc/mempool (2 sats)           -> PASS (1291ms, Preimage: 7b3c75624271da84...)
TEST 5: GET /v1/chain/btc/fees (1 sat)               -> PASS (1158ms, Preimage: b2abbc11f2b02524...)
TEST 6: GET /v1/chain/btc/block (1 sat)              -> PASS (1314ms, Preimage: 7c9002aa4ac0712a...)
TEST 7: POST /v1/chain/evm/eip7702-shield (5 sats)   -> PASS (1423ms, Preimage: 490408aac31105a3...)
TEST 8: POST /v1/chain/evm/bytecode-risk-ml (5 sats) -> PASS (1251ms, Preimage: e1c0ff9cab511ce9...)
```

*(Note: All results above are project-run reproducibility evidence, not an independent audit or CrewAI certification.)*

### 5. Reproducibility Quick Check
```bash
git clone https://github.com/sovroutecore/sovroute-crewai-guardrail.git
cd sovroute-crewai-guardrail
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --verify-mcp
```
*(Live values reflect real-time Bitcoin mainnet state at execution time; high-value applications should always apply independent confirmation thresholds and human approval policies.)*
