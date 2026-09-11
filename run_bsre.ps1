$BaseDir = "C:\BSRE-Automation"

$Python = "$BaseDir\venv\Scripts\python.exe"
$Script = "$BaseDir\cek_nik_bsre_spreadseheet_merge_all_rows.py"
$LogDir = "$BaseDir\logs"


# ==========================================
# PASTIKAN FOLDER LOG TERSEDIA
# ==========================================

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}


# ==========================================
# WAKTU MULAI
# ==========================================

$StartTime = Get-Date


# ==========================================
# FILE LOG BERDASARKAN TANGGAL
# ==========================================

$bulan = @(
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
)

$DateTime = "{0:D2}-{1}-{2}_{3:HHmmss}" -f `
    $StartTime.Day,
    $bulan[$StartTime.Month - 1],
    $StartTime.Year,
    $StartTime

$LogFile = "$LogDir\bsre_$DateTime.log"


# ==========================================
# PINDAH KE WORKING DIRECTORY
# ==========================================

Set-Location $BaseDir


# ==========================================
# START LOG
# ==========================================

"============================================================" |
    Out-File $LogFile -Append

"BSRE Sync Start : $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))" |
    Out-File $LogFile -Append

"============================================================" |
    Out-File $LogFile -Append


# ==========================================
# JALANKAN SCRIPT
# ==========================================

$ExitCode = 1
$Status = "ERROR"

try {

    & $Python $Script *>> $LogFile

    $ExitCode = $LASTEXITCODE

    if ($ExitCode -eq 0) {
        $Status = "SUCCESS"
    }
    else {
        $Status = "FAILED"
    }

}
catch {

    "ERROR : $($_.Exception.Message)" |
        Out-File $LogFile -Append

    $ExitCode = 1
    $Status = "ERROR"
}


# ==========================================
# END TIME & DURATION
# ==========================================

$EndTime = Get-Date
$Duration = $EndTime - $StartTime

$TotalHours = [math]::Floor($Duration.TotalHours)
$DurationText = "{0:D2}:{1:D2}:{2:D2}" -f `
    [int]$TotalHours,
    [int]$Duration.Minutes,
    [int]$Duration.Seconds

$EndTimeText = "{0:D2}-{1}-{2}_{3:HH:mm:ss}" -f `
    $EndTime.Day,
    $bulan[$EndTime.Month - 1],
    $EndTime.Year,
    $EndTime


# ==========================================
# END LOG
# ==========================================

"" |
    Out-File $LogFile -Append

"End Time   : $EndTimeText" |
    Out-File $LogFile -Append

"Duration   : $DurationText" |
    Out-File $LogFile -Append

if ($Status -eq "SUCCESS") {

    "BSRE Sync SUCCESS : $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))" |
        Out-File $LogFile -Append

}
elseif ($Status -eq "FAILED") {

    "BSRE Sync FAILED - Exit Code: $ExitCode : $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))" |
        Out-File $LogFile -Append

}
else {

    "BSRE Sync ERROR : $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))" |
        Out-File $LogFile -Append

}

"============================================================" |
    Out-File $LogFile -Append


exit $ExitCode