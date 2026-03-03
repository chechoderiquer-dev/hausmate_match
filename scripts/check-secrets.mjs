import { execFileSync } from "node:child_process";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";

const PLACEHOLDER_PREFIXES = [
  "your-",
  "your_",
  "example",
  "sample",
  "placeholder",
  "changeme",
  "replace",
  "<",
];

const SAFE_SECRET_METADATA_KEYS = new Set([
  "SECRETS_SCAN_OMIT_KEYS",
  "SECRETS_SCAN_OMIT_PATHS",
  "SECRETS_SCAN_ENABLED",
]);

const TEXT_EXTENSIONS = new Set([
  "",
  ".env",
  ".js",
  ".jsx",
  ".json",
  ".md",
  ".mjs",
  ".cjs",
  ".ts",
  ".tsx",
  ".toml",
  ".txt",
  ".yaml",
  ".yml",
]);

const GENERIC_SECRET_KEY_PATTERN =
  /(secret|token|password|passwd|pwd|private[_-]?key|api[_-]?key|access[_-]?key|client[_-]?secret|service[_-]?role)/i;
const EXAMPLE_FILE_PATTERN = /(^|\/)\.env(\.example|\.sample|\.template)?$/i;
const SUPABASE_VALUE_PATTERN = /^\s*(VITE_SUPABASE_(URL|ANON_KEY|TABLE))\s*=\s*(.+)\s*$/i;
const ENV_LINE_PATTERN =
  /^\s*([A-Z0-9_]*(SECRET|TOKEN|PASSWORD|PASSWD|PWD|PRIVATE_KEY|API_KEY|ACCESS_KEY|CLIENT_SECRET|SERVICE_ROLE)[A-Z0-9_]*)\s*=\s*(.+)\s*$/i;
const RAW_SECRET_PATTERNS = [
  {
    label: "Supabase service role key",
    pattern: /\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/,
    filter: (value) => value.toLowerCase().includes("service_role"),
  },
  {
    label: "Private key block",
    pattern: /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
  },
  {
    label: "GitHub personal access token",
    pattern: /\bghp_[A-Za-z0-9]{36}\b/,
  },
  {
    label: "OpenAI API key",
    pattern: /\bsk-[A-Za-z0-9]{20,}\b/,
  },
];

function runGit(args) {
  return execFileSync("git", args, { encoding: "utf8" }).trim();
}

function getCandidateFiles(scanMode) {
  if (scanMode === "staged") {
    const output = runGit(["diff", "--cached", "--name-only", "--diff-filter=ACMR"]);
    return output ? output.split("\n").filter(Boolean) : [];
  }

  const output = runGit(["ls-files"]);
  return output ? output.split("\n").filter(Boolean) : [];
}

function getFileContents(filePath, scanMode) {
  if (scanMode === "staged") {
    return execFileSync("git", ["show", `:${filePath}`], { encoding: "utf8" });
  }

  return readFileSync(filePath, "utf8");
}

function isPlaceholder(value) {
  const normalized = value.trim().replace(/^['"]|['"]$/g, "");
  if (!normalized) {
    return true;
  }

  const lower = normalized.toLowerCase();
  return PLACEHOLDER_PREFIXES.some((prefix) => lower.startsWith(prefix));
}

function isTextFile(filePath) {
  const extension = path.extname(filePath);
  return TEXT_EXTENSIONS.has(extension) || path.basename(filePath).startsWith(".env");
}

function scanContents(filePath, contents) {
  const problems = [];
  const lines = contents.split("\n");

  lines.forEach((line, index) => {
    const exampleMatch = filePath.match(EXAMPLE_FILE_PATTERN)
      ? line.match(SUPABASE_VALUE_PATTERN)
      : null;

    if (exampleMatch && !isPlaceholder(exampleMatch[3])) {
      problems.push({
        filePath,
        line: index + 1,
        reason: `${exampleMatch[1]} must stay blank or use a placeholder in example env files`,
      });
    }

    const envMatch = line.match(ENV_LINE_PATTERN);
    if (
      envMatch &&
      !SAFE_SECRET_METADATA_KEYS.has(envMatch[1]) &&
      !isPlaceholder(envMatch[3])
    ) {
      problems.push({
        filePath,
        line: index + 1,
        reason: `${envMatch[1]} looks like a real secret value`,
      });
    }
  });

  RAW_SECRET_PATTERNS.forEach(({ label, pattern, filter }) => {
    const match = contents.match(pattern);
    if (!match) {
      return;
    }

    if (filter && !filter(match[0])) {
      return;
    }

    const line = contents.slice(0, match.index).split("\n").length;
    problems.push({
      filePath,
      line,
      reason: `${label} detected`,
    });
  });

  return problems;
}

function main() {
  const scanMode = process.argv.includes("--staged") ? "staged" : "tracked";
  const files = getCandidateFiles(scanMode);
  const problems = [];

  files.forEach((filePath) => {
    if (!isTextFile(filePath)) {
      return;
    }

    try {
      if (scanMode === "tracked" && !statSync(filePath).isFile()) {
        return;
      }

      const contents = getFileContents(filePath, scanMode);
      problems.push(...scanContents(filePath, contents));
    } catch (error) {
      if (String(error).includes("exists on disk, but not in")) {
        return;
      }

      throw error;
    }
  });

  if (problems.length === 0) {
    console.log(`Secret scan passed (${scanMode}).`);
    return;
  }

  console.error("Secret scan failed:");
  problems.forEach(({ filePath, line, reason }) => {
    console.error(`- ${filePath}:${line} ${reason}`);
  });
  console.error("Remove the value or replace it with a placeholder before committing or pushing.");
  process.exit(1);
}

main();
