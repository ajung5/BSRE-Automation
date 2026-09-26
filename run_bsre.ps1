$BaseDir = "C:\BSRE-Automation"

$Python = "$BaseDir\venv\Scripts\python.exe"
$Script = "$BaseDir\cek_nik_bsre_spreadseheet_merge_all_rows.py"
$LogDir = "$BaseDir\logs"
$MutexName = "Global\BSRE-Automation-Sync"

# ==========================================
# PASTIKAN FOLDER LOG TERSEDIA
# ==========================================

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# ==========================================
# SINGLE INSTANCE GUARD
# ==========================================
# Mencegah Task Scheduler/manual run kedua berjalan paralel
# dan menulis berdasarkan snapshot spreadsheet yang sudah stale.

$Mutex = New-Object System.Threading.Mutex($false, $MutexName)
$HasMutex = $false

try {
    try {
        $HasMutex = $Mutex.WaitOne(0, $false)
    }
    catch [System.Threading.AbandonedMutexException] {
        # Proses sebelumnya crash/berhenti paksa. Ownership mutex berpindah
        # ke proses ini sehingga eksekusi boleh dilanjutkan.
        $HasMutex = $true
    }

    if (-not $HasMutex) {
        $Now = Get-Date
        $SkipLog = Join-Path $LogDir ("bsre_SKIPPED_ALREADY_RUNNING_{0}.log" -f $Now.ToString("yyyy-MM-dd_HHmmss"))

        "BSRE Sync SKIPPED : proses lain masih berjalan." | Out-File $SkipLog -Encoding utf8
        "Time              : $($Now.ToString('yyyy-MM-dd HH:mm:ss'))" | Out-File $SkipLog -Append -Encoding utf8
        "Mutex             : $MutexName" | Out-File $SkipLog -Append -Encoding utf8

        Write-Output "BSRE Sync SKIPPED: proses lain masih berjalan."
        exit 2
    }

    # ==========================================
    # VALIDASI FILE EKSEKUSI
    # ==========================================

    if (!(Test-Path $Python)) {
        throw "Python virtual environment tidak ditemukan: $Python"
    }

    if (!(Test-Path $Script)) {
        throw "Script BSRE tidak ditemukan: $Script"
    }

    # ==========================================
    # WAKTU MULAI
    # ==========================================

    $StartTime = Get-Date

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
    # WORKING DIRECTORY
    # ==========================================

    Set-Location $BaseDir

    # ==========================================
    # START LOG
    # ==========================================

    "============================================================" | Out-File $LogFile -Append -Encoding utf8
    "BSRE Sync Start : $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))" | Out-File $LogFile -Append -Encoding utf8
    "Mutex           : $MutexName" | Out-File $LogFile -Append -Encoding utf8
    "============================================================" | Out-File $LogFile -Append -Encoding utf8

    $ExitCode = 1
    $Status = "ERROR"

    try {
        & $Python -u $Script *>> $LogFile
        $ExitCode = $LASTEXITCODE

        if ($ExitCode -eq 0) {
            $Status = "SUCCESS"
        }
        else {
            $Status = "FAILED"
        }
    }
    catch {
        "ERROR : $($_.Exception.Message)" | Out-File $LogFile -Append -Encoding utf8
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

    "" | Out-File $LogFile -Append -Encoding utf8
    "End Time   : $EndTimeText" | Out-File $LogFile -Append -Encoding utf8
    "Duration   : $DurationText" | Out-File $LogFile -Append -Encoding utf8
    "Exit Code  : $ExitCode" | Out-File $LogFile -Append -Encoding utf8

    if ($Status -eq "SUCCESS") {
        "BSRE Sync SUCCESS : $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))" | Out-File $LogFile -Append -Encoding utf8
    }
    elseif ($Status -eq "FAILED") {
        "BSRE Sync FAILED - Exit Code: $ExitCode : $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))" | Out-File $LogFile -Append -Encoding utf8
    }
    else {
        "BSRE Sync ERROR : $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))" | Out-File $LogFile -Append -Encoding utf8
    }

    "============================================================" | Out-File $LogFile -Append -Encoding utf8
    exit $ExitCode
}
finally {
    if ($HasMutex) {
        try {
            $Mutex.ReleaseMutex()
        }
        catch {
            # Jangan menutupi exit code proses utama hanya karena cleanup mutex.
        }
    }

    if ($null -ne $Mutex) {
        $Mutex.Dispose()
    }
}
