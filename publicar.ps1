# Crea el repo publico HeberonMC/upcsmp-pack (si no existe) y sube el pack como release.
# Uso: .\publicar.ps1 v1
param([Parameter(Mandatory = $true)][string]$Version)

Set-Location $PSScriptRoot
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$repo = "HeberonMC/upcsmp-pack"

# En PowerShell 5.1 el stderr de gh cuenta como error, asi que se consulta con cmd.
cmd /c "`"$gh`" repo view $repo --json name >nul 2>nul"
if ($LASTEXITCODE -ne 0) {
    & $gh repo create $repo --public --description "Resource pack de UPCSMP: insignias de rangos y teams + animaciones" --source . --push
} else {
    git push origin main
}

$sha = (Get-Content salida\sha1.txt -Raw).Trim()
& $gh release create $Version salida\pack-servidor.zip --repo $repo --title $Version --notes "Pack del server. SHA1: $sha"

Write-Host ""
Write-Host "resource-pack=https://github.com/$repo/releases/download/$Version/pack-servidor.zip"
Write-Host "resource-pack-sha1=$sha"
