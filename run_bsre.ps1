$BaseDir = "C:\BSRE-Automation"

$Python = "$BaseDir\venv\Scripts\python.exe"

$Script = "$BaseDir\cek_nik_bsre_spreadseheet_merge.py"

$LogDir = "$BaseDir\logs"


# ==========================================
# PASTIKAN FOLDER LOG TERSEDIA
# ==========================================

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}


# ==========================================
# FILE LOG BERDASARKAN TANGGAL
# ==========================================

$bulan = @(
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
)

$now = Get-Date

$DateTime = "{0:D2}-{1}-{2}_{3:HH-mm-ss}" -f `
    $now.Day,
    $bulan[$now.Month - 1],
    $now.Year,
    $now

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

"BSRE Sync Start : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
    Out-File $LogFile -Append

"============================================================" |
    Out-File $LogFile -Append


# ==========================================
# JALANKAN SCRIPT
# ==========================================

try {

    & $Python $Script *>> $LogFile

    $ExitCode = $LASTEXITCODE


    if ($ExitCode -eq 0) {

        "BSRE Sync SUCCESS : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
            Out-File $LogFile -Append

    }
    else {

        "BSRE Sync FAILED - Exit Code: $ExitCode" |
            Out-File $LogFile -Append

    }

}
catch {

    "ERROR : $($_.Exception.Message)" |
        Out-File $LogFile -Append

    exit 1

}


"============================================================" |
    Out-File $LogFile -Append


exit $ExitCode