#Requires -Version 5.1
# SPDX-License-Identifier: MIT
# Offline preparation from the original bundled package; no system installation.
$FontSpecs = @(
    @{ File = 'Arial.TTF'; Target = 'Arial.ttf'; Aliases = @('Arial.TTF','Arial.ttf','arial.ttf'); Hash = '35c0f3559d8db569e36c31095b8a60d441643d95f59139de40e23fada819b833' },
    @{ File = 'Arialbd.TTF'; Target = 'Arial_Bold.ttf'; Aliases = @('Arialbd.TTF','Arial_Bold.ttf','arialbd.ttf'); Hash = '4044aa6b5bebbc36980206b45b0aaaaa5681552a48bcadb41746d5d1d71fd7b4' },
    @{ File = 'Ariali.TTF'; Target = 'Arial_Italic.ttf'; Aliases = @('Ariali.TTF','Arial_Italic.ttf','ariali.ttf'); Hash = '70ade233175a6a6675e4501461af9326e6f78b1ffdf787ca0da5ab0fc8c9cfd6' },
    @{ File = 'Arialbi.TTF'; Target = 'Arial_Bold_Italic.ttf'; Aliases = @('Arialbi.TTF','Arial_Bold_Italic.ttf','arialbi.ttf'); Hash = '2f371cd9d96b3ac544519d85c16dc43ceacdfcea35090ee8ddf3ec5857c50328' }
)

function Find-ControlledFonts([string[]]$Roots) {
    $Found = @()
    foreach ($Spec in $script:FontSpecs) {
        $Match = $null
        foreach ($Root in $Roots) {
            if (-not $Root) { continue }
            foreach ($Alias in $Spec.Aliases) {
                $File = Join-Path $Root $Alias
                if ((Test-Path -LiteralPath $File -PathType Leaf) -and (Get-Sha256 $File) -eq $Spec.Hash) {
                    $Match = (Resolve-Path -LiteralPath $File).ProviderPath
                    break
                }
            }
            if ($Match) { break }
        }
        if (-not $Match) { return @() }
        $Found += @{ Source = $Match; Target = $Spec.Target }
    }
    return $Found
}

function Get-ControlledFonts {
    $Cache = Join-Path $env:LOCALAPPDATA 'DGDTL\fonts'
    $Roots = @($script:FontDirectory, $env:DGDTL_ARIAL_FONT_DIR, $Cache, (Join-Path $env:WINDIR 'Fonts'))
    $Found = @(Find-ControlledFonts $Roots)
    if ($Found.Count -eq 4) { return $Found }

    $Package = Join-Path $PSScriptRoot 'third-party\arial32.exe'
    if ($script:InstallerPath) { $Package = (Resolve-Path -LiteralPath $script:InstallerPath).ProviderPath }
    $Expected = '85297a4d146e9c87ac6f74822734bdee5f4b2a722d7eaa584b7f2cbf76f478f6'
    if (-not (Test-Path -LiteralPath $Package -PathType Leaf)) {
        throw "Bundled Arial package missing: $Package. Restore the complete release."
    }
    $PackageHash = Get-Sha256 $Package
    $PackageBytes = (Get-Item -LiteralPath $Package).Length
    if ($PackageHash -ne $Expected -or $PackageBytes -ne 554208) {
        throw "Arial package identity mismatch: $Package ($PackageBytes bytes; SHA256 $PackageHash). Restore the exact distributed package."
    }
    $Eula = Join-Path $PSScriptRoot 'THIRD_PARTY_NOTICES\MICROSOFT_TRUE_TYPE_FONTS_EULA.txt'
    if ((Get-Sha256 $Eula) -ne '2cd931154031bd5daba4adf9812bd9e2cbd8e6561b2d1699dfa1cb907fc69aeb') {
        throw 'Microsoft Core Fonts EULA identity mismatch.'
    }
    Write-Host ([IO.File]::ReadAllText($Eula, [Text.Encoding]::GetEncoding(1252)))
    $Answer = Read-Host 'Type exactly I ACCEPT to prepare the controlled Arial fonts offline, or Enter to stop'
    if ($Answer -cne 'I ACCEPT') { throw 'Font license not accepted; no font prepared.' }

    $FontTemp = Join-Path $script:TemporaryRoot 'fonts'
    New-Item -ItemType Directory -Path $FontTemp | Out-Null
    $Installer = Join-Path $FontTemp 'arial32.exe'
    [IO.File]::Copy($Package, $Installer, $false)
    if ((Get-Sha256 $Installer) -ne $Expected -or (Get-Item -LiteralPath $Installer).Length -ne 554208) {
        throw 'Arial package changed during preparation; stopped before extraction.'
    }
    # Extract the certified embedded CAB; never execute the bundled installer.
    $Bytes = [IO.File]::ReadAllBytes($Installer)
    $CabBytes = New-Object byte[] 478103
    [Array]::Copy($Bytes, 67104, $CabBytes, 0, 478103)
    $Cab = Join-Path $FontTemp 'arial32.cab'
    [IO.File]::WriteAllBytes($Cab, $CabBytes)
    if ((Get-Sha256 $Cab) -ne '8ef0b0b2cb6f2d28c695f1483eb335d8c672aeca29136ac10359ea07690694d5') {
        throw 'Embedded font cabinet identity mismatch.'
    }
    $Extract = Join-Path $FontTemp 'extracted'
    New-Item -ItemType Directory -Path $Extract | Out-Null
    $Expand = Join-Path $env:SystemRoot 'System32\expand.exe'
    & $Expand '-F:*' $Cab $Extract | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Font extraction failed: $LASTEXITCODE" }
    foreach ($Spec in $script:FontSpecs) {
        if ((Get-Sha256 (Join-Path $Extract $Spec.File)) -ne $Spec.Hash) { throw "Font mismatch: $($Spec.File)" }
        $Dest = Join-Path $Cache $Spec.File
        if ((Test-Path -LiteralPath $Dest) -and (Get-Sha256 $Dest) -ne $Spec.Hash) {
            throw "Refusing to replace a different cached font: $Dest"
        }
    }
    New-Item -ItemType Directory -Path $Cache -Force | Out-Null
    foreach ($Spec in $script:FontSpecs) {
        $Dest = Join-Path $Cache $Spec.File
        if (-not (Test-Path -LiteralPath $Dest)) { [IO.File]::Copy((Join-Path $Extract $Spec.File), $Dest, $false) }
    }
    [IO.File]::WriteAllText((Join-Path $Cache 'LICENSE_ACCEPTANCE.txt'),
        "Microsoft Core Fonts EULA accepted: $((Get-Date).ToUniversalTime().ToString('o'))`r`nInstaller SHA256: $Expected`r`n")
    $Found = @(Find-ControlledFonts @($Cache))
    if ($Found.Count -ne 4) { throw 'Controlled-font cache verification failed.' }
    Write-Host 'Controlled Arial fonts prepared offline; no Windows system fonts were changed.'
    return $Found
}
