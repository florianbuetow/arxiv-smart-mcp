# arXiv MCP Server and Rate Limiting Proxy

MCP server for searching and reading arXiv papers from AI assistants — self-rate-limited to avoid getting blocked by the arXiv API.

## Why not a simple MCP server?

The arXiv API enforces strict rate limits. If you exceed them, your IP gets blocked. A naive MCP server that calls the arXiv API directly has no way to throttle requests — and AI agents tend to fire many requests in quick succession.

This project solves that by routing all requests through a local FastAPI proxy that enforces rate limiting automatically. Your AI assistant can call as many tools as it wants without getting banned.

```
AI assistant  →  MCP server  →  FastAPI proxy (rate-limited)  →  arXiv API
```

## Tools

When connected, your AI agent gets access to these tools:

- **search_papers** — search arXiv by query with sorting options
- **get_paper** — get full metadata for a paper by arXiv ID
- **download_pdf** — download a paper's PDF
- **get_paper_html** — get the HTML rendering from ar5iv
- **get_paper_markdown** — get a markdown conversion of the paper

## Setup

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just)

**1. Initialize and start the proxy**

```bash
just init
just start
```

The proxy must be running for the MCP tools to work. The MCP server connects to the proxy on `http://127.0.0.1:7171` by default.

**2. Connect the MCP server**

Paste this to your AI assistant and ask it to add this MCP server:

```json
{
  "mcpServers": {
    "arxiv-smart": {
      "command": "npx",
      "args": ["tsx", "mcp/arxiv-smart.ts"],
      "cwd": "/path/to/arxiv-smart-mcp"
    }
  }
}
```

Replace `/path/to/arxiv-smart-mcp` with the actual path to this repository.

## Configuration

The proxy is configured via `config.yaml`, which is created from `config.yaml.template` during `just init`. Key settings:

- **port** — proxy listen port (default: 7171)
- **rate_limit_seconds** — minimum interval between arXiv API calls (default: 3.0)
- **request_timeout_seconds** — timeout for arXiv API requests (default: 30.0)

If you change the port, set the `REST_BASE` environment variable in your MCP config so the MCP server can find the proxy:

```json
{
  "mcpServers": {
    "arxiv-smart": {
      "command": "npx",
      "args": ["tsx", "mcp/arxiv-smart.ts"],
      "cwd": "/path/to/arxiv-smart-mcp",
      "env": {
        "REST_BASE": "http://127.0.0.1:7171"
      }
    }
  }
}

## License

[MIT](LICENSE)
