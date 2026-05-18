# 从 Maven Central 下载 knife4j-openapi3-ui 并解压到 backend/app/static/knife4j
$ErrorActionPreference = "Stop"
$Version = "4.5.0"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir
$DestDir = Join-Path $BackendDir "app\static\knife4j"
$JarUrl = "https://repo1.maven.org/maven2/com/github/xiaoymin/knife4j-openapi3-ui/$Version/knife4j-openapi3-ui-$Version.jar"
$TempJar = Join-Path $env:TEMP "knife4j-openapi3-ui-$Version.jar"
$TempExtract = Join-Path $env:TEMP "knife4j-extract-$Version"

Write-Host "Downloading Knife4j UI $Version ..."
Invoke-WebRequest -Uri $JarUrl -OutFile $TempJar

if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }
New-Item -ItemType Directory -Path $TempExtract -Force | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($TempJar, $TempExtract)

$Resources = Join-Path $TempExtract "META-INF\resources"
if (-not (Test-Path (Join-Path $Resources "doc.html"))) {
    Write-Error "doc.html not found in jar; check artifact version."
}

if (Test-Path $DestDir) { Remove-Item -Recurse -Force $DestDir }
Copy-Item -Path $Resources -Destination $DestDir -Recurse -Force

$GroupJson = @'
[
  {
    "name": "Job AI Copilot",
    "url": "/openapi.json",
    "swaggerVersion": "3.0",
    "location": "/openapi.json"
  }
]
'@
Set-Content -Path (Join-Path $DestDir "group.json") -Value $GroupJson -Encoding UTF8

Write-Host "Done: $DestDir"
Write-Host "Open http://127.0.0.1:8000/doc.html after starting API."
