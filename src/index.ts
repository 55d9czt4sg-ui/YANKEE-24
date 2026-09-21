interface McpToolDefinition {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
    additionalProperties?: boolean;
  };
}

interface McpToolExport {
  tools: McpToolDefinition[];
  callTool: (name: string, args: Record<string, unknown>) => Promise<unknown>;
  meter?: { credits: number };
  cost?: Record<string, unknown>;
  provider?: string;
}

interface ToolConfig extends McpToolDefinition {
  path: string | ((args: Record<string, unknown>) => string);
  params?: (args: Record<string, unknown>) => Record<string, unknown>;
}

const BASE = "https://financialmodelingprep.com/stable";
const passthrough = {
  type: "object" as const,
  properties: {},
  additionalProperties: true,
};

const requireString = (
  args: Record<string, unknown>,
  key: string,
  example: string,
) => {
  const value = args[key];
  if (typeof value !== "string") {
    throw new Error(
      `Required argument "${key}" is missing. Pass a string like ${example}.`,
    );
  }
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(
      `Required argument "${key}" is missing. Pass a string like ${example}.`,
    );
  }
  return trimmed;
};

const symbolParams = (args: Record<string, unknown>) => ({
  symbol: requireString(args, "symbol", '"AAPL"'),
});

const statementParams = (args: Record<string, unknown>) => ({
  symbol: requireString(args, "symbol", '"AAPL"'),
  period: args.period,
  limit: args.limit,
});

const searchParams = (args: Record<string, unknown>, example: string) => ({
  query: requireString(args, "query", example),
  limit: args.limit,
  exchange: args.exchange,
});

const toolConfigs: ToolConfig[] = [
  {
    name: "profile",
    description:
      "Fetch FMP company profile for a ticker symbol, including sector, industry, description, CEO, employee count, website, market cap, and exchange listing details.",
    inputSchema: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
    path: "/profile",
    params: symbolParams,
  },
  {
    name: "quote",
    description:
      "Fetch the current real-time quote for a ticker symbol from FMP, including price, change, percent change, day range, 52-week range, volume, and market cap.",
    inputSchema: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
    path: "/quote",
    params: symbolParams,
  },
  {
    name: "quote_short",
    description:
      "Fetch a lightweight FMP quote for a ticker symbol returning only price, volume, and percent change; use when only the current price is needed.",
    inputSchema: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
    path: "/quote-short",
    params: symbolParams,
  },
  {
    name: "historical_price",
    description: "Daily EOD history.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        from: { type: "string" },
        to: { type: "string" },
      },
      required: ["symbol"],
    },
    path: "/historical-price-eod/full",
    params: (args) => ({
      symbol: requireString(args, "symbol", '"AAPL"'),
      from: args.from,
      to: args.to,
    }),
  },
  {
    name: "intraday",
    description: "Intraday OHLC (paid).",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        interval: { type: "string" },
      },
      required: ["symbol", "interval"],
    },
    path: (args) =>
      `/historical-chart/${encodeURIComponent(
        requireString(args, "interval", '"1hour"'),
      )}`,
    params: symbolParams,
  },
  {
    name: "income_statement",
    description: "Income statement.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        period: { type: "string" },
        limit: { type: "number" },
      },
      required: ["symbol"],
    },
    path: "/income-statement",
    params: statementParams,
  },
  {
    name: "balance_sheet",
    description: "Balance sheet.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        period: { type: "string" },
        limit: { type: "number" },
      },
      required: ["symbol"],
    },
    path: "/balance-sheet-statement",
    params: statementParams,
  },
  {
    name: "cash_flow",
    description:
      "Financial Modeling Prep cash-flow statement for a US-listed ticker: operating, investing, financing activities, free cash flow, capex, net change in cash. Annual (period=annual) or quarterly. Use for fundamental analysis, DCF inputs, cash-flow valuation.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        period: { type: "string" },
        limit: { type: "number" },
      },
      required: ["symbol"],
    },
    path: "/cash-flow-statement",
    params: statementParams,
  },
  {
    name: "ratios",
    description: "Financial ratios.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        period: { type: "string" },
        limit: { type: "number" },
      },
      required: ["symbol"],
    },
    path: "/ratios",
    params: statementParams,
  },
  {
    name: "enterprise_value",
    description: "Enterprise value.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        period: { type: "string" },
        limit: { type: "number" },
      },
      required: ["symbol"],
    },
    path: "/enterprise-values",
    params: statementParams,
  },
  {
    name: "key_metrics",
    description: "TTM key metrics.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        period: { type: "string" },
        limit: { type: "number" },
      },
      required: ["symbol"],
    },
    path: "/key-metrics",
    params: statementParams,
  },
  {
    name: "financial_growth",
    description: "Growth rates.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        period: { type: "string" },
        limit: { type: "number" },
      },
      required: ["symbol"],
    },
    path: "/financial-growth",
    params: statementParams,
  },
  {
    name: "search_symbol",
    description: "Symbol search.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        limit: { type: "number" },
        exchange: { type: "string" },
      },
      required: ["query"],
    },
    path: "/search-symbol",
    params: (args) => searchParams(args, '"AAPL"'),
  },
  {
    name: "search_name",
    description: "Company-name search.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        limit: { type: "number" },
        exchange: { type: "string" },
      },
      required: ["query"],
    },
    path: "/search-name",
    params: (args) => searchParams(args, '"apple"'),
  },
  {
    name: "stock_screener",
    description: "Stock screener (paid).",
    inputSchema: passthrough,
    path: "/company-screener",
    params: (args) => args,
  },
  {
    name: "stock_news",
    description: "News (paid).",
    inputSchema: {
      type: "object",
      properties: {
        symbols: { type: "string" },
        page: { type: "number" },
        limit: { type: "number" },
      },
    },
    path: "/news/stock",
    params: (args) => args,
  },
  {
    name: "earnings_calendar",
    description: "Earnings calendar (paid).",
    inputSchema: {
      type: "object",
      properties: {
        from: { type: "string" },
        to: { type: "string" },
      },
    },
    path: "/earnings-calendar",
    params: (args) => args,
  },
  {
    name: "economic_calendar",
    description: "Economic events (paid).",
    inputSchema: {
      type: "object",
      properties: {
        from: { type: "string" },
        to: { type: "string" },
      },
    },
    path: "/economic-calendar",
    params: (args) => args,
  },
  {
    name: "ipos_calendar",
    description: "IPO calendar (paid).",
    inputSchema: {
      type: "object",
      properties: {
        from: { type: "string" },
        to: { type: "string" },
      },
    },
    path: "/ipos-calendar",
    params: (args) => args,
  },
  {
    name: "mergers_acquisitions",
    description:
      'Financial Modeling Prep recent M&A activity feed: announced deals with acquirer, target, value, date. Use for "who did $TICKER acquire", "recent deals in sector X", deal-flow monitoring.',
    inputSchema: {
      type: "object",
      properties: { page: { type: "number" } },
    },
    path: "/mergers-acquisitions-latest",
    params: (args) => args,
  },
  {
    name: "delisted_companies",
    description: "Delisted companies.",
    inputSchema: {
      type: "object",
      properties: { limit: { type: "number" } },
    },
    path: "/delisted-companies",
    params: (args) => args,
  },
  {
    name: "insider_trading",
    description: "Insider trading (paid).",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        page: { type: "number" },
        limit: { type: "number" },
      },
    },
    path: "/insider-trading-search",
    params: (args) => args,
  },
  {
    name: "institutional_ownership",
    description: "Institutional ownership (paid).",
    inputSchema: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
    path: "/institutional-ownership/symbol-ownership",
    params: symbolParams,
  },
  {
    name: "etf_holdings",
    description: "ETF holdings (paid).",
    inputSchema: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
    path: "/etf/holdings",
    params: symbolParams,
  },
];

const tools = toolConfigs.map(({ name, description, inputSchema }) => ({
  name,
  description,
  inputSchema,
}));

const toolConfigByName = new Map(toolConfigs.map((tool) => [tool.name, tool]));

async function parseResponse(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text.trim()) {
    return null;
  }
  return JSON.parse(text) as unknown;
}

async function callTool(
  name: string,
  args: Record<string, unknown>,
): Promise<unknown> {
  const apiKey =
    (args._apiKey as string | undefined)?.trim() ??
    process.env.PLATFORM_FMP_KEY?.trim();
  if (!apiKey) {
    throw new Error(
      "FMP requires an API key. Set PLATFORM_FMP_KEY or pass ?_apiKey=… (free at https://site.financialmodelingprep.com/developer/docs).",
    );
  }

  const tool = toolConfigByName.get(name);
  if (!tool) {
    throw new Error(
      `Unknown tool: ${name}. Available tools: ${tools.map((item) => item.name).join(", ")}`,
    );
  }

  const searchParams = new URLSearchParams({ apikey: apiKey });
  const params = tool.params?.(args);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (key !== "_apiKey" && value != null) {
        searchParams.set(key, String(value));
      }
    }
  }

  const path = typeof tool.path === "function" ? tool.path(args) : tool.path;
  const response = await fetch(`${BASE}${path}?${searchParams}`, {
    headers: { Accept: "application/json" },
  });

  if (response.status === 401 || response.status === 403) {
    throw new Error("FMP: invalid API key.");
  }
  if (response.status === 402) {
    throw new Error(
      "FMP: 402 — this endpoint requires a paid plan. See https://site.financialmodelingprep.com/pricing-plans.",
    );
  }
  if (response.status === 429) {
    throw new Error(
      "FMP: 429 rate limit. See https://site.financialmodelingprep.com/developer/docs.",
    );
  }
  if (!response.ok) {
    throw new Error(`FMP: ${response.status}`);
  }

  return parseResponse(response);
}

export default {
  tools,
  callTool,
  meter: { credits: 1 },
} satisfies McpToolExport;
