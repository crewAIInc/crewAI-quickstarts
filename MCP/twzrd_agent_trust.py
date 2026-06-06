"""
CrewAI + TWZRD Agent Intel: Solana Agent Trust Scoring via MCP

This quickstart demonstrates using the TWZRD Agent Intel MCP server with CrewAI
to score Solana agent wallets before authorizing x402 micropayments.

MCP server: https://intel.twzrd.xyz/mcp (streamable-HTTP, zero-install)

Tools available:
- score_agent(wallet)      : on-chain trust score 0-1 (free)
- preflight_check(wallet)  : full pre-payment due diligence (free)
- get_trust_receipt(wallet): signed trust receipt via HTTP 402 (paid)

Requirements:
    pip install crewai "crewai-tools[mcp]"
"""

from crewai import Agent, Crew, Process, Task
from crewai_tools import MCPServerAdapter


def run_trust_check(wallet: str = "D1QkbFJKiPsymJ65RKHhF6DFB8sPMfpBaFBzuHKfJGWi") -> str:
    """Run a trust check on a Solana agent wallet using TWZRD Agent Intel."""

    # MCPServerAdapter connects to the TWZRD streamable-HTTP MCP endpoint
    with MCPServerAdapter({"url": "https://intel.twzrd.xyz/mcp"}) as tools:

        analyst = Agent(
            role="Solana Agent Trust Analyst",
            goal=(
                "Evaluate Solana agent wallets for x402 payment trustworthiness. "
                "Use score_agent and preflight_check to assess on-chain reputation."
            ),
            backstory=(
                "You specialize in Solana agent ecosystems and use on-chain data to "
                "determine whether an AI agent has a reliable payment history."
            ),
            tools=tools,
            verbose=True,
        )

        task = Task(
            description=(
                f"Evaluate wallet {wallet}:\n"
                "1. Call score_agent to get the trust score\n"
                "2. Call preflight_check for full due diligence\n"
                "3. Return: score (0-1), payment count, and APPROVE/REJECT with reasoning"
            ),
            expected_output=(
                "Trust score (0-1), number of prior x402 payments, "
                "and APPROVE or REJECT recommendation with one-sentence rationale."
            ),
            agent=analyst,
        )

        crew = Crew(
            agents=[analyst],
            tasks=[task],
            process=Process.sequential,
        )

        return str(crew.kickoff())


if __name__ == "__main__":
    result = run_trust_check()
    print("\n=== Trust Assessment ===")
    print(result)
