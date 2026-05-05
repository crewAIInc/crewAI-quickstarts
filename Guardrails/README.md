# Guardrails Quickstart

## Optional Static Release-Readiness Check
This notebook uses `SerperDevTool()` for read-only web search. The scoped `shipgate.yaml` in this directory lets maintainers run [Agents Shipgate](https://github.com/ThreeMoonsLab/agents-shipgate) as an optional static release-readiness check for the tool surface.

Because this quickstart is a notebook, the local `tool-inventory.json` documents the tool exposed by the example. Agents Shipgate reads that local metadata without running the notebook, calling Serper, making LLM calls, or uploading source.

```bash
pipx install agents-shipgate
agents-shipgate scan -c Guardrails/shipgate.yaml --ci-mode advisory
```
