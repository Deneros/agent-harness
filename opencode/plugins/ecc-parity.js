import { spawn } from "node:child_process";

const eccRoot = process.env.ECC_ROOT || `${process.env.HOME}/.opencode`;
const runner = `${eccRoot}/scripts/hooks/run-with-flags.js`;

const hooks = {
  before: [
    ["pre:observe:continuous-learning", "scripts/hooks/observe-runner.js"],
    ["pre:governance-capture", "scripts/hooks/governance-capture.js"],
    ["pre:mcp-health-check", "scripts/hooks/mcp-health-check.js"],
  ],
  after: [
    ["post:quality-gate", "scripts/hooks/quality-gate.js"],
    ["post:observe:continuous-learning", "scripts/hooks/observe-runner.js"],
    ["post:ecc-metrics-bridge", "scripts/hooks/ecc-metrics-bridge.js"],
    ["post:ecc-context-monitor", "scripts/hooks/ecc-context-monitor.js"],
  ],
  idle: [
    ["stop:format-typecheck", "scripts/hooks/stop-format-typecheck.js"],
    ["stop:evaluate-session", "scripts/hooks/evaluate-session.js"],
  ],
};

function run(id, script, cwd, payload) {
  const child = spawn(process.execPath, [runner, id, script, "standard,strict"], {
    cwd,
    env: { ...process.env, ECC_PLUGIN_ROOT: eccRoot, CLAUDE_PLUGIN_ROOT: eccRoot },
    stdio: ["pipe", "ignore", "ignore"],
  });
  child.stdin.end(JSON.stringify(payload));
}

function runAll(entries, cwd, payload) {
  for (const [id, script] of entries) run(id, script, cwd, payload);
}

export default async ({ directory, worktree }) => {
  const cwd = worktree || directory;
  return {
    "tool.execute.before": async (input, output) => {
      runAll(hooks.before, cwd, { hook_event_name: "PreToolUse", session_id: input.sessionID, tool_name: input.tool, tool_input: output.args });
    },
    "tool.execute.after": async (input, output) => {
      runAll(hooks.after, cwd, { hook_event_name: "PostToolUse", session_id: input.sessionID, tool_name: input.tool, tool_input: input.args, tool_output: output.output });
    },
    "session.idle": async () => runAll(hooks.idle, cwd, { hook_event_name: "Stop" }),
  };
};
