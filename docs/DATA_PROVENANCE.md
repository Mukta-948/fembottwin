# Data provenance and access

## CGMacros (primary PoC candidate)

Official record: [PhysioNet CGMacros v1.0.0](https://physionet.org/content/cgmacros/1.0.0/), DOI 10.13026/3z8q-x658. The access policy permits anyone to access files subject to the license; the stated license is [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The archive is `CGMacros_dateshifted365.zip` (627.1 MB; server object length 657,187,340 bytes). The record describes 45 participants: 15 healthy, 16 pre-diabetes, and 14 T2D. The release has participant-specific CSVs, supporting demographic/biomarker tables, and meal photographs. It is free-living, approximately ten days per participant. It does not include menstrual cycle measurements and cannot validate cycle effects. Follow the license attribution, non-commercial, and share-alike terms; do not redistribute raw participant data from this project.

The official v1.0.0 top-level file listing exposes the observation-bearing ZIP as one 657,187,340-byte file; the separately listed small files are dictionaries and documentation, not a smaller participant-observation subset. A dictionary download alone cannot support post-meal model training. The official SHA-256 for the ZIP is `05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d` from the [official checksum list](https://physionet.org/files/cgmacros/1.0.0/SHA256SUMS.txt). No local CSV schema has been observed in this checkout.

Use `backend/scripts/download_cgmacros.ps1` from PowerShell to fetch the official archive and extract under `data/raw/cgmacros/extracted`. It resumes partial transfers with bounded retries/progress (15-minute default transfer cap), verifies the pinned official SHA-256 (`05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d`), validates the ZIP, and stages extraction without overwriting an existing extracted directory. The official SHA-256 list is [PhysioNet SHA256SUMS.txt](https://physionet.org/files/cgmacros/1.0.0/SHA256SUMS.txt). PhysioNet documents resumable `wget -r -N -c -np https://physionet.org/files/cgmacros/1.0.0/` and `aws s3 sync --no-sign-request s3://physionet-open/cgmacros/1.0.0/ DESTINATION` as alternatives.

**Safe recovery for the current slow transfer:** keep `CGMacros_dateshifted365.zip.partial` untouched. One bounded resume attempt was made with the hardened script; after DNS failure in the sandbox, the network-enabled attempt advanced only from 2,088,584 to 2,150,024 bytes (about 0.33%) and was stopped. The partial is still incomplete and unverified. PhysioNet documents the S3 source `s3://physionet-open/cgmacros/1.0.0/`, but AWS CLI is not installed in this environment. Windows BITS cmdlets are available and can resume a persistent transfer. In Windows PowerShell, start it in a *separate temp directory*:

```powershell
$downloadDir = Join-Path $env:TEMP 'FemMetaboTwin-CGMacros'
New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
$url = 'https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip'
$zip = Join-Path $downloadDir 'CGMacros_dateshifted365.zip'
$job = Get-BitsTransfer -Name 'FemMetaboTwin-CGMacros' -ErrorAction SilentlyContinue
if (-not $job) {
  Start-BitsTransfer -Source $url -Destination $zip -DisplayName 'FemMetaboTwin-CGMacros' -Asynchronous -RetryInterval 60 -RetryTimeout 3600 | Out-Null
} elseif ($job.JobState -eq 'Suspended') {
  Resume-BitsTransfer -BitsJob $job -Asynchronous
} else {
  Write-Host "Existing BITS job is $($job.JobState); do not start a duplicate."
}
# Check status; suspend instead of retrying if throughput is unusable.
Get-BitsTransfer -Name 'FemMetaboTwin-CGMacros' | Format-List DisplayName,JobState,BytesTransferred,BytesTotal
```

Once status is `Transferred`, complete the temp-file transfer and verify before copying/extraction:

```powershell
$job = Get-BitsTransfer -Name 'FemMetaboTwin-CGMacros'
if ($job.JobState -ne 'Transferred') { throw "Download incomplete: $($job.JobState); do not extract." }
Complete-BitsTransfer -BitsJob $job
if ((Get-Item -LiteralPath $zip).Length -ne 657187340) { throw 'Unexpected archive size; do not extract.' }
$expected = '05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d'
if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Official SHA-256 mismatch; do not extract.' }
$repo = (Resolve-Path .).Path  # Run these commands from the FemMetaboTwin repository root.
Copy-Item -LiteralPath $zip -Destination (Join-Path $repo 'data/raw/cgmacros/CGMacros_dateshifted365.zip')
& (Join-Path $repo 'backend/scripts/download_cgmacros.ps1')
```

Run the final verification/copy commands from the FemMetaboTwin repository root. The official PhysioNet page also documents `aws s3 sync --no-sign-request 's3://physionet-open/cgmacros/1.0.0/' DESTINATION`; use it only where AWS CLI is already installed. A browser alternative is to save the official PhysioNet ZIP to a separate filename in `$env:TEMP`, set `$zip` to that exact path, then run the same verification and copy commands; never overwrite the partial. Do not extract, inspect, or train from an incomplete/unverified ZIP. Do not commit participant data or meal images; the raw-data directory is gitignored.

The repository partial is 2,150,024 bytes; it remains untouched and has not been extracted or checksum-verified. The existing separate BITS job (`FemMetaboTwin-CGMacros`) was resumed once from 409,600 and progressed to **884,736 of 657,187,340 bytes**, then suspended because the observed rate was too slow for this session. It remains resumable; use the commands above and do not create a duplicate. A prior HTTP Range request returned `206 Partial Content`, confirming resumption support. The current downloader has bounded retries, progress, and a 15-minute default cap. There are no observed local CGMacros columns, participant IDs, timestamps, units, missingness, or meal linkage to report. `inspect_data.py` inventories actual local files and CSV headers, row counts, missing values, candidate fields, and timestamp parse coverage after extraction; mappings must be checked against observed data and the data dictionary. Numeric timestamp units and glucose units are not guessed. The simple model is a research baseline, not a clinical predictor.

## mcPHASES (separate restricted research source)

Official record: [PhysioNet mcPHASES v1.0.0](https://physionet.org/content/mcphases/1.0.0/), DOI 10.13026/zx6a-2c81. The described cohort is 42 young adult menstruators in Canada, with wearable, hormone/self-report, and CGM data in Interval 1. It is **restricted access** under the PhysioNet Restricted Health Data License 1.5.0 and DUA 1.5.0. Access requires a PhysioNet account, credentialing/CITI approval, and acceptance of the dataset DUA. Complete those steps on the official record before downloading. This project does not automate credentialed downloads. If lawfully downloaded, store only in `data/restricted/`, which is gitignored.

mcPHASES is not a T2D cohort; do not pool its participants with CGMacros. It may support a separately evaluated research exploration of cycle labels and glucose, subject to access terms, ethics, and cohort limitations. It does not establish personalized menstrual-cycle effects for women with T2D. This app currently has no cycle model.
