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

const BASE = "https://financialmodelingprep.com/stable";
const UA = "pipeworx-mcp-fmp/1.0 (+https://pipeworx.io)";
const passthrough = {
  type: "object" as const,
  properties: {},
  additionalProperties: true,
};

const tools: McpToolExport["tools"] = [
  {
    name: "profile",
    description:
      "Fetch FMP company profile for a ticker symbol, including sector, industry, description, CEO, employee count, website, market cap, and exchange listing details.",
    inputSchema: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
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
  },
  {
    name: "stock_screener",
    description: "Stock screener (paid).",
    inputSchema: passthrough,
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
  },
  {
    name: "mergers_acquisitions",
    description:
      "Financial Modeling Prep recent M&A activity feed: announced deals with acquirer, target, value, date. Use for \"who did $TICKER acquire\", \"recent deals in sector X\", deal-flow monitoring.",
    inputSchema: {
      type: "object",
      properties: { page: { type: "number" } },
    },
  },
  {
    name: "delisted_companies",
    description: "Delisted companies.",
    inputSchema: {
      type: "object",
      properties: { limit: { type: "number" } },
    },
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
  },
  {
    name: "institutional_ownership",
    description: "Institutional ownership (paid).",
    inputSchema: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
  },
  {
    name: "etf_holdings",
    description: "ETF holdings (paid).",
    inputSchema: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
  },
];

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

  const get = async (path: string, params?: Record<string, unknown>) => {
    const searchParams = new URLSearchParams({ apikey: apiKey });
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (key !== "_apiKey" && value != null) {
          searchParams.set(key, String(value));
        }
      }
    }

    const response = await fetch(`${BASE}${path}?${searchParams}`, {
      headers: {
        Accept: "application/json",
        "User-Agent": UA,
      },
    });

    if (response.status === 401 || response.status === 403) {
      throw new Error("FMP: invalid API key.");
    }
    if (response.status === 402) {
      throw new Error(
        "FMP: 402 — this endpoint requires a paid plan. Free tier has changed since Aug 2025; upgrade at https://site.financialmodelingprep.com/pricing-plans.",
      );
    }
    if (response.status === 429) {
      throw new Error("FMP: 429 rate limit (free tier 250/day).");
    }
    if (!response.ok) {
      throw new Error(`FMP: ${response.status}`);
    }

    return response.json();
  };

  const requireString = (key: string, example: string) => {
    const value = args[key];
    if (typeof value !== "string" || !value.trim()) {
      throw new Error(
        `Required argument "${key}" is missing. Pass a string like ${example}.`,
      );
    }
    return value;
  };

  const symbol = () => requireString("symbol", '"AAPL"');

  switch (name) {
    case "profile":
      return get("/profile", { symbol: symbol() });
    case "quote":
      return get("/quote", { symbol: symbol() });
    case "quote_short":
      return get("/quote-short", { symbol: symbol() });
    case "historical_price":
      return get("/historical-price-eod/full", {
        symbol: symbol(),
        from: args.from,
        to: args.to,
      });
    case "intraday":
      return get(
        `/historical-chart/${encodeURIComponent(
          requireString("interval", '"1hour"'),
        )}`,
        { symbol: symbol() },
      );
    case "income_statement":
      return get("/income-statement", {
        symbol: symbol(),
        period: args.period,
        limit: args.limit,
      });
    case "balance_sheet":
      return get("/balance-sheet-statement", {
        symbol: symbol(),
        period: args.period,
        limit: args.limit,
      });
    case "cash_flow":
      return get("/cash-flow-statement", {
        symbol: symbol(),
        period: args.period,
        limit: args.limit,
      });
    case "ratios":
      return get("/ratios", {
        symbol: symbol(),
        period: args.period,
        limit: args.limit,
      });
    case "enterprise_value":
      return get("/enterprise-values", {
        symbol: symbol(),
        period: args.period,
        limit: args.limit,
      });
    case "key_metrics":
      return get("/key-metrics", {
        symbol: symbol(),
        period: args.period,
        limit: args.limit,
      });
    case "financial_growth":
      return get("/financial-growth", {
        symbol: symbol(),
        period: args.period,
        limit: args.limit,
      });
    case "search_symbol":
      return get("/search-symbol", {
        query: requireString("query", '"AAPL"'),
        limit: args.limit,
        exchange: args.exchange,
      });
    case "search_name":
      return get("/search-name", {
        query: requireString("query", '"apple"'),
        limit: args.limit,
        exchange: args.exchange,
      });
    case "stock_screener":
      return get("/company-screener", args);
    case "stock_news":
      return get("/news/stock", args);
    case "earnings_calendar":
      return get("/earnings-calendar", args);
    case "economic_calendar":
      return get("/economic-calendar", args);
    case "ipos_calendar":
      return get("/ipos-calendar", args);
    case "mergers_acquisitions":
      return get("/mergers-acquisitions-latest", args);
    case "delisted_companies":
      return get("/delisted-companies", args);
    case "insider_trading":
      return get("/insider-trading-search", args);
    case "institutional_ownership":
      return get("/institutional-ownership/symbol-ownership", {
        symbol: symbol(),
      });
    case "etf_holdings":
      return get("/etf/holdings", { symbol: symbol() });
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

export default {
  tools,
  callTool,
  meter: { credits: 1 },
} satisfies McpToolExport;
