"""
SovRoute x CrewAI — Bitcoin Pre-Flight Security Guardrail Demo

Connects a CrewAI agent to SovRoute's Remote Streamable HTTP MCP server
(https://node.sovroute.com/mcp) to evaluate Bitcoin transactions before
accepting 0-conf payments or broadcasting raw transactions.

Modes:
  python main.py --verify-mcp
      Verifies MCP handshake, tool discovery, and live tool execution without requiring an LLM key.

  python main.py --txid <64-char-hex-txid>
      Runs the full CrewAI Security Analyst agent and produces a Pre-Flight Security Report.
"""

import argparse
import asyncio
import json
import os
import sys
from dotenv import load_dotenv
import httpx

load_dotenv()

SOVROUTE_MCP_URL = os.getenv("SOVROUTE_MCP_URL", "https://node.sovroute.com/mcp")
SOVROUTE_MCP_API_KEY = os.getenv("SOVROUTE_MCP_API_KEY", "").strip()


def _mcp_headers() -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if SOVROUTE_MCP_API_KEY:
        headers["Authorization"] = f"Bearer {SOVROUTE_MCP_API_KEY}"
    return headers


def _parse_mcp_response(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return json.loads(text)


async def verify_mcp_connection(txid: str | None = None) -> None:
    """Smoke-test the SovRoute Remote MCP endpoint without needing an LLM key."""
    print(f"[SovRoute MCP] Connecting to {SOVROUTE_MCP_URL} ...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        init_res = await client.post(
            SOVROUTE_MCP_URL,
            headers=_mcp_headers(),
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "sovroute-crewai-verifier", "version": "1.0.0"},
                },
            },
        )
        init_res.raise_for_status()
        print("[SovRoute MCP] Handshake OK")

        list_res = await client.post(
            SOVROUTE_MCP_URL,
            headers=_mcp_headers(),
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        list_res.raise_for_status()
        tools = _parse_mcp_response(list_res.text)["result"]["tools"]
        print(f"[SovRoute MCP] Discovered {len(tools)} tools: {[t['name'] for t in tools]}")

        fee_res = await client.post(
            SOVROUTE_MCP_URL,
            headers=_mcp_headers(),
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "get_bitcoin_smart_fees", "arguments": {}},
            },
        )
        fee_res.raise_for_status()
        print("[SovRoute MCP] get_bitcoin_smart_fees output:")
        print(_parse_mcp_response(fee_res.text)["result"]["content"][0]["text"])

        if txid:
            rbf_res = await client.post(
                SOVROUTE_MCP_URL,
                headers=_mcp_headers(),
                json={
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "check_rbf_fraud_shield", "arguments": {"txid": txid}},
                },
            )
            rbf_res.raise_for_status()
            print(f"[SovRoute MCP] check_rbf_fraud_shield({txid}) output:")
            print(_parse_mcp_response(rbf_res.text)["result"]["content"][0]["text"])


def run_crewai_audit(txid: str | None, raw_tx_hex: str | None) -> None:
    """Run the CrewAI Bitcoin Pre-Flight Security Analyst against SovRoute MCP."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is required for full CrewAI mode. Use --verify-mcp for key-free smoke testing.")
        sys.exit(1)

    from crewai import Agent, Crew, LLM, Task
    from crewai_tools import MCPServerAdapter

    model_name = os.getenv("CREWAI_MODEL", "gpt-4o-mini")
    api_base = os.getenv("OPENAI_API_BASE", "").strip()
    llm_kwargs: dict = {"model": model_name, "api_key": os.getenv("OPENAI_API_KEY")}
    if api_base:
        llm_kwargs["base_url"] = api_base
    agent_llm = LLM(**llm_kwargs)

    server_params = {
        "url": SOVROUTE_MCP_URL,
        "transport": "streamable-http",
    }
    if SOVROUTE_MCP_API_KEY:
        server_params["headers"] = {"Authorization": f"Bearer {SOVROUTE_MCP_API_KEY}"}

    with MCPServerAdapter(server_params) as mcp_tools:
        security_analyst = Agent(
            role="Bitcoin Pre-Flight Security Analyst",
            goal=(
                "Evaluate Bitcoin transactions and mempool conditions using verifiable "
                "Bitcoin Core RPC data from SovRoute MCP before any payment is accepted or broadcast."
            ),
            backstory=(
                "You are a deterministic blockchain risk officer. You never guess fee rates, "
                "RBF risks, or transaction validity; you always verify them with SovRoute MCP tools."
            ),
            tools=mcp_tools,
            llm=agent_llm,
            verbose=True,
        )

        target_desc = []
        if txid:
            target_desc.append(f"Transaction ID (txid): {txid}")
        if raw_tx_hex:
            target_desc.append(f"Signed Raw Tx Hex: {raw_tx_hex}")
        if not target_desc:
            target_desc.append("No specific txid provided; audit current Bitcoin mainnet fee & mempool readiness.")

        audit_task = Task(
            description=(
                "Perform a Pre-Flight Bitcoin Security Audit for the following target:\n"
                + "\n".join(target_desc)
                + "\n\nRequired checks:\n"
                "1. Call get_bitcoin_smart_fees and get_mempool_entropy to assess current network congestion.\n"
                "2. Call get_next_block_xray (with txid if provided) to check next-block cutoff fee and rank.\n"
                "3. If txid is provided, call check_rbf_fraud_shield to detect BIP-125 RBF double-spend risk.\n"
                "4. If rawTxHex is provided, call simulate_raw_transaction for zero-broadcast consensus validation.\n"
                "5. Produce a concise Pre-Flight Security Report ending with a clear verdict: APPROVE, HOLD, or REJECT."
            ),
            expected_output=(
                "Structured Markdown Pre-Flight Security Report with Network Fees, Mempool State, "
                "Next-Block Inclusion Analysis, RBF/Consensus Findings, and Final Verdict (APPROVE/HOLD/REJECT)."
            ),
            agent=security_analyst,
        )

        crew = Crew(agents=[security_analyst], tasks=[audit_task], verbose=True)
        result = crew.kickoff()
        print("\n=== SOVROUTE x CREWAI PRE-FLIGHT SECURITY REPORT ===\n")
        print(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="SovRoute x CrewAI Bitcoin Guardrail Demo")
    parser.add_argument("--verify-mcp", action="store_true", help="Smoke-test SovRoute MCP endpoint without LLM")
    parser.add_argument("--txid", type=str, default=None, help="64-char hex Bitcoin transaction ID to audit")
    parser.add_argument("--raw-tx-hex", type=str, default=None, help="Raw signed Bitcoin tx hex to simulate")
    args = parser.parse_args()

    if args.verify_mcp:
        asyncio.run(verify_mcp_connection(args.txid))
        return

    run_crewai_audit(args.txid, args.raw_tx_hex)


if __name__ == "__main__":
    main()
