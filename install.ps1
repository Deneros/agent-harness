$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$claude = Join-Path $HOME ".claude"
$codex = Join-Path $HOME ".codex"
$opencode = Join-Path $HOME ".config/opencode/plugins"

New-Item -ItemType Directory -Force -Path $claude, $codex, $opencode | Out-Null
Copy-Item "$root/claude/settings.template.json" "$claude/agent-harness.settings.json"
Copy-Item "$root/codex/config.template.toml" "$codex/agent-harness.toml"
Copy-Item "$root/opencode/plugins/ecc-parity.js" "$opencode/ecc-parity.js"

Write-Output "Installed templates. Merge the Claude and Codex templates into their active configuration files."
