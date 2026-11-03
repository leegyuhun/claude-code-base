# =============================================================================
# clone_claude_template.ps1
#   Pull the latest Claude Code template into the current working tree (works
#   from any branch) and run setup. Which branch is the template, which paths
#   it owns and which paths hold work records is NOT hard-coded here: it comes
#   from clone_claude_template.json next to this script (project-owned).
#
#   Usage:
#     clone_claude_template.bat              -> menu (skipped when only one template)
#     clone_claude_template.bat <name>       -> no menu (name from the json; a number also works)
#     powershell -File clone_claude_template.ps1 -Template <name> [-Config <path>]
#
#   Config (clone_claude_template.json):
#     remote       : git remote that holds the template branch (default "origin")
#     default      : template name used when nothing is chosen
#     mirrorDirs   : template-owned ACTIVE dirs, mirrored EXACTLY (local extras removed)
#     mirrorFiles  : template-owned single files, same rule
#     templates.<name>:
#       branch     : template branch name (any Unicode is fine - the json is UTF-8)
#       paths      : paths taken from the template commit (checkout)
#       fillOnly   : work-record paths under `paths` - 3-way filled, never pruned
#       localOnly  : filled once when missing, never updated afterwards
#       detectPath : optional - if HEAD tracks this path, this template becomes the default
#       runSetup   : run setup_claude.bat after sync
#
#   Design notes:
#   - This file is pure ASCII on purpose. Non-ASCII branch names and paths come
#     from the json and are never typed here, so the .ps1 has no encoding hazard.
#   - We NEVER pass the branch name to git as an argument. We list remote refs
#     and match the name in memory, then drive git by the resolved commit hash.
#   - Without a console (stdin redirected, e.g. run by an agent) the menu is
#     skipped and the default is used.
#   - build-specific files and .gitignore are intentionally left alone;
#     setup_claude.bat repairs ignore rules on its own (.git/info/exclude).
#   - FillOnly paths hold work records, not template (e.g. .claude/harness.json
#     that PHASE 4.5 filled for THIS project). A local file is never overwritten
#     when it differs from the last synced version, so un-promoted local state
#     survives a re-sync. Missing files are added; files you did not touch are
#     updated to the source version; nothing is deleted.
#   - LocalOnly files are filled once when missing and never updated afterwards.
#   - .claude/.template-base records "<template> <commit>" of the last sync.
#     It is the 3-way base for the fill pass above.
#   - ACTIVE_ISSUE: if it already exists in the current tree it is PRESERVED
#     (the current issue pointer wins); if absent, the template copy is taken.
#   - Untracked local files (e.g. .claude/settings.local.json with your API
#     keys) are not tracked, so git checkout never touches them.
#   - Deletions ARE mirrored: (1) files the source branch itself once tracked
#     and later deleted (its history), and (2) EXACT mirror of mirrorDirs /
#     mirrorFiles - extras there are removed even if they came from another
#     template. Switching template therefore swaps those areas completely.
#     FillOnly paths are never pruned. A full backup is taken first.
# =============================================================================

param(
    [string]$Template = '',
    [string]$Config = ''
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Fail([string]$m) { Write-Host "[ERROR] $m" -ForegroundColor Red; exit 1 }
function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }

# Default template-owned ACTIVE areas, mirrored EXACTLY (local extras are removed).
# A stray file here changes Claude Code behavior, so it must match the source.
# Passive dirs (scripts, refs, tests, project-specific data) are NOT listed:
# they only lose files the source branch itself deleted (history pass).
$DefaultMirrorDirs  = @('.claude/agents', '.claude/commands', '.claude/hooks', '.claude/rules', '.claude/skills', '.claude/templates')
$DefaultMirrorFiles = @('.claude/settings.json')

# ---- 0. Load config ---------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($Config)) { $Config = Join-Path $PSScriptRoot 'clone_claude_template.json' }
if (-not (Test-Path -LiteralPath $Config -PathType Leaf)) {
    Fail "Config not found: $Config  (copy clone_claude_template.json next to this script and set the template branch)"
}
try {
    $cfg = Get-Content -Raw -LiteralPath $Config -Encoding UTF8 | ConvertFrom-Json
} catch {
    Fail "Config is not valid JSON: $Config ($($_.Exception.Message))"
}
if ($null -eq $cfg.templates) { Fail "Config has no 'templates' section: $Config" }

function Get-List($v) { if ($null -eq $v) { return @() } else { return @($v | ForEach-Object { [string]$_ }) } }

$Remote      = if ([string]::IsNullOrWhiteSpace($cfg.remote)) { 'origin' } else { [string]$cfg.remote }
$ActiveDirs  = if ($null -eq $cfg.mirrorDirs)  { $DefaultMirrorDirs }  else { Get-List $cfg.mirrorDirs }
$ActiveFiles = if ($null -eq $cfg.mirrorFiles) { $DefaultMirrorFiles } else { Get-List $cfg.mirrorFiles }

$Templates = [ordered]@{}
foreach ($p in $cfg.templates.PSObject.Properties) {
    $t = $p.Value
    if ([string]::IsNullOrWhiteSpace($t.branch)) { Fail "Template '$($p.Name)' has no 'branch'." }
    $Templates[$p.Name] = @{
        Branch      = [string]$t.branch
        Paths       = Get-List $t.paths
        FillOnly    = Get-List $t.fillOnly
        LocalOnly   = Get-List $t.localOnly
        DetectPath  = if ($null -eq $t.detectPath) { '' } else { [string]$t.detectPath }
        MirrorDirs  = $ActiveDirs
        MirrorFiles = $ActiveFiles
        RunSetup    = if ($null -eq $t.runSetup) { $true } else { [bool]$t.runSetup }
    }
    if ($Templates[$p.Name].Paths.Count -eq 0) { Fail "Template '$($p.Name)' has no 'paths'." }
}
$Names = @($Templates.Keys)
if ($Names.Count -eq 0) { Fail "Config defines no templates." }

# True when $rel is one of $roots or lies under one of them.
function Test-Under([string]$rel, [string[]]$roots) {
    foreach ($r in $roots) {
        if ($rel -ieq $r -or $rel.StartsWith("$r/", [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

# path -> blob id of every file under $paths in commit $rev (empty map if none).
function Get-TreeBlobs([string]$rev, [string[]]$paths) {
    $map = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
    if ([string]::IsNullOrWhiteSpace($rev) -or $paths.Count -eq 0) { return ,$map }
    foreach ($line in (& git -c core.quotePath=false ls-tree -r $rev -- $paths)) {
        $tab = $line.IndexOf("`t")
        if ($tab -lt 0) { continue }
        $meta = $line.Substring(0, $tab) -split ' '
        if ($meta.Count -ge 3 -and $meta[1] -eq 'blob') { $map[$line.Substring($tab + 1)] = $meta[2] }
    }
    return ,$map
}

# path -> blob id the file would have if added now (clean filters / autocrlf
# applied, so an untouched checkout hashes to its tree blob). Missing = absent.
function Get-LocalBlobs([string[]]$rels) {
    $map = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
    $present = @($rels | Where-Object { Test-Path -LiteralPath (Join-Path $root $_) -PathType Leaf })
    # Paths go as arguments in chunks (not via a stdin pipe: Windows PowerShell
    # may prepend a BOM to piped text, which would shift every hash by one).
    for ($s = 0; $s -lt $present.Count; $s += 150) {
        $chunk  = @($present[$s..([Math]::Min($s + 149, $present.Count - 1))])
        $hashes = @(& git hash-object -- $chunk)
        if ($hashes.Count -ne $chunk.Count) { Fail "git hash-object returned $($hashes.Count) hash(es) for $($chunk.Count) file(s)." }
        for ($i = 0; $i -lt $chunk.Count; $i++) { $map[$chunk[$i]] = $hashes[$i] }
    }
    return ,$map
}

# Write blob $oid to $path byte-exact (cmd redirection: PowerShell would re-encode).
function Save-Blob([string]$oid, [string]$path) {
    & cmd.exe /c "git cat-file blob $oid > `"$path`""
    return ($LASTEXITCODE -eq 0)
}

# 3-way merge of a work record changed on both sides. On a clean merge the
# local file is rewritten with the result (keeping its CRLF/LF style) and $true
# is returned; on conflict or error the local file is left untouched.
function Merge-WorkRecord([string]$rel, [string]$baseOid, [string]$srcOid) {
    $full = Join-Path $root $rel
    $tmp  = Join-Path ([System.IO.Path]::GetTempPath()) ("clone_claude_merge_" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    try {
        $raw = [System.IO.File]::ReadAllBytes($full)
        if ([Array]::IndexOf($raw, [byte]0) -ge 0) { return $false }
        # Clean the local copy through git (autocrlf) so it compares with the blobs.
        $locOid = (& git hash-object -w "--path=$rel" -- $full) -join ''
        $pl = Join-Path $tmp 'local'; $pb = Join-Path $tmp 'base'; $pr = Join-Path $tmp 'source'
        if (-not ((Save-Blob $locOid $pl) -and (Save-Blob $baseOid $pb) -and (Save-Blob $srcOid $pr))) { return $false }
        & git merge-file -q $pl $pb $pr
        if ($LASTEXITCODE -ne 0) { return $false }
        $out = [System.IO.File]::ReadAllBytes($pl)
        $crlf = ([System.Text.Encoding]::ASCII.GetString($raw)).Contains("`r`n")
        if ($crlf) {
            $txt = [System.Text.Encoding]::GetEncoding(28591).GetString($out)   # byte-transparent
            $txt = ($txt -replace "`r`n", "`n") -replace "`n", "`r`n"
            $out = [System.Text.Encoding]::GetEncoding(28591).GetBytes($txt)
        }
        [System.IO.File]::WriteAllBytes($full, $out)
        return $true
    } finally {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Template name from user input: exact name (case-insensitive) or 1-based number.
function Resolve-TemplateName([string]$v) {
    $v = $v.Trim()
    if ([string]::IsNullOrWhiteSpace($v)) { return $null }
    foreach ($n in $Names) { if ($n -ieq $v) { return $n } }
    $idx = 0
    if ([int]::TryParse($v, [ref]$idx) -and $idx -ge 1 -and $idx -le $Names.Count) { return $Names[$idx - 1] }
    return $null
}

# ---- 1. Locate repo root ----------------------------------------------------
$root = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
    Fail "Not inside a git repository."
}
Set-Location -LiteralPath $root
Info "[1/7] Repo root: $root"

# ---- 1b. Choose template ----------------------------------------------------
$branchName = (& git rev-parse --abbrev-ref HEAD 2>$null)

# Default: the config's "default", unless a template's detectPath is tracked by HEAD.
$default = $null
foreach ($n in $Names) {
    $dp = $Templates[$n].DetectPath
    if ([string]::IsNullOrWhiteSpace($dp)) { continue }
    $hit = & git ls-tree --name-only HEAD -- $dp
    if (-not [string]::IsNullOrWhiteSpace(($hit -join ''))) { $default = $n; break }
}
if ($null -eq $default) {
    $default = Resolve-TemplateName ([string]$cfg.default)
    if ($null -eq $default) { $default = $Names[0] }
}

$interactive = $true
try { if ([Console]::IsInputRedirected) { $interactive = $false } } catch {}
if (-not [Environment]::UserInteractive) { $interactive = $false }

$chosen = $null
if (-not [string]::IsNullOrWhiteSpace($Template)) {
    $chosen = Resolve-TemplateName $Template
    if ($null -eq $chosen) { Fail "Unknown template '$Template'. Use one of: $($Names -join ' | ')" }
} elseif ($Names.Count -eq 1) {
    $chosen = $Names[0]
} elseif ($interactive) {
    Write-Host ''
    Write-Host 'Select Claude Code template:'
    for ($i = 0; $i -lt $Names.Count; $i++) {
        Write-Host ("  {0}. {1,-12} ({2})" -f ($i + 1), $Names[$i], $Templates[$Names[$i]].Branch)
    }
    Write-Host "  default: $default   (current branch: $branchName)" -ForegroundColor DarkGray
    while ($null -eq $chosen) {
        $ans = Read-Host "Enter = $default, or a number/name"
        if ([string]::IsNullOrWhiteSpace($ans)) { $chosen = $default } else { $chosen = Resolve-TemplateName $ans }
        if ($null -eq $chosen) { Warn "Type a number 1-$($Names.Count) or a template name (or press Enter)." }
    }
} else {
    $chosen = $default
    Warn "No console input - menu skipped, using default template: $chosen"
}

if ($chosen -ne $default -and $Names.Count -gt 1) {
    Warn "Current branch '$branchName' usually uses '$default', but '$chosen' was selected."
    Warn "The active template areas ($($ActiveDirs -join ', ')) will be swapped."
    if ($interactive -and [string]::IsNullOrWhiteSpace($Template)) {
        $ok = $null
        while ($null -eq $ok) {
            $a = (Read-Host 'Continue? (1. Yes / 2. No)').Trim().ToLowerInvariant()
            if ($a -in @('1', 'y', 'yes')) { $ok = $true } elseif ($a -in @('2', 'n', 'no')) { $ok = $false }
        }
        if (-not $ok) { Write-Host 'Cancelled.'; exit 1 }
    }
}

$T           = $Templates[$chosen]
$SrcBranch   = $T.Branch
$TargetRef   = "$Remote/$SrcBranch"
$Paths       = $T.Paths
$FillOnly    = $T.FillOnly
$LocalOnly   = $T.LocalOnly
$MirrorDirs  = $T.MirrorDirs
$MirrorFiles = $T.MirrorFiles
Info "      Template: $chosen  ($TargetRef)"

# ---- 2. Fetch latest (branch name never passed as an argument) --------------
Info "[2/7] Fetching '$Remote' ..."
# Do NOT redirect git's stderr (2>&1): git writes progress there, and under
# $ErrorActionPreference='Stop' a redirected native stderr line is wrapped as a
# terminating NativeCommandError even on a successful fetch. Let it stream to
# the console untouched and judge success by $LASTEXITCODE only.
& git fetch $Remote --prune
if ($LASTEXITCODE -ne 0) {
    Warn "fetch failed - falling back to local remote-tracking refs if available."
}

# ---- 3. Resolve source commit by matching ref name in memory ----------------
$rows = & git -c core.quotePath=false for-each-ref "refs/remotes/$Remote" "refs/heads" --format='%(objectname)|%(refname:short)'
$hash = $null
foreach ($r in $rows) {
    $parts = $r -split '\|', 2
    if ($parts.Count -eq 2 -and $parts[1] -eq $TargetRef) { $hash = $parts[0]; break }
}
if ([string]::IsNullOrWhiteSpace($hash)) {
    # Local branch fallback (template branch exists only locally, e.g. the template repo itself).
    foreach ($r in $rows) {
        $parts = $r -split '\|', 2
        if ($parts.Count -eq 2 -and $parts[1] -eq $SrcBranch) { $hash = $parts[0]; $TargetRef = $SrcBranch; break }
    }
}
if ([string]::IsNullOrWhiteSpace($hash)) {
    Fail "Source branch '$TargetRef' not found on remote '$Remote' (nor locally). (fetch ok? branch name in clone_claude_template.json correct?)"
}
Info "[3/7] Source: $TargetRef @ $($hash.Substring(0, [Math]::Min(10, $hash.Length)))"

# Last synced commit of the SAME template = 3-way base (see header).
$baseFile     = Join-Path $root '.claude/.template-base'
$overrideFile = Join-Path $root '.claude/.template-base-conflicts'   # "<path>`t<base blob>" per line
$baseHash     = $null
if (Test-Path -LiteralPath $baseFile) {
    $bparts = ((Get-Content -Raw -LiteralPath $baseFile) -replace '\s+', ' ').Trim() -split ' '
    if ($bparts.Count -ge 2 -and $bparts[0] -eq $chosen) {
        $ok = & git rev-parse -q --verify "$($bparts[1])^{commit}"
        if (-not [string]::IsNullOrWhiteSpace(($ok -join ''))) { $baseHash = $bparts[1] }
    }
}
if ($null -ne $baseHash) {
    Info "      Base  : last sync @ $($baseHash.Substring(0, [Math]::Min(10, $baseHash.Length)))"
} else {
    Info "      Base  : none (first sync of '$chosen' here) - work records are only filled, never updated."
}

# Local template edits that the checkout below will overwrite (they are in the
# backup, but they should have been promoted to the template branch first).
if ($null -ne $baseHash) {
    $tplBase  = Get-TreeBlobs $baseHash $Paths
    $tplRels  = @($tplBase.Keys | Where-Object { -not (Test-Under $_ ($FillOnly + $LocalOnly)) })
    $tplLocal = Get-LocalBlobs $tplRels
    # Edited since the base AND different from the source (already promoted = no loss).
    $tplSrc   = Get-TreeBlobs $hash $Paths
    $edited   = @($tplRels | Where-Object {
        $tplLocal.ContainsKey($_) -and $tplLocal[$_] -ne $tplBase[$_] -and
        -not ($tplSrc.ContainsKey($_) -and $tplSrc[$_] -eq $tplLocal[$_]) })
    # Files you added in the mirrored areas: the mirror pass would remove them.
    foreach ($md in $MirrorDirs) {
        $mdFull = Join-Path $root $md
        if (-not (Test-Path -LiteralPath $mdFull -PathType Container)) { continue }
        $prefix = (Resolve-Path -LiteralPath $root).Path.TrimEnd('\') + '\'
        Get-ChildItem -LiteralPath $mdFull -File -Recurse -Force | ForEach-Object {
            $rel = $_.FullName.Substring($prefix.Length) -replace '\\', '/'
            if (-not $tplBase.ContainsKey($rel) -and -not $tplSrc.ContainsKey($rel)) { $edited += "$rel  (new)" }
        }
    }
    if ($edited.Count -gt 0) {
        Warn "$($edited.Count) locally edited template file(s) will be overwritten (kept in the backup):"
        $edited | Select-Object -First 20 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
        if ($edited.Count -gt 20) { Write-Host "    ... and $($edited.Count - 20) more" -ForegroundColor Yellow }
        Warn "Promote them to the template branch first if they should be kept."
        if ($interactive) {
            $go = $null
            while ($null -eq $go) {
                $a = (Read-Host 'Overwrite and continue? (1. Yes / 2. No)').Trim().ToLowerInvariant()
                if ($a -in @('1', 'y', 'yes')) { $go = $true } elseif ($a -in @('2', 'n', 'no')) { $go = $false }
            }
            if (-not $go) { Write-Host 'Cancelled.'; exit 1 }
        }
    }
}

# ---- 4. Backup current template files --------------------------------------
$ts  = Get-Date -Format 'yyyyMMdd_HHmmss'
$bak = Join-Path $root ".claude_template_backup_$ts"

# Make sure backup dirs are ignored (repo-local) before we create them.
# Resolve via --git-path: in a linked worktree '.git' is a FILE, so a literal
# '.git/info/exclude' does not exist there.
$giRel = (& git rev-parse --git-path info/exclude)
if ([System.IO.Path]::IsPathRooted($giRel)) { $gi = $giRel } else { $gi = Join-Path $root $giRel }
$pat = '/.claude_template_backup_*/'
if (Test-Path -LiteralPath $gi) {
    $giLines = Get-Content -LiteralPath $gi
    if ($giLines -notcontains $pat) {
        Add-Content -LiteralPath $gi -Value ''
        Add-Content -LiteralPath $gi -Value '# Claude template sync backups (clone_claude_template)'
        Add-Content -LiteralPath $gi -Value $pat
    }
}

$existing = $Paths | Where-Object { Test-Path -LiteralPath (Join-Path $root $_) }
if ($existing) {
    New-Item -ItemType Directory -Force -Path $bak | Out-Null
    foreach ($it in $existing) {
        Copy-Item -LiteralPath (Join-Path $root $it) -Destination $bak -Recurse -Force
    }
    Info "[4/7] Backup created: $bak"
} else {
    Info "[4/7] No existing template files found - skipping backup."
    $bak = '(none)'
}

# ---- 5. Preserve ACTIVE_ISSUE, then checkout template ----------------------
$activePath = Join-Path $root '.claude/ACTIVE_ISSUE'
$activeKeep = $null
if (Test-Path -LiteralPath $activePath) {
    $activeKeep = Get-Content -Raw -LiteralPath $activePath
}

# Checkout only the paths that actually exist on the source commit, so a
# missing optional path does not abort the whole operation.
# Existence check uses 'ls-tree' output (empty = absent). It never writes to
# stderr for a missing path, so there is no NativeCommandError-under-Stop
# hazard (a redirected 'cat-file -e ... 2>$null' throws in Windows PowerShell).
# FillOnly paths nested in a checked-out path are excluded here (fill below).
foreach ($p in $Paths) {
    $found = & git -c core.quotePath=false ls-tree --name-only $hash -- $p
    if (-not [string]::IsNullOrWhiteSpace(($found -join ''))) {
        $spec = @($p)
        foreach ($f in $FillOnly) { if ($f.StartsWith("$p/")) { $spec += ":(exclude)$f" } }
        # No 2>&1 here either: same NativeCommandError-under-Stop hazard as fetch.
        & git checkout $hash -- $spec
        if ($LASTEXITCODE -ne 0) { Warn "checkout of '$p' failed (skipped)." }
    } else {
        Warn "'$p' not present on source branch - skipped."
    }
}

# Fill pass for work records (3-way against the last synced base):
#   missing locally            -> add
#   local == base, src changed -> update (you did not touch it)
#   local != base, src same    -> keep yours
#   local != base, src changed -> 3-way merge into your file; keep yours and
#                                 report a conflict when it does not merge
#   LocalOnly                  -> add when missing, otherwise never touched
# Nothing is ever deleted here.
$filled = 0; $updated = 0; $merged = 0; $keptLocal = 0
$conflicts = @()
if ($FillOnly.Count -gt 0) {
    $srcBlobs  = Get-TreeBlobs $hash $FillOnly
    $baseBlobs = Get-TreeBlobs $baseHash $FillOnly
    # Unresolved conflicts from earlier syncs keep their OWN base blob, so
    # advancing .template-base never makes the other side look like yours.
    if ($null -ne $baseHash -and (Test-Path -LiteralPath $overrideFile)) {
        foreach ($ln in [System.IO.File]::ReadAllLines($overrideFile)) {
            $kv = $ln -split "`t"
            if ($kv.Count -eq 2 -and $kv[1] -match '^[0-9a-f]{40}$') { $baseBlobs[$kv[0]] = $kv[1] }
        }
    }
    $locBlobs  = Get-LocalBlobs @($srcBlobs.Keys)
    $take = New-Object 'System.Collections.Generic.List[string]'
    foreach ($f in $srcBlobs.Keys) {
        $r = $srcBlobs[$f]
        if (-not $locBlobs.ContainsKey($f)) { $take.Add(":(literal)$f"); $filled++; continue }
        $l = $locBlobs[$f]
        if ($l -eq $r) { continue }
        if (Test-Under $f $LocalOnly) { continue }
        if ($baseBlobs.ContainsKey($f) -and $l -eq $baseBlobs[$f]) { $take.Add(":(literal)$f"); $updated++; continue }
        if ($baseBlobs.ContainsKey($f) -and $r -ne $baseBlobs[$f]) {
            # Changed on both sides: fold the source side in.
            if (Merge-WorkRecord $f $baseBlobs[$f] $r) { $merged++ } else { $keptLocal++; $conflicts += $f }
            continue
        }
        $keptLocal++
    }
    if ($take.Count -gt 0) {
        $specFile = Join-Path ([System.IO.Path]::GetTempPath()) "clone_claude_fill_$ts.txt"
        [System.IO.File]::WriteAllLines($specFile, $take, (New-Object System.Text.UTF8Encoding($false)))
        & git checkout $hash "--pathspec-from-file=$specFile"
        if ($LASTEXITCODE -ne 0) { Warn "fill of work-record paths failed (skipped)."; $filled = 0; $updated = 0 }
        Remove-Item -LiteralPath $specFile -Force -ErrorAction SilentlyContinue
    }
}

# Mirror deletions (two passes, both case-insensitive: on Windows a
# case-only rename must not delete the live file).
$srcSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($f in (& git -c core.quotePath=false ls-tree -r --name-only $hash -- $Paths)) { [void]$srcSet.Add($f) }
$removed = @()

# Never walk up past these when pruning empty dirs.
$KeepDirs = $Paths + $MirrorDirs + $FillOnly

function Remove-SyncedFile([string]$rel) {
    $full = Join-Path $root $rel
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { return }
    Remove-Item -LiteralPath $full -Force
    $script:removed += $rel
    # Drop now-empty parent dirs, but never a top-level synced path or a
    # mirrored template dir itself.
    $dir = Split-Path -Parent $full
    while ($dir -and ($dir.Length -gt $root.Length) -and
           ($KeepDirs -notcontains ($dir.Substring($root.Length).TrimStart('\', '/') -replace '\\', '/')) -and
           (Test-Path -LiteralPath $dir) -and
           -not (Get-ChildItem -LiteralPath $dir -Force | Select-Object -First 1)) {
        Remove-Item -LiteralPath $dir -Force
        $dir = Split-Path -Parent $dir
    }
}

# Pass 1 - history: files the source branch once tracked under $Paths and
# later deleted (--no-renames so a rename shows as delete+add), minus anything
# still present in the source tree. Covers passive dirs (scripts, refs, ...).
# FillOnly paths (work records) are never pruned.
$delHist = & git -c core.quotePath=false log --no-renames --diff-filter=D --name-only --format= $hash -- $Paths
foreach ($d in ($delHist | Where-Object { $_ } | Sort-Object -Unique)) {
    if ($srcSet.Contains($d)) { continue }
    if ($d -ieq '.claude/ACTIVE_ISSUE') { continue }
    if (Test-Under $d $FillOnly) { continue }
    Remove-SyncedFile $d
}

# Pass 2 - exact mirror of template-owned ACTIVE areas. Anything in these
# dirs/files that the source tree does not have is removed, even if it never
# came from this branch (e.g. leftovers from another template). These are the
# places where a stray file changes behavior (a hook, a command, an agent, a
# rule, a settings.json registering hooks). Local-only files live elsewhere
# (settings.local.json, ACTIVE_ISSUE, harness.json, project data dirs, ...).
# Guard: skip entirely if the source listing came back empty.
if ($srcSet.Count -gt 0) {
    foreach ($md in $MirrorDirs) {
        $mdFull = Join-Path $root $md
        if (-not (Test-Path -LiteralPath $mdFull -PathType Container)) { continue }
        $prefix = (Resolve-Path -LiteralPath $root).Path.TrimEnd('\') + '\'
        # Snapshot the listing BEFORE deleting anything. Streaming it through
        # the pipeline would let Remove-SyncedFile prune an emptied subdir
        # (e.g. hooks/__pycache__) while the recursive walk is still about to
        # enter it -> DirectoryNotFound, fatal under ErrorActionPreference=Stop.
        $mdFiles = @(Get-ChildItem -LiteralPath $mdFull -File -Recurse -Force)
        foreach ($f in $mdFiles) {
            $rel = $f.FullName.Substring($prefix.Length) -replace '\\', '/'
            if (-not $srcSet.Contains($rel)) { Remove-SyncedFile $rel }
        }
    }
    foreach ($mf in $MirrorFiles) {
        if (-not $srcSet.Contains($mf)) { Remove-SyncedFile $mf }
    }
}

# Capture the synced changes while they are STILL STAGED. After the reset
# below the paths become untracked, and if ignore rules already hide them
# (e.g. a repeat run, or a from-scratch sync into a tree that ignores
# /.claude/) a plain 'git status' would hide them - falsely reporting
# "no changes" even when 1000+ files were just laid down. Staged status/diff
# is immune to ignore rules, so we snapshot here and print it in step 6.
$SyncedPaths  = $Paths + $FillOnly
$changedShort = & git -c core.quotePath=false status --short -- $SyncedPaths
$changedStat  = & git --no-pager -c core.quotePath=false diff --cached --stat -- $SyncedPaths

# Unstage the synced template so it lands as untracked + ignored. This keeps
# the standard across branch switches without ever being committed into a
# working branch. On a branch that TRACKS these paths (the template branch
# itself) the reset just leaves them as ordinary working-tree changes.
foreach ($p in $SyncedPaths) { & git reset -q -- $p 2>$null }
& git reset -q -- clone_claude_template.bat clone_claude_template.ps1 clone_claude_template.json 2>$null

if ($null -ne $activeKeep) {
    # Restore the pre-existing ACTIVE_ISSUE and unstage it (current pointer wins).
    Set-Content -LiteralPath $activePath -Value $activeKeep -NoNewline
    & git reset -q -- $activePath 2>$null
    Info "[5/7] ACTIVE_ISSUE preserved (kept your current issue pointer)."
} else {
    Info "[5/7] ACTIVE_ISSUE taken from template (none existed locally)."
}

# ---- 6. Show what was synced (snapshot taken pre-reset, while staged) -------
Info "[6/7] Changes synced from '$TargetRef':"
if ([string]::IsNullOrWhiteSpace(($changedShort -join "`n"))) {
    Write-Host "  (no changes - working tree already matched the template)" -ForegroundColor DarkGray
} else {
    $changedShort | ForEach-Object { Write-Host "  $_" }
    Write-Host "  legend (staged): 'A' new file, 'M' modified, 'D' deleted" -ForegroundColor DarkGray
    Write-Host ''
    Write-Host "  --- line-level diff (staged vs HEAD) ---" -ForegroundColor DarkGray
    $changedStat | Out-Host
}
if ($FillOnly.Count -gt 0) {
    Write-Host ''
    Write-Host "  --- work records ($($FillOnly -join ', ')): $filled added, $updated updated, $merged merged, $keptLocal local edit(s) kept ---" -ForegroundColor DarkGray
    if ($conflicts.Count -gt 0) {
        Warn "$($conflicts.Count) work record(s) changed BOTH locally and on the source - your version was kept:"
        $conflicts | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
        Warn "Merge them by hand (compare with: git show ${TargetRef}:<path>). Their old base is kept in"
        Warn ".claude/.template-base-conflicts so the next sync still treats them as conflicts, not as yours."
    }
}
if ($removed.Count -gt 0) {
    Write-Host ''
    Write-Host "  --- removed (not in source template): $($removed.Count) file(s) ---" -ForegroundColor DarkGray
    $removed | ForEach-Object { Write-Host "  - $_" }
}

# Record the new base (3-way base for the next sync's fill pass).
if (Test-Path -LiteralPath (Join-Path $root '.claude') -PathType Container) {
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($baseFile, "$chosen $hash`r`n", $utf8)
    if ($conflicts.Count -gt 0) {
        [System.IO.File]::WriteAllLines($overrideFile, [string[]]@($conflicts | ForEach-Object { "$_`t$($baseBlobs[$_])" }), $utf8)
    } elseif (Test-Path -LiteralPath $overrideFile) {
        Remove-Item -LiteralPath $overrideFile -Force
    }
}

# ---- 7. Apply (run setup_claude.bat) ---------------------------------------
$setup = Join-Path $root 'setup_claude.bat'
if (-not $T.RunSetup) {
    Info "[7/7] '$chosen' template has no setup step - skipped."
} elseif (Test-Path -LiteralPath $setup) {
    Info "[7/7] Running setup_claude.bat ..."
    & cmd.exe /c "`"$setup`""
    Info "Setup finished (exit $LASTEXITCODE)."
} else {
    Warn "[7/7] setup_claude.bat not found - apply step skipped."
}

Write-Host ''
Write-Host "Done. Claude Code template '$chosen' synced from $TargetRef." -ForegroundColor Green
Write-Host "  Backup : $bak"
Write-Host "  Removed: $($removed.Count) file(s) not in the source template were removed locally."
Write-Host "  Note   : synced files are left UNSTAGED (untracked/ignored on work branches)."
Write-Host "           To undo, restore from the backup folder above."
exit 0
