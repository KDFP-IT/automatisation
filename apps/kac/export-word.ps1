param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [Parameter(Mandatory = $true)][string]$Pdf,
    [string]$Report
)

$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$discardChanges = 0
try {
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $readOnly = -not $Report
    $confirmConversion = $false
    $addToRecentFiles = $false
    $document = $word.Documents.Open([ref]$Docx, [ref]$confirmConversion,
                                     [ref]$readOnly, [ref]$addToRecentFiles)
    try {
        $document.Repaginate()
        if ($Report) {
            foreach ($toc in $document.TablesOfContents) {
                $toc.Update()
            }
            $document.Repaginate()
            foreach ($toc in $document.TablesOfContents) {
                $toc.UpdatePageNumbers()
            }
            $document.Repaginate()
            $pages = @(foreach ($shape in $document.InlineShapes) {
                if ($shape.AlternativeText -match '^KAC:(\d+):(\d+)\|') {
                    $section = [int]$Matches[1]
                    $index = [int]$Matches[2]
                    $range = $shape.Range.Duplicate
                    $range.Collapse(1)
                    [pscustomobject]@{
                        section = $section
                        index = $index
                        physical = $range.Information(3)
                        printed = $range.Information(1)
                    }
                }
            })
            $document.Save()
            ConvertTo-Json -InputObject $pages -Compress | Set-Content -LiteralPath $Report -Encoding UTF8
        }
        $document.ExportAsFixedFormat($Pdf, 17)
    } finally {
        $document.Close([ref]$discardChanges)
    }
} finally {
    $word.Quit([ref]$discardChanges)
}
