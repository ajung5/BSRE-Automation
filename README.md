# BSRE Automation — Windows Task Scheduler Guide

Panduan ini menjelaskan cara menjalankan **BSRE Automation** secara otomatis di Windows atau Windows Server menggunakan **Task Scheduler**.

File ini dibuat sebagai dokumentasi terpisah dan **tidak menggantikan `README.md` utama**.

---

## Tujuan

Task Scheduler digunakan untuk menjalankan:

```text
run_bsre.ps1
```

secara otomatis pada jadwal tertentu.

Wrapper PowerShell tersebut kemudian menjalankan:

```text
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

menggunakan Python dari virtual environment.

Alur eksekusi:

```text
Windows Task Scheduler
        |
        v
powershell.exe
        |
        v
run_bsre.ps1
        |
        v
venv\Scripts\python.exe
        |
        v
cek_nik_bsre_spreadseheet_merge_all_rows.py
        |
        +--> API BSrE
        +--> Google Sheets
        `--> logs\bsre_*.log
```

---

# Prasyarat

Pastikan repository berada pada:

```text
C:\BSRE-Automation
```

dan struktur minimal tersedia:

```text
C:\BSRE-Automation\
├── cek_nik_bsre_spreadseheet_merge_all_rows.py
├── run_bsre.ps1
├── .env
├── google_credentials.json
├── venv\
└── logs\
```

Pastikan juga virtual environment sudah dibuat dan dependency sudah ter-install.

Contoh:

```powershell
cd C:\BSRE-Automation

python -m venv venv

.\venv\Scripts\python.exe -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

---

# 1. Test Manual Sebelum Membuat Task

Sebelum membuat scheduled task, pastikan wrapper bisa dijalankan secara manual.

Jalankan PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

Pastikan:

```text
1. Script berhasil berjalan.
2. API BSrE dapat diakses.
3. Google Spreadsheet dapat diakses.
4. File log berhasil dibuat.
```

Lokasi log:

```text
C:\BSRE-Automation\logs\
```

Jika eksekusi manual belum berhasil, perbaiki terlebih dahulu sebelum membuat Task Scheduler.

---

# 2. Membuka Windows Task Scheduler

Tekan:

```text
Win + R
```

kemudian jalankan:

```text
taskschd.msc
```

Pada panel kanan pilih:

```text
Create Task...
```

Direkomendasikan menggunakan:

```text
Create Task
```

dan bukan:

```text
Create Basic Task
```

karena `Create Task` menyediakan konfigurasi keamanan dan reliability yang lebih lengkap.

---

# 3. Konfigurasi Tab General

Isi contoh berikut:

```text
Name:
BSRE Daily Certificate Sync

Description:
Sinkronisasi harian status pengguna dan sertifikat elektronik BSrE ke Google Spreadsheet.
```

Pada bagian:

```text
Security options
```

pilih:

```text
Run whether user is logged on or not
```

dan aktifkan:

```text
Run with highest privileges
```

Rekomendasi:

```text
[✓] Run whether user is logged on or not
[✓] Run with highest privileges
```

Untuk:

```text
Configure for
```

pilih versi Windows atau Windows Server yang digunakan.

---

# 4. Konfigurasi Tab Triggers

Masuk ke:

```text
Triggers
```

klik:

```text
New...
```

Contoh konfigurasi:

```text
Begin the task : On a schedule
Settings       : Daily
Start          : 01:00:00
Recur every    : 1 days
Enabled        : Yes
```

Dengan konfigurasi tersebut, automation berjalan:

```text
setiap hari pukul 01:00
```

berdasarkan waktu lokal Windows Server / VPS.

Waktu dapat disesuaikan sesuai kebutuhan.

Contoh alternatif:

```text
02:00
03:00
23:00
```

---

# 5. Konfigurasi Tab Actions

Masuk ke:

```text
Actions
```

klik:

```text
New...
```

Pilih:

```text
Action:
Start a program
```

Isi sebagai berikut.

## Program/script

```text
powershell.exe
```

## Add arguments

```text
-NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

## Start in

```text
C:\BSRE-Automation
```

Konfigurasi final:

```text
Program/script:
powershell.exe

Add arguments:
-NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"

Start in:
C:\BSRE-Automation
```

Bagian:

```text
Start in
```

sangat disarankan agar working directory konsisten ketika script dijalankan melalui Task Scheduler.

---

# 6. Kenapa Menggunakan run_bsre.ps1

Task Scheduler sebaiknya tidak langsung menjalankan file Python.

Gunakan:

```text
run_bsre.ps1
```

karena wrapper dapat menangani:

```text
- lokasi project;
- virtual environment;
- Python interpreter;
- stdout;
- stderr;
- logging;
- exit code;
- waktu mulai;
- waktu selesai;
- durasi proses.
```

Dengan demikian alur automation lebih mudah diaudit dan troubleshooting lebih sederhana.

---

# 7. Konfigurasi Tab Conditions

Pada VPS atau Windows Server, beberapa opsi power tidak diperlukan.

Jika tersedia, pertimbangkan untuk menonaktifkan:

```text
Start the task only if the computer is on AC power
```

dan:

```text
Stop if the computer switches to battery power
```

Untuk server/VPS, opsi tersebut biasanya tidak relevan.

Jika automation membutuhkan internet, pastikan server memiliki koneksi jaringan yang stabil.

---

# 8. Konfigurasi Tab Settings

Rekomendasi:

```text
[✓] Allow task to be run on demand

[✓] Run task as soon as possible after
    a scheduled start is missed
```

Untuk retry:

```text
If the task fails, restart every:
10 minutes

Attempt to restart up to:
3 times
```

Untuk mencegah dua proses automation berjalan bersamaan:

```text
If the task is already running, then the following rule applies:
Do not start a new instance
```

Ini penting karena proses dapat membutuhkan waktu cukup lama ketika row spreadsheet sangat banyak.

Rekomendasi final:

```text
Allow manual run         : Enabled
Missed schedule recovery : Enabled
Restart on failure       : 10 minutes
Retry                    : 3 times
Concurrent execution     : Do not start a new instance
```

---

# 9. Simpan Task

Klik:

```text
OK
```

Jika menggunakan:

```text
Run whether user is logged on or not
```

Windows dapat meminta password account yang digunakan untuk menjalankan task.

Pastikan account tersebut memiliki permission membaca:

```text
C:\BSRE-Automation\
C:\BSRE-Automation\.env
C:\BSRE-Automation\google_credentials.json
C:\BSRE-Automation\venv\
```

dan permission menulis ke:

```text
C:\BSRE-Automation\logs\
```

---

# 10. Test Task Scheduler

Setelah task dibuat:

```text
1. Buka Task Scheduler Library.
2. Cari BSRE Daily Certificate Sync.
3. Klik kanan.
4. Pilih Run.
5. Tunggu proses selesai.
6. Klik Refresh.
7. Periksa Last Run Result.
8. Periksa file log.
```

Jika berhasil, nilai umumnya:

```text
0x0
```

atau:

```text
The operation completed successfully.
```

---

# 11. Validasi File Log

Periksa:

```text
C:\BSRE-Automation\logs\
```

Contoh nama file:

```text
bsre_12-Sep-2026_01-00-02.log
```

Pastikan bagian akhir log menunjukkan:

```text
BSRE Sync SUCCESS
```

Contoh:

```text
============================================================
STATUS     : SUCCESS
Exit Code  : 0
End Time   : 12-Sep-2026_01:15:22
Duration   : 00:15:20
============================================================
```

Jika task menunjukkan sukses tetapi file log tidak dibuat, periksa:

```text
Start in
permission folder
path run_bsre.ps1
path virtual environment
```

---

# 12. Last Run Result yang Umum

| Result | Arti Umum | Pemeriksaan |
|---|---|---|
| `0x0` | Berhasil | Tidak ada tindakan |
| `0x1` | Script mengembalikan error | Periksa log PowerShell/Python |
| `0x2` | File atau path tidak ditemukan | Periksa path project, wrapper, dan venv |
| `0x41301` | Task masih berjalan | Periksa proses PowerShell/Python |
| `0x41303` | Task belum pernah dijalankan | Jalankan manual dari Task Scheduler |

Task Scheduler result tidak selalu menunjukkan root cause aplikasi secara detail.

Gunakan file log sebagai referensi utama troubleshooting.

---

# 13. Troubleshooting

## Task Berjalan Manual tetapi Gagal di Task Scheduler

Periksa konfigurasi:

```text
Program/script:
powershell.exe
```

```text
Arguments:
-NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

```text
Start in:
C:\BSRE-Automation
```

Pastikan account Task Scheduler memiliki permission terhadap:

```text
C:\BSRE-Automation\
C:\BSRE-Automation\.env
C:\BSRE-Automation\google_credentials.json
C:\BSRE-Automation\venv\
C:\BSRE-Automation\logs\
```

---

## Error 0x1

Jalankan command yang sama secara manual:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

Kemudian periksa log terbaru.

Kemungkinan penyebab:

```text
- error Python;
- dependency tidak tersedia;
- API BSrE gagal;
- credential salah;
- Google Sheets gagal;
- environment variable tidak terbaca.
```

---

## Error 0x2

Biasanya menunjukkan file/path tidak ditemukan.

Gunakan:

```powershell
Test-Path "C:\BSRE-Automation\run_bsre.ps1"
```

```powershell
Test-Path "C:\BSRE-Automation\venv\Scripts\python.exe"
```

```powershell
Test-Path "C:\BSRE-Automation\.env"
```

```powershell
Test-Path "C:\BSRE-Automation\google_credentials.json"
```

Expected:

```text
True
```

---

## Task Tetap Running / 0x41301

Periksa proses:

```powershell
Get-Process python,powershell -ErrorAction SilentlyContinue
```

Periksa juga log terbaru.

Kemungkinan:

```text
- jumlah data sangat besar;
- API BSrE lambat;
- network timeout;
- request menggantung;
- Python belum selesai;
- proses sebelumnya belum terminate.
```

Jangan membuat instance task baru sebelum mengetahui penyebab proses sebelumnya belum selesai.

---

# 14. Rekomendasi Production

Untuk VPS atau Windows Server:

```text
Schedule:
Daily 01:00

Run whether user is logged on:
Yes

Run with highest privileges:
Yes

Run missed schedule:
Yes

Restart on failure:
Every 10 minutes

Retry:
3 times

Concurrent execution:
Do not start a new instance
```

---

# 15. Rekomendasi Keamanan

File berikut bersifat sensitif:

```text
.env
google_credentials.json
```

Jangan commit ke Git.

Pastikan `.gitignore` mencakup:

```gitignore
.env
*.env

google_credentials.json
*credentials*.json

logs/
*.log

venv/
.venv/
```

Batasi permission folder hanya untuk account yang membutuhkan akses.

Gunakan prinsip:

```text
Least Privilege
```

untuk:

```text
- account Windows;
- Google Service Account;
- API BSrE;
- filesystem;
- scheduled task.
```

---

# 16. Checklist Final

Sebelum automation dianggap siap production, pastikan:

```text
[ ] Repository berada di C:\BSRE-Automation

[ ] Virtual environment tersedia

[ ] Dependency Python sudah ter-install

[ ] File .env tersedia

[ ] google_credentials.json tersedia

[ ] Google Service Account memiliki akses Editor

[ ] API BSrE dapat diakses

[ ] run_bsre.ps1 berhasil dijalankan manual

[ ] Log berhasil dibuat

[ ] Task Scheduler dibuat

[ ] Program/script = powershell.exe

[ ] Arguments sudah benar

[ ] Start in = C:\BSRE-Automation

[ ] Run whether user is logged on or not aktif

[ ] Run with highest privileges aktif

[ ] Do not start a new instance aktif

[ ] Test manual dari Task Scheduler berhasil

[ ] Last Run Result = 0x0

[ ] Log menunjukkan BSRE Sync SUCCESS
```

---

# Ringkasan Konfigurasi

```text
Task Name:
BSRE Daily Certificate Sync

Trigger:
Daily 01:00

Program:
powershell.exe

Arguments:
-NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"

Start in:
C:\BSRE-Automation

Security:
Run whether user is logged on or not
Run with highest privileges

Failure:
Restart every 10 minutes
Maximum 3 attempts

Concurrency:
Do not start a new instance
```

---

# Author

**ajung5**

Repository:

```text
https://github.com/ajung5/BSRE-Automation
```
