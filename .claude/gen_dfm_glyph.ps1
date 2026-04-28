# DFM Glyph.Data 인코딩 스크립트
# 사용법:
#   ConvertBmp-ToDfmHex 'C:\Temp\image.bmp' 'C:\Temp\output.txt'
#   ConvertImg-ToDfmHex 'C:\Temp\image.jpg' 'C:\Temp\output.txt'
# 주의: 한글 경로 파일은 ASCII 경로로 복사 후 사용

function ConvertBmp-ToDfmHex($path, $outPath) {
    # BMP: raw bytes 그대로 읽기 (변환 금지)
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $len = $bytes.Length
    $prefix = [byte[]]@(($len -band 0xFF), (($len -shr 8) -band 0xFF),
                        (($len -shr 16) -band 0xFF), (($len -shr 24) -band 0xFF))
    $allBytes = $prefix + $bytes
    $hex = ($allBytes | ForEach-Object { $_.ToString('X2') }) -join ''
    $lines = @()
    for ($i = 0; $i -lt $hex.Length; $i += 64) {
        $lines += '        ' + $hex.Substring($i, [Math]::Min(64, $hex.Length - $i))
    }
    $lines[-1] = $lines[-1] + '}'
    $lines | Set-Content $outPath -Encoding ASCII
    Write-Host "Done: $($bytes.Length) bytes, $($lines.Count) lines -> $outPath"
}

function ConvertImg-ToDfmHex($path, $outPath) {
    # JPG/PNG: 24bpp BMP로 변환
    Add-Type -AssemblyName System.Drawing
    $img = [System.Drawing.Image]::FromFile($path)
    $bmp = New-Object System.Drawing.Bitmap($img.Width, $img.Height,
                      [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.DrawImage($img, 0, 0, $img.Width, $img.Height)
    $g.Dispose(); $img.Dispose()
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Bmp)
    $bmp.Dispose()
    $bytes = $ms.ToArray(); $ms.Dispose()
    $len = $bytes.Length
    $prefix = [byte[]]@(($len -band 0xFF), (($len -shr 8) -band 0xFF),
                        (($len -shr 16) -band 0xFF), (($len -shr 24) -band 0xFF))
    $allBytes = $prefix + $bytes
    $hex = ($allBytes | ForEach-Object { $_.ToString('X2') }) -join ''
    $lines = @()
    for ($i = 0; $i -lt $hex.Length; $i += 64) {
        $lines += '        ' + $hex.Substring($i, [Math]::Min(64, $hex.Length - $i))
    }
    $lines[-1] = $lines[-1] + '}'
    $lines | Set-Content $outPath -Encoding ASCII
    Write-Host "Done: $($bytes.Length) bytes, $($lines.Count) lines -> $outPath"
}
