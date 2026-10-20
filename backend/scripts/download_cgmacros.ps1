param(
    [string]$Destination = "../../data/raw/cgmacros",
    [ValidateRange(1, 120)][int]$MaxTransferMinutes = 15
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Target = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $Destination))
New-Item -ItemType Directory -Force -Path $Target | Out-Null
$Url = "https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip"
$Archive = Join-Path $Target "CGMacros_dateshifted365.zip"
$Partial = "$Archive.partial"
$Extracted = Join-Path $Target "extracted"
$ExpectedSha256 = "05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d"
$Curl = (Get-Command curl.exe -ErrorAction Stop).Source

# Preserve a previous interrupted download and resume from its byte offset. curl retries
# transient failures and shows transfer progress. The release is pinned by its official
# PhysioNet SHA256SUMS.txt entry (see docs/DATA_PROVENANCE.md).
$ArchiveAlreadyVerified = $false
if (Test-Path -LiteralPath $Archive) {
    $archiveHash = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archiveHash -eq $ExpectedSha256) { $ArchiveAlreadyVerified = $true }
    else {
        if (-not (Test-Path -LiteralPath $Partial) -and (Get-Item -LiteralPath $Archive).Length -lt 657187340) {
            Move-Item -LiteralPath $Archive -Destination $Partial
        } else {
            $unverified = "$Archive.unverified-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Move-Item -LiteralPath $Archive -Destination $unverified
            Write-Warning "Preserved an existing unverified archive as $unverified."
        }
    }
}

function Invoke-ArchiveDownload([switch]$Resume) {
    $maxSeconds = $MaxTransferMinutes * 60
    $arguments = @("--fail", "--location", "--retry", "2", "--retry-all-errors", "--retry-delay", "5", "--retry-max-time", "60", "--max-time", "$maxSeconds", "--connect-timeout", "30", "--speed-limit", "1024", "--speed-time", "120", "--progress-bar")
    if ($Resume) { $arguments += @("--continue-at", "-") }
    $arguments += @("--output", $Partial, $Url)
    & $Curl @arguments
    if ($LASTEXITCODE -ne 0) { throw "curl failed with exit code $LASTEXITCODE; partial bytes were retained for a later resume." }
}

if (-not $ArchiveAlreadyVerified) {
    if (-not (Test-Path -LiteralPath $Partial) -or (Get-Item -LiteralPath $Partial).Length -eq 0) {
        Invoke-ArchiveDownload
    } else {
        # A transient failure must not discard a large resumable partial or silently
        # restart from byte zero. curl's retries are bounded above; rerun this script
        # later to continue from the retained offset.
        Invoke-ArchiveDownload -Resume
    }
}

$candidate = if ($ArchiveAlreadyVerified) { $Archive } else { $Partial }
$actualSha256 = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualSha256 -ne $ExpectedSha256) {
    # If the server ignored a Range request, the resumed file may be duplicated/corrupt.
    # Preserve it for inspection and perform one clean download into a fresh partial file.
    if ((Get-Item -LiteralPath $candidate).Length -lt 657187340) {
        throw "Archive is incomplete (SHA-256 $actualSha256); partial bytes retained. Re-run this script to resume."
    }
    $bad = "$candidate.invalid-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Move-Item -LiteralPath $candidate -Destination $bad
    Write-Warning "Completed transfer did not match the pinned SHA-256; preserved it as $bad and restarting cleanly."
    Invoke-ArchiveDownload
    $actualSha256 = (Get-FileHash -LiteralPath $Partial -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualSha256 -ne $ExpectedSha256) { throw "Fresh archive failed SHA-256 verification ($actualSha256); it will not be extracted." }
}

if ($actualSha256 -ne $ExpectedSha256) { throw "Archive has not reached the official checksum; it will not be extracted." }
$candidate = if ($ArchiveAlreadyVerified) { $Archive } else { $Partial }
$zip = [System.IO.Compression.ZipFile]::OpenRead($candidate)
try {
    if ($zip.Entries.Count -eq 0) { throw "Verified archive contains no entries." }
} finally { $zip.Dispose() }

if (-not $ArchiveAlreadyVerified) { Move-Item -LiteralPath $Partial -Destination $Archive }
$VerificationMarker = Join-Path $Target "verified.sha256"
if (Test-Path -LiteralPath $VerificationMarker) {
    $existingMarker = (Get-Content -LiteralPath $VerificationMarker -Raw).Trim().ToLowerInvariant()
    if ($existingMarker -ne $ExpectedSha256) { throw "Existing verification marker differs from the pinned release; it was preserved at $VerificationMarker." }
} else {
    $ExpectedSha256 | Set-Content -LiteralPath $VerificationMarker -NoNewline -Encoding ascii
}
if (Test-Path -LiteralPath $Extracted) {
    Write-Host "Archive verified. Existing extracted directory preserved at $Extracted; no files were overwritten."
    return
}
$Staging = Join-Path $Target (".extract-" + [guid]::NewGuid().ToString("N"))
try {
    Expand-Archive -LiteralPath $Archive -DestinationPath $Staging
    Move-Item -LiteralPath $Staging -Destination $Extracted
} finally {
    if (Test-Path -LiteralPath $Staging) { Remove-Item -LiteralPath $Staging -Recurse -Force }
}
Write-Host "Verified SHA-256 $actualSha256 and extracted to $Extracted. Raw data remains gitignored."
