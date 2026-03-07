/**
 * SURVIVE OS module template - replace MODULE_NAME with your module.
 * @module survive-MODULE_NAME
 */

import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import yaml from "js-yaml";

const MODULE_NAME = "MODULE_NAME";
const VERSION = "0.1.0";
const PORT = parseInt(process.env.PORT || "8000", 10);
const CONFIG_PATH = `/etc/survive/${MODULE_NAME}.yml`;

/** @returns {object} Module configuration from YAML file */
function loadConfig() {
  if (existsSync(CONFIG_PATH)) {
    const raw = readFileSync(CONFIG_PATH, "utf8");
    return yaml.load(raw) || {};
  }
  return {};
}

const config = loadConfig();

const server = createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "healthy", version: VERSION }));
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "not found" }));
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`[${MODULE_NAME}] listening on port ${PORT}`);
});
