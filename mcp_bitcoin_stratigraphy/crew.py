from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

# Connect to the Bitcoin Stratigraphy MCP Server via SSE
serverparams = {
    "url": "https://bitcoin-stratigraphy-dashboard.replit.app/mcp"
}

with MCPServerAdapter(serverparams) as tools:
    notary_agent = Agent(
        role='Bitcoin Data Notary',
        goal='Fetch thermodynamic telemetry and anchor it to the Bitcoin base layer.',
        backstory='You are an autonomous AI auditor. You use L402 batch payments to access data and OpenTimestamps to notarize it.',
        tools=tools,
        verbose=True
    )

    anchor_task = Task(
        description='Fetch the latest subsurface supply dynamics and notarize the report using the proof.notarize tool.',
        expected_output='A summary of the telemetry and the cryptographic .ots receipt.',
        agent=notary_agent
    )

    crew = Crew(
        agents=[notary_agent],
        tasks=[anchor_task]
    )

    crew.kickoff()
