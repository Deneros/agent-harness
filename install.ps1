# Port a PowerShell de bootstrap.sh. SIN PROBAR en Windows nativo.
# En WSL usar bootstrap.sh, que sí está verificado.
$ErrorActionPreference = "Stop"
$src   = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "home"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (Test-Path "$HOME\.claude") {
  Copy-Item "$HOME\.claude" "$HOME\.claude-backup-$stamp" -Recurse -Force
  Write-Output "==> respaldo en $HOME\.claude-backup-$stamp"
}

New-Item -ItemType Directory -Force -Path "$HOME\.agents", "$HOME\.claude" | Out-Null
Copy-Item "$src\.agents\skills" "$HOME\.agents\" -Recurse -Force
foreach ($d in "agents","commands","scripts","hooks","rules","ecc","skills") {
  Copy-Item "$src\.claude\$d" "$HOME\.claude\" -Recurse -Force
}
Copy-Item "$src\.claude\settings.json" "$HOME\.claude\settings.json" -Force

$slug = $HOME -replace '[\\/:]','-'
$mem  = "$HOME\.claude\projects\$slug\memory"
New-Item -ItemType Directory -Force -Path $mem | Out-Null
Copy-Item "$src\.claude\memory\*" $mem -Recurse -Force

$state = "$HOME\.claude\ecc\install-state.json"
if (Test-Path $state) {
  (Get-Content $state -Raw).Replace("/home/nicol", $HOME.Replace('\','/')) | Set-Content $state -NoNewline
}

Write-Output "LISTO. Ejecuta: claude login"
