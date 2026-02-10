import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const REST_BASE = process.env.REST_BASE ?? "http://127.0.0.1:7171";
const HEALTH_TIMEOUT_MS = 3000;

const server = new McpServer({
  name: "arxiv-smart-mcp",
  version: "0.1.0",
});

async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${REST_BASE}/v1/health`, {
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
    const data = (await response.json()) as { data?: { status?: string } };
    return data.data?.status === "healthy";
  } catch {
    return false;
  }
}

server.tool(
  "search_papers",
  "Search arXiv for papers matching a query",
  {
    query: z.string().describe("Search query text (arXiv query syntax)"),
    max_results: z.number().int().min(1).max(50).describe("Number of results to return (1-50)"),
    sort_by: z
      .enum(["relevance", "lastUpdatedDate", "submittedDate"])
      .describe("Sort criterion"),
    sort_order: z.enum(["ascending", "descending"]).describe("Sort direction"),
  },
  async ({ query, max_results, sort_by, sort_order }) => {
    if (!(await checkHealth())) {
      return { content: [{ type: "text", text: "arXiv proxy service is currently offline." }], isError: true };
    }

    try {
      const response = await fetch(`${REST_BASE}/v1/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, start: 0, max_results, sort_by, sort_order }),
      });
      const data = await response.json();
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
    }
  },
);

server.tool(
  "get_paper",
  "Get full metadata for a specific arXiv paper",
  {
    arxiv_id: z.string().describe("arXiv paper ID (e.g. '2301.00001v1')"),
  },
  async ({ arxiv_id }) => {
    if (!(await checkHealth())) {
      return { content: [{ type: "text", text: "arXiv proxy service is currently offline." }], isError: true };
    }

    try {
      const response = await fetch(`${REST_BASE}/v1/paper/${arxiv_id}`);
      const data = await response.json();
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
    }
  },
);

server.tool(
  "download_pdf",
  "Download PDF of an arXiv paper (returns base64-encoded content)",
  {
    arxiv_id: z.string().describe("arXiv paper ID (e.g. '2301.00001v1')"),
  },
  async ({ arxiv_id }) => {
    if (!(await checkHealth())) {
      return { content: [{ type: "text", text: "arXiv proxy service is currently offline." }], isError: true };
    }

    try {
      const response = await fetch(`${REST_BASE}/v1/paper/${arxiv_id}/pdf`);
      if (!response.ok) {
        return { content: [{ type: "text", text: `PDF download failed: ${response.status}` }], isError: true };
      }
      const buffer = await response.arrayBuffer();
      const base64 = Buffer.from(buffer).toString("base64");
      return { content: [{ type: "text", text: base64 }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
    }
  },
);

server.tool(
  "get_paper_html",
  "Get HTML rendering of an arXiv paper from ar5iv.labs.arxiv.org",
  {
    arxiv_id: z.string().describe("arXiv paper ID (e.g. '2301.00001v1')"),
  },
  async ({ arxiv_id }) => {
    if (!(await checkHealth())) {
      return { content: [{ type: "text", text: "arXiv proxy service is currently offline." }], isError: true };
    }

    try {
      const response = await fetch(`${REST_BASE}/v1/paper/${arxiv_id}/html`);
      const data = await response.json();
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
    }
  },
);

server.tool(
  "get_paper_markdown",
  "Get markdown rendering of an arXiv paper (converted from HTML)",
  {
    arxiv_id: z.string().describe("arXiv paper ID (e.g. '2301.00001v1')"),
  },
  async ({ arxiv_id }) => {
    if (!(await checkHealth())) {
      return { content: [{ type: "text", text: "arXiv proxy service is currently offline." }], isError: true };
    }

    try {
      const response = await fetch(`${REST_BASE}/v1/paper/${arxiv_id}/markdown`);
      const data = await response.json();
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
    }
  },
);

const transport = new StdioServerTransport();
await server.connect(transport);
