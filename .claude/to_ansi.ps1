# UTF-8 -> ANSI(CP949) 변환 스크립트
# 사용법:
#   .\to_ansi.ps1 'C:\path\to\file.pas'
#   .\to_ansi.ps1 'C:\path\to\file1.pas' 'C:\path\to\file2.pas'
#   .\to_ansi.ps1 'C:\path\to\dir' -Recurse   # 디렉토리 내 .pas 파일 전체

param(
    [Parameter(Mandatory=$true, Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$Paths,
    [switch]$Recurse
)

$ansi = [System.Text.Encoding]::GetEncoding(949)

$files = @()
foreach ($p in $Paths) {
    if (Test-Path $p -PathType Container) {
        $opt = if ($Recurse) { '-Recurse' } else { '' }
        $files += Get-ChildItem $p -Filter '*.pas' $(if ($Recurse) { '-Recurse' }) | Select-Object -ExpandProperty FullName
    } else {
        $files += $p
    }
}

foreach ($f in $files) {
    if (-not (Test-Path $f)) {
        Write-Host "Not found: $f"
        continue
    }
    $content = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText($f, $content, $ansi)
    Write-Host "Converted to ANSI: $f"
}
