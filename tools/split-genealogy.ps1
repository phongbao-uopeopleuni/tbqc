$src = Join-Path $PSScriptRoot "..\templates\genealogy.html" | Resolve-Path
$lines = Get-Content -LiteralPath $src -Encoding UTF8
$out = Join-Path $PSScriptRoot "..\templates\genealogy\partials"
if (!(Test-Path $out)) { New-Item -ItemType Directory -Path $out -Force | Out-Null }

function Write-Slice([string]$relPath, [int]$start, [int]$end) {
  $path = Join-Path $out $relPath
  $slice = $lines[($start - 1)..($end - 1)]
  $text = ($slice -join "`n") + "`n"
  [System.IO.File]::WriteAllText($path, $text, [System.Text.UTF8Encoding]::new($false))
}

Write-Slice "_head.html" 1 2300
# Skip line 2301 (<body>) — thẻ mở nằm trong genealogy.html sau include _head
Write-Slice "_body_nav_gate.html" 2302 2332
Write-Slice "_main_genealogy_content.html" 2333 2765
Write-Slice "_scripts_external_bundle.html" 2766 2794
Write-Slice "_scripts_tree_controls.html" 2795 3329
Write-Slice "_scripts_lineage_ui.html" 3330 4045
Write-Slice "_scripts_member_stats.html" 4046 5766
Write-Slice "_styles_stats_responsive.html" 5767 5780
Write-Slice "_scripts_grave_and_family_view.html" 5781 7188
Write-Slice "_footer_zalo_and_gate_script.html" 7189 7323
Write-Host "Done writing partials to $out"
