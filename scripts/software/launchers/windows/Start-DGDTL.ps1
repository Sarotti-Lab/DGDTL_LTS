#Requires -Version 5.1
# SPDX-License-Identifier: MIT
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('Hunter','Unified')][string]$Mode,
    [string]$FontDirectory = '',
    [string]$InstallerPath = ''
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$ReleaseRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$TemporaryRoot = $null
$ExitCode = 1
$Utf8 = New-Object Text.UTF8Encoding($false)
$Python = '/opt/dgdtl/env/bin/python'
$ManifestDigest = 'sha256:d1f78a55ef681ddb79ebe9fcdfb2697e19beb8ce6fa75c9d31cbc19830198f87'
$ConfigDigest = 'sha256:912a19b08eb9d0cb5249faf63147db902a286f1c5644a1f5bed45060cd636faf'

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Invoke-DockerCapture([string[]]$DockerArguments) {
    # In PS 5.1 informational native stderr must not override the native exit code.
    $SavedPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $Lines = @(& docker.exe @DockerArguments 2>&1 | ForEach-Object { $_.ToString() })
        $Code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $SavedPreference }
    return @{ Code = $Code; Text = ($Lines -join "`n") }
}

function Get-DockerText([string[]]$DockerArguments) {
    $Result = Invoke-DockerCapture $DockerArguments
    if ($Result.Code -ne 0) { throw "Docker failed ($($Result.Code)): $($Result.Text)" }
    return $Result.Text
}

function Get-HostPath([string]$Value, [string]$Base) {
    if ($Value -eq '~' -or $Value.StartsWith('~\') -or $Value.StartsWith('~/')) {
        $Value = Join-Path ([Environment]::GetFolderPath('UserProfile')) $Value.Substring(1).TrimStart('\','/')
    }
    if ($Value -match '^[A-Za-z]:(?![\\/])' -or $Value.StartsWith('\\')) {
        throw 'Use an absolute local drive path or a path relative to the working directory.'
    }
    if (-not [IO.Path]::IsPathRooted($Value)) { $Value = Join-Path $Base $Value }
    elseif ($Value -match '^[\\/][^\\/]') {
        $Value = Join-Path ([IO.Path]::GetPathRoot($Base)) $Value.TrimStart('\','/')
    }
    $Resolved = [IO.Path]::GetFullPath($Value)
    if ($Resolved -match '[,\r\n"]') { throw 'Docker mount paths cannot contain comma, double quote or newline.' }
    # Junctions would bypass read-only product/reference boundaries.
    $Cursor = $Resolved
    while ($Cursor) {
        if (Test-Path -LiteralPath $Cursor) {
            if ((Get-Item -LiteralPath $Cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Use a physical path, without junctions or symbolic links: $Cursor"
            }
        }
        $Parent = Split-Path -Parent $Cursor
        if ($Parent -eq $Cursor) { break }
        $Cursor = $Parent
    }
    return $Resolved
}

function Test-Within([string]$Path, [string]$Root) {
    return $Path.Equals($Root, [StringComparison]::OrdinalIgnoreCase) -or
        $Path.StartsWith($Root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)
}

function Assert-WritableLocation([string]$Path) {
    if ((Test-Within $Path $script:ReleaseRoot) -or (Test-Within $script:ReleaseRoot $Path)) {
        throw 'Select a working/output directory outside the release and its parent directories.'
    }
    if ($Path -match '(?i)(^|[\\/])reference_results([\\/]|$)') {
        throw 'Certified reference_results cannot be used as a writable directory.'
    }
}

function New-Bind([string]$Source, [string]$Target, [switch]$ReadOnly) {
    $Source = Get-HostPath $Source (Get-Location).ProviderPath
    $Value = "type=bind,source=$Source,target=$Target"
    if ($ReadOnly) { $Value += ',readonly' }
    return @('--mount', $Value)
}

function Assert-Image($Image, $Config, [string]$ExpectedId) {
    if ($Image.Id -ne $ExpectedId -or $Image.Os -ne 'linux' -or $Image.Architecture -ne 'amd64') {
        throw 'Loaded Certified Runtime identity/platform mismatch.'
    }
    if (($Image.RootFS.Layers -join '|') -cne ($Config.rootfs.diff_ids -join '|') -or
        ($Image.Config.Entrypoint -join '|') -cne $script:Python) {
        throw 'Loaded Certified Runtime layers or frozen Python entrypoint mismatch.'
    }
}

function Get-CertifiedImage($Info) {
    $Oci = Join-Path $script:ReleaseRoot 'runtime\dgdtl-crt-exp-pv1-linux-amd64-c001.oci.tar'
    if ((Get-Item -LiteralPath $Oci).Length -ne 701538304 -or
        (Get-Sha256 $Oci) -ne '5f2779def4bb23fe2102945d97d34d67d949dbcd075f0483cdde415a1e949b05') {
        throw 'Official Certified Runtime OCI identity mismatch.'
    }
    $ManifestText = @(& tar.exe -xOf $Oci ('blobs/sha256/' + $script:ManifestDigest.Substring(7)))
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read the certified OCI manifest.' }
    $Manifest = ($ManifestText -join "`n") | ConvertFrom-Json
    if ($Manifest.config.digest -ne $script:ConfigDigest) { throw 'OCI config identity mismatch.' }
    $ConfigText = @(& tar.exe -xOf $Oci ('blobs/sha256/' + $script:ConfigDigest.Substring(7)))
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read the certified OCI config.' }
    $Config = ($ConfigText -join "`n") | ConvertFrom-Json
    $Containerd = ($Info.DriverStatus | ConvertTo-Json -Depth 8) -match 'io\.containerd\.snapshotter\.v1'
    $ExpectedId = if ($Containerd) { $script:ManifestDigest } else { $script:ConfigDigest }
    $Existing = Invoke-DockerCapture @('image','inspect',$ExpectedId,'--format','{{json .}}')
    if ($Existing.Code -eq 0) {
        Assert-Image ($Existing.Text | ConvertFrom-Json) $Config $ExpectedId
        return $ExpectedId
    }
    if ($Existing.Text -notmatch '(?i)no such image|no such object') {
        throw "Cannot inspect the certified image: $($Existing.Text)"
    }
    if ($Containerd) {
        Write-Host (Get-DockerText @('load','--input',$Oci))
    } else {
        # Certified transport: add only a Docker manifest to a temporary exact OCI copy.
        # Original config and compressed layer blobs are retained byte-for-byte.
        $Archive = Join-Path $script:TemporaryRoot 'runtime.docker.tar'
        $Wrapper = @(@{ Config = 'blobs/sha256/' + $script:ConfigDigest.Substring(7)
            RepoTags = @(); Layers = @($Manifest.layers | ForEach-Object { 'blobs/sha256/' + $_.digest.Substring(7) }) })
        [IO.File]::WriteAllText((Join-Path $script:TemporaryRoot 'manifest.json'),
            (ConvertTo-Json -InputObject $Wrapper -Depth 8), $script:Utf8)
        [IO.File]::Copy($Oci, $Archive, $false)
        & tar.exe -rf $Archive -C $script:TemporaryRoot manifest.json
        if ($LASTEXITCODE -ne 0) { throw 'Cannot prepare the lossless Docker transport wrapper.' }
        Write-Host (Get-DockerText @('load','--input',$Archive))
    }
    $Image = (Get-DockerText @('image','inspect',$ExpectedId,'--format','{{json .}}')) | ConvertFrom-Json
    Assert-Image $Image $Config $ExpectedId
    return $ExpectedId
}

function Invoke-Runtime([string]$Action, [string[]]$Mounts = @(), [switch]$Interactive,
    [Parameter(Mandatory = $true)][ref]$ExitStatus) {
    $DockerArguments = @('run','--rm','--pull','never') + $script:RuntimeBase + $Mounts
    if ($Interactive) { $DockerArguments += @('-it') }
    $DockerArguments += @('--entrypoint',$script:Python,$script:ImageId,'-s',
        '/release/launchers/windows/runtime_entry.py',$Action)
    $SavedPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        if ($Interactive) {
            # Keep the native console attached, including prompts without a newline.
            & docker.exe @DockerArguments
            $ExitStatus.Value = $LASTEXITCODE
        } else {
            & docker.exe @DockerArguments | Out-Host
            $ExitStatus.Value = $LASTEXITCODE
        }
    } finally { $ErrorActionPreference = $SavedPreference }
    # Call without assignment/piping: status travels separately from console I/O.
}

try {
    if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem -or
        ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64' -and $env:PROCESSOR_ARCHITEW6432 -ne 'AMD64')) {
        throw 'This launcher requires Windows x86-64.'
    }
    foreach ($Command in @('docker.exe','tar.exe','wsl.exe')) {
        if (-not (Get-Command $Command -CommandType Application -ErrorAction SilentlyContinue)) {
            throw "Missing prerequisite: $Command. Docker Desktop with WSL2/Linux containers is required."
        }
    }
    $ReleaseRoot = Get-HostPath $ReleaseRoot (Get-Location).ProviderPath
    $ReleaseManifest = Join-Path $ReleaseRoot 'manifests\RELEASE_CONTENTS.sha256'
    foreach ($Line in [IO.File]::ReadAllLines($ReleaseManifest)) {
        if ($Line -notmatch '^([0-9a-f]{64})  (.+)$') { throw 'Invalid release manifest entry.' }
        $Expected = $Matches[1]; $Relative = $Matches[2]
        $File = Get-HostPath (Join-Path $ReleaseRoot $Relative) $ReleaseRoot
        if (-not (Test-Within $File $ReleaseRoot) -or (Get-Sha256 $File) -ne $Expected) {
            throw "Release integrity mismatch: $Relative"
        }
    }
    $Info = (Get-DockerText @('info','--format','{{json .}}')) | ConvertFrom-Json
    if ($Info.OSType -ne 'linux' -or $Info.Architecture -notin @('x86_64','amd64') -or
        $Info.OperatingSystem -notmatch 'Docker Desktop' -or $Info.KernelVersion -notmatch 'microsoft-standard-WSL2') {
        throw 'Start Docker Desktop using WSL2, Linux containers and the x86-64 backend.'
    }
    $TemporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ('dgdtl-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $TemporaryRoot | Out-Null
    $ImageId = Get-CertifiedImage $Info
    . (Join-Path $PSScriptRoot 'Controlled-Fonts.ps1')
    $Fonts = @(Get-ControlledFonts)
    $RuntimeBase = @('--platform','linux/amd64','--network','none','--workdir','/work',
        '--env','PATH=/opt/dgdtl/env/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        '--env','PYTHONHASHSEED=0','--env','OPENBLAS_NUM_THREADS=1','--env','MKL_NUM_THREADS=1',
        '--env','OMP_NUM_THREADS=1','--env','VECLIB_MAXIMUM_THREADS=1','--env','NUMEXPR_NUM_THREADS=1',
        '--env','PYTHONUNBUFFERED=1','--env','PYTHONUTF8=1','--env','PYTHONPATH=',
        '--env','PYTHONNOUSERSITE=1','--env','PYTHONDONTWRITEBYTECODE=1',
        '--env','MPLCONFIGDIR=/tmp/dgdtl-matplotlib')
    $RuntimeBase += New-Bind $ReleaseRoot '/release' -ReadOnly
    foreach ($Font in $Fonts) {
        $RuntimeBase += New-Bind $Font.Source ('/opt/dgdtl/env/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf/' + $Font.Target) -ReadOnly
    }
    $Code = 1
    Invoke-Runtime 'check' -ExitStatus ([ref]$Code)
    if ($Code -ne 0) { throw "Frozen environment/font preflight failed ($Code)." }
    $Working = (Get-Location).ProviderPath
    if ($Mode -eq 'Hunter') {
        $Answer = (Read-Host 'Provide the target path for data files (Enter: current directory)').Trim(" '").Trim('"')
        if ($Answer) { $Working = Get-HostPath $Answer $Working }
    }
    $Working = Get-HostPath $Working (Get-Location).ProviderPath
    if (-not (Test-Path -LiteralPath $Working -PathType Container)) { throw "Working directory does not exist: $Working" }
    if ($Mode -eq 'Hunter') {
        $Transport = Join-Path $TemporaryRoot 'request'
        New-Item -ItemType Directory -Path $Transport | Out-Null
        Invoke-Runtime 'configure' (New-Bind $Transport '/transport') -Interactive -ExitStatus ([ref]$Code)
        if ($Code -ne 0) { throw "Hunter configuration failed ($Code)." }
        $Request = [IO.File]::ReadAllText((Join-Path $Transport 'hunter.json'), $Utf8) | ConvertFrom-Json
        $Train = Get-HostPath $Request.paths.train $Working
        $Valid = Get-HostPath $Request.paths.valid $Working
        foreach ($File in @($Train,$Valid)) {
            if (-not (Test-Path -LiteralPath $File -PathType Leaf)) { throw "Input file does not exist: $File" }
        }
        $Output = Get-HostPath $Request.paths.output $Working
        Assert-WritableLocation $Output
        foreach ($File in @($Train,$Valid)) {
            if (Test-Within $File $Output) { throw 'Select an output directory that does not contain either input dataset.' }
        }
        New-Item -ItemType Directory -Path $Output -Force | Out-Null
        $Mounts = (New-Bind $Train '/input/train' -ReadOnly) + (New-Bind $Valid '/input/valid' -ReadOnly) +
            (New-Bind $Output '/output') + (New-Bind $Transport '/transport' -ReadOnly)
        Invoke-Runtime 'hunter' $Mounts -Interactive -ExitStatus ([ref]$ExitCode)
    } else {
        Assert-WritableLocation $Working
        Write-Host "Working directory: $Working (container /work). Enter relative paths with forward slashes."
        Invoke-Runtime 'unified' (New-Bind $Working '/work') -Interactive -ExitStatus ([ref]$ExitCode)
    }
} catch {
    Write-Host "DGDTL launcher: $($_.Exception.Message)" -ForegroundColor Red
    $ExitCode = 1
} finally {
    if ($TemporaryRoot -and (Test-Path -LiteralPath $TemporaryRoot)) {
        Remove-Item -LiteralPath $TemporaryRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
exit $ExitCode
