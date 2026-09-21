import test from "node:test";
import assert from "node:assert/strict";

import fmp from "./index.js";

type MockResponse = {
  status: number;
  ok: boolean;
  text: () => Promise<string>;
};

function response(status: number, body = ""): MockResponse {
  return {
    status,
    ok: status >= 200 && status < 300,
    text: async () => body,
  };
}

function setFetch(
  impl: (input: string | URL | Request) => Promise<MockResponse>,
): () => void {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = impl as typeof fetch;
  return () => {
    globalThis.fetch = originalFetch;
  };
}

test("profile routes to the profile endpoint", async () => {
  let requestedUrl = "";
  const restoreFetch = setFetch(async (input) => {
    requestedUrl = String(input);
    return response(200, '[{"ok":true}]');
  });

  try {
    const result = await fmp.callTool("profile", {
      symbol: " AAPL ",
      _apiKey: " demo ",
    });

    assert.deepEqual(result, [{ ok: true }]);
    assert.equal(
      requestedUrl,
      "https://financialmodelingprep.com/stable/profile?apikey=demo&symbol=AAPL",
    );
  } finally {
    restoreFetch();
  }
});

test("intraday encodes interval in the endpoint path", async () => {
  let requestedUrl = "";
  const restoreFetch = setFetch(async (input) => {
    requestedUrl = String(input);
    return response(200, "[]");
  });

  try {
    await fmp.callTool("intraday", {
      symbol: "MSFT",
      interval: "1hour",
      _apiKey: "demo",
    });

    assert.equal(
      requestedUrl,
      "https://financialmodelingprep.com/stable/historical-chart/1hour?apikey=demo&symbol=MSFT",
    );
  } finally {
    restoreFetch();
  }
});

test("success with an empty body returns null", async () => {
  const restoreFetch = setFetch(async () => response(204));

  try {
    assert.equal(
      await fmp.callTool("quote", { symbol: "AAPL", _apiKey: "demo" }),
      null,
    );
  } finally {
    restoreFetch();
  }
});

test("missing API keys are rejected before any request is sent", async () => {
  await assert.rejects(
    () => fmp.callTool("quote", { symbol: "AAPL" }),
    /FMP requires an API key\./,
  );
});

test("missing string arguments are rejected", async () => {
  await assert.rejects(
    () => fmp.callTool("quote", { symbol: "   ", _apiKey: "demo" }),
    /Required argument "symbol" is missing\./,
  );
});

test("unknown tools list the supported names", async () => {
  await assert.rejects(
    () => fmp.callTool("missing_tool", { _apiKey: "demo" }),
    /Available tools: profile, quote, quote_short/,
  );
});

test("401 responses surface an invalid API key error", async () => {
  const restoreFetch = setFetch(async () => response(401));

  try {
    await assert.rejects(
      () => fmp.callTool("quote", { symbol: "AAPL", _apiKey: "demo" }),
      /FMP: invalid API key\./,
    );
  } finally {
    restoreFetch();
  }
});

test("402 responses surface a paid-plan error", async () => {
  const restoreFetch = setFetch(async () => response(402));

  try {
    await assert.rejects(
      () => fmp.callTool("quote", { symbol: "AAPL", _apiKey: "demo" }),
      /FMP: 402 — this endpoint requires a paid plan\./,
    );
  } finally {
    restoreFetch();
  }
});

test("429 responses surface a rate-limit error", async () => {
  const restoreFetch = setFetch(async () => response(429));

  try {
    await assert.rejects(
      () => fmp.callTool("quote", { symbol: "AAPL", _apiKey: "demo" }),
      /FMP: 429 rate limit\./,
    );
  } finally {
    restoreFetch();
  }
});

test("generic HTTP failures preserve the status code", async () => {
  const restoreFetch = setFetch(async () => response(500));

  try {
    await assert.rejects(
      () => fmp.callTool("quote", { symbol: "AAPL", _apiKey: "demo" }),
      /FMP: 500/,
    );
  } finally {
    restoreFetch();
  }
});
