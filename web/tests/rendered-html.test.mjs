import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", String(Date.now()));
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the visitor dashboard and holiday methodology", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>Singapore Visitor Pulse<\/title>/i);
  assert.match(html, /HOLIDAY OPPORTUNITY/);
  assert.match(html, /Join the weekend/);
  assert.match(html, /Carry across months/);
  assert.match(html, /Find family windows/);
  assert.match(html, /Learn by origin/);
  assert.doesNotMatch(html, /\u00c2|\u00e2|\ufffd/);
});

test("keeps the improved challenger behind the better production baseline", async () => {
  const dashboard = JSON.parse(
    await readFile(new URL("../app/data/dashboard.json", import.meta.url), "utf8"),
  );
  assert.equal(dashboard.evaluation.selected_model, "seasonal_naive");
  assert.ok(dashboard.evaluation.model.wape < 0.15);
  assert.ok(
    dashboard.evaluation.seasonal_naive.wape < dashboard.evaluation.model.wape,
  );
  assert.equal(dashboard.evaluation.model_alpha, 30);
});
