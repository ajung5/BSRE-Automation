# BSRE Automation

Automasi pengecekan **status pengguna dan sertifikat elektronik BSrE** berdasarkan data NIK pada Google Spreadsheet.

Repository menyediakan dua mode operasi:

1. **Filtered / Visible Rows**
   - file: `cek_nik_bsre_spreadseheet_merge.py`
   - hanya memproses row yang terlihat;
   - row yang tersembunyi oleh filter atau secara manual tidak diproses.

2. **All Rows**
   - file: `cek_nik_bsre_spreadseheet_merge_all_rows.py`
   - memproses seluruh row data;
   - filter atau hidden row tidak memengaruhi proses.

Kedua script menggunakan mekanisme **differential update**, yaitu hanya cell pada kolom **O, P, Q, dan R yang benar-benar berubah** yang ditulis kembali ke Google Sheets.

---

## Fitur

- Membaca data NIK langsung dari Google Spreadsheet.
- Mendukung mode filtered/visible rows.
- Mendukung mode seluruh row.
- Mengecek status sertifikat melalui API BSrE.
- Mengecek profile sertifikat untuk memperoleh tanggal berlaku.
- Memetakan status API BSrE ke status yang lebih mudah dibaca.
- Membandingkan data lama dengan hasil terbaru.
- Hanya meng-update cell O/P/Q/R yang berubah.
- Menormalisasi format tanggal sebelum dibandingkan.
- Melakukan batch update ke Google Sheets.
- Menampilkan statistik hasil pengecekan pada akhir proses.
- Menyediakan PowerShell wrapper untuk automation di Windows.
- Menyimpan output automation ke file log.
- Menyediakan unit test untuk memvalidasi logic tanpa mengubah Google Sheets atau mengakses API BSrE nyata.

---

## Alur Kerja

### Mode Filtered

```text
Google Spreadsheet
        |
        v
Deteksi row yang terlihat
        |
        +--> hiddenByFilter = true --> SKIP
        |
        +--> hiddenByUser = true ----> SKIP
        |
        v
     Ambil NIK
        |
        +-------------------------+
        |                         |
        v                         v
/api/user/status/{nik}    /api/user/profile/{nik}
        |                         |
        v                         v
 Status Pengguna           Tanggal Sertifikat
 Status Sertifikat         Terbit / Berakhir
        |                         |
        +------------+------------+
                     |
                     v
              Bandingkan O:P:Q:R
                     |
             +-------+-------+
             |               |
           Sama            Berubah
             |               |
           SKIP        Update cell saja
```

### Mode All Rows

```text
Google Spreadsheet
        |
        v
Ambil seluruh row data
        |
        v
     Ambil NIK
        |
        v
Cek API BSrE
        |
        v
Bandingkan O:P:Q:R
        |
        v
Update hanya cell yang berubah
```

---

## Struktur Repository

```text
BSRE-Automation/
├── cek_nik_bsre_spreadseheet_merge.py
├── cek_nik_bsre_spreadseheet_merge_all_rows.py
├── run_bsre.ps1
├── test/
│   ├── test_cek_nik_bsre.py
│   └── test_both_bsre_modes.py
├── .gitignore
├── README.md
├── .env                       # tidak disimpan ke Git
├── google_credentials.json    # tidak disimpan ke Git
├── venv/                      # tidak disimpan ke Git
└── logs/
```

---

## Kolom Google Spreadsheet

Script menggunakan kolom berikut:

| Kolom | Fungsi                    |
| ----- | ------------------------- |
| `NIK` | Sumber NIK yang diperiksa |
| `O`   | Status Pengguna           |
| `P`   | Status Sertifikat         |
| `Q`   | Tanggal terbit            |
| `R`   | Tanggal berakhir          |

Script juga memastikan header:

```text
Q1 = Tanggal terbit
R1 = Tanggal berakhir
```

Tanggal dikirim ke Google Sheets dalam format:

```text
YYYY-MM-DD
```

agar dikenali sebagai tipe **Date**, kemudian tampilan kolom `Q:R` diformat menjadi:

```text
dd-mmm-yyyy
```

Contoh:

```text
12-Agu-2026
```

---

## Differential Update

Sebelum melakukan write, script membandingkan data hasil API dengan nilai yang saat ini ada di spreadsheet.

Contoh:

```text
Spreadsheet:
O = Verified
P = Issued
Q = 12-Agu-2024
R = 12-Agu-2026

Hasil API:
O = Verified
P = Expired
Q = 2024-08-12
R = 2026-08-12
```

Hasil:

```text
O -> sama    -> tidak di-update
P -> berubah -> update
Q -> sama    -> tidak di-update
R -> sama    -> tidak di-update
```

Pada contoh tersebut hanya cell kolom `P` yang ditulis kembali.

Format tanggal dinormalisasi sebelum dibandingkan, sehingga nilai seperti:

```text
12-Agu-2026
2026-08-12
12/08/2026
```

dianggap tanggal yang sama.

---

## Mapping Status BSrE

| Status API       | Status Pengguna | Status Sertifikat |
| ---------------- | --------------- | ----------------- |
| `ISSUE`          | Verified        | Issued            |
| `REVOKE`         | Verified        | Revoke            |
| `RENEW`          | Verified        | Renew             |
| `NO_CERTIFICATE` | Verified        | New               |
| `EXPIRED`        | Verified        | Expired           |
| `NOT_REGISTERED` | Tidak diubah    | Tidak diubah      |

---

# Persyaratan

## Sistem

Direkomendasikan:

- Windows 10 / Windows 11 / Windows Server, atau macOS/Linux untuk penggunaan manual;
- Python 3.10+;
- PowerShell untuk automation Windows;
- Google Service Account;
- credential API BSrE yang valid.

## Python Dependency

```text
gspread
requests
python-dateutil
python-dotenv
tqdm
google-auth
google-api-python-client
```

Install:

```bash
pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

Atau agar dependency dipasang ke interpreter Python yang benar:

```bash
python -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

Pada macOS biasanya:

```bash
python3 -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

---

# Instalasi

## Windows

Clone repository:

```powershell
git clone https://github.com/ajung5/BSRE-Automation.git C:\BSRE-Automation
cd C:\BSRE-Automation
```

Buat virtual environment:

```powershell
python -m venv venv
```

Aktifkan:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependency:

```powershell
python -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

## macOS

Clone repository:

```bash
git clone https://github.com/ajung5/BSRE-Automation.git
cd BSRE-Automation
```

Buat virtual environment:

```bash
python3 -m venv venv
```

Aktifkan:

```bash
source venv/bin/activate
```

Install dependency:

```bash
python3 -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

---

# Konfigurasi

Buat file `.env` pada root repository.

Contoh:

```env
# ==========================================
# BSRE API
# ==========================================

BSRE_BASE_URL=https://example-bsre-api
BSRE_USERNAME=your_username
BSRE_PASSWORD=your_password


# ==========================================
# GOOGLE SHEETS
# ==========================================

GOOGLE_CREDENTIALS=google_credentials.json

SPREADSHEET_ID=your_google_spreadsheet_id

WORKSHEET_NAME=Nama Worksheet
```

> Jangan commit `.env` karena berisi credential dan konfigurasi sensitif.

---

# Google Service Account

Simpan credential Google Service Account sebagai:

```text
google_credentials.json
```

pada root repository.

Pastikan nilai:

```env
GOOGLE_CREDENTIALS=google_credentials.json
```

sesuai dengan nama/path credential.

Cari `client_email` pada file credential:

```json
"client_email": "service-account-name@project-id.iam.gserviceaccount.com"
```

Share Google Spreadsheet ke alamat tersebut dan berikan permission:

```text
Editor
```

---

# Menjalankan Script Manual

## Windows — Filtered / Visible Rows

```powershell
cd C:\BSRE-Automation
python .\cek_nik_bsre_spreadseheet_merge.py
```

Dengan interpreter dari virtual environment tanpa aktivasi:

```powershell
.\venv\Scripts\python.exe .\cek_nik_bsre_spreadseheet_merge.py
```

## Windows — Semua Row

```powershell
python .\cek_nik_bsre_spreadseheet_merge_all_rows.py
```

atau:

```powershell
.\venv\Scripts\python.exe .\cek_nik_bsre_spreadseheet_merge_all_rows.py
```

## macOS — Filtered / Visible Rows

```bash
cd BSRE-Automation
python3 cek_nik_bsre_spreadseheet_merge.py
```

Dengan virtual environment:

```bash
./venv/bin/python cek_nik_bsre_spreadseheet_merge.py
```

## macOS — Semua Row

```bash
python3 cek_nik_bsre_spreadseheet_merge_all_rows.py
```

atau:

```bash
./venv/bin/python cek_nik_bsre_spreadseheet_merge_all_rows.py
```

---

# Menjalankan dengan PowerShell Wrapper

Repository menyediakan:

```text
run_bsre.ps1
```

Wrapper digunakan untuk automation Windows dan saat ini menjalankan:

```text
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

Directory default:

```powershell
$BaseDir = "C:\BSRE-Automation"
```

Contoh:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

Wrapper akan:

1. menentukan lokasi project;
2. menggunakan Python dari virtual environment;
3. memastikan directory `logs` tersedia;
4. membuat file log setiap eksekusi;
5. menjalankan script all-rows;
6. menangkap `stdout` dan `stderr`;
7. mencatat status proses;
8. mencatat waktu selesai dan durasi;
9. mengembalikan exit code ke Windows.

---

# Konfigurasi Windows Task Scheduler

Bagian ini digunakan untuk menjalankan **BSRE Automation** secara otomatis di Windows atau Windows Server menggunakan **Task Scheduler**.

Task Scheduler akan menjalankan:

```text
run_bsre.ps1
```

yang kemudian menjalankan:

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

## 1. Test `run_bsre.ps1` Secara Manual

Sebelum membuat Task Scheduler, pastikan wrapper dapat dijalankan secara manual.

Jalankan:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

Pastikan:

```text
- script berhasil berjalan;
- API BSrE dapat diakses;
- Google Spreadsheet dapat diakses;
- file log berhasil dibuat.
```

Log seharusnya tersedia pada:

```text
C:\BSRE-Automation\logs\
```

Jika eksekusi manual belum berhasil, selesaikan error terlebih dahulu sebelum membuat scheduled task.

## 2. Buka Task Scheduler

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

Direkomendasikan menggunakan **Create Task**, bukan **Create Basic Task**, agar konfigurasi keamanan dan reliability lebih lengkap.

## 3. Tab `General`

Contoh:

```text
Name        : BSRE Daily Certificate Sync
Description : Sinkronisasi harian status pengguna dan sertifikat elektronik BSrE ke Google Spreadsheet
```

Pada bagian **Security options**, gunakan:

```text
Run whether user is logged on or not
Run with highest privileges
```

Rekomendasi:

```text
[✓] Run whether user is logged on or not
[✓] Run with highest privileges
```

Pada **Configure for**, pilih versi Windows atau Windows Server yang digunakan.

Account Windows yang menjalankan task harus memiliki akses ke:

```text
C:\BSRE-Automation\
C:\BSRE-Automation\.env
C:\BSRE-Automation\google_credentials.json
C:\BSRE-Automation\venv\
C:\BSRE-Automation\logs\
```

## 4. Tab `Triggers`

Klik:

```text
New...
```

Contoh konfigurasi agar automation berjalan setiap hari pukul `01:00`:

```text
Begin the task : On a schedule
Settings       : Daily
Start          : 01:00:00
Recur every    : 1 days
Enabled        : Yes
```

Waktu dapat disesuaikan dengan kebutuhan operasional.

Task Scheduler menggunakan waktu lokal Windows Server/VPS.

## 5. Tab `Actions`

Klik:

```text
New...
```

Pilih:

```text
Action:
Start a program
```

Isi sebagai berikut.

### Program/script

```text
powershell.exe
```

### Add arguments

```text
-NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

### Start in

```text
C:\BSRE-Automation
```

Konfigurasi final:

```text
Program/script : powershell.exe
Arguments      : -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
Start in       : C:\BSRE-Automation
```

Bagian `Start in` penting agar working directory tetap konsisten ketika task dijalankan tanpa terminal interaktif.

Task Scheduler sebaiknya menjalankan `run_bsre.ps1`, bukan file Python secara langsung, karena wrapper menangani:

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

## 6. Tab `Conditions`

Untuk VPS atau Windows Server, opsi daya biasanya tidak diperlukan.

Jika tersedia, pertimbangkan untuk menonaktifkan:

```text
Start the task only if the computer is on AC power
Stop if the computer switches to battery power
```

Pastikan koneksi internet server tersedia karena script membutuhkan akses ke:

```text
API BSrE
Google Sheets API
```

## 7. Tab `Settings`

Rekomendasi:

```text
[✓] Allow task to be run on demand

[✓] Run task as soon as possible after a scheduled start is missed
```

Untuk retry ketika task gagal:

```text
If the task fails, restart every : 10 minutes
Attempt to restart up to         : 3 times
```

Untuk mencegah dua proses berjalan bersamaan:

```text
If the task is already running,
then the following rule applies:

Do not start a new instance
```

Opsi ini penting agar dua proses tidak melakukan request API dan update Google Sheets secara paralel.

## 8. Simpan Task

Klik:

```text
OK
```

Jika menggunakan:

```text
Run whether user is logged on or not
```

Windows dapat meminta password account yang digunakan untuk menjalankan task.

## 9. Test dari Task Scheduler

Setelah task dibuat:

```text
1. Buka Task Scheduler Library.
2. Cari task "BSRE Daily Certificate Sync".
3. Klik kanan task.
4. Pilih Run.
5. Tunggu proses selesai.
6. Klik Refresh.
7. Periksa Last Run Result.
8. Periksa file log.
```

Jika berhasil, **Last Run Result** umumnya:

```text
0x0
```

atau:

```text
The operation completed successfully.
```

## 10. Validasi Log

Periksa folder:

```text
C:\BSRE-Automation\logs\
```

Pastikan terdapat file log baru sesuai waktu eksekusi Task Scheduler.

Contoh:

```text
bsre_12-Sep-2026_01-00-02.log
```

Pastikan bagian akhir log menunjukkan proses berhasil.

Contoh:

```text
STATUS     : SUCCESS
Exit Code  : 0
```

Jika task terlihat sukses tetapi log tidak terbentuk, periksa kembali:

```text
Start in
permission folder
path run_bsre.ps1
path virtual environment
```

## 11. Last Run Result yang Umum

| Result    | Arti Umum                      | Pemeriksaan                             |
| --------- | ------------------------------ | --------------------------------------- |
| `0x0`     | Berhasil                       | Tidak ada tindakan                      |
| `0x1`     | Script mengembalikan error     | Periksa log PowerShell/Python           |
| `0x2`     | File atau path tidak ditemukan | Periksa path project, wrapper, dan venv |
| `0x41301` | Task masih berjalan            | Periksa proses PowerShell/Python        |
| `0x41303` | Task belum pernah dijalankan   | Jalankan manual dari Task Scheduler     |

Task Scheduler result tidak selalu menunjukkan root cause aplikasi secara detail.

Gunakan file log sebagai sumber utama troubleshooting.

## 12. Troubleshooting Task Scheduler

### Task Berjalan Manual tetapi Gagal dari Task Scheduler

Periksa kembali:

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

Pastikan account Task Scheduler memiliki permission terhadap seluruh file yang dibutuhkan.

### Error `0x1`

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

### Error `0x2`

Biasanya menunjukkan file/path tidak ditemukan.

Verifikasi:

```powershell
Test-Path "C:\BSRE-Automation\run_bsre.ps1"
Test-Path "C:\BSRE-Automation\venv\Scripts\python.exe"
Test-Path "C:\BSRE-Automation\.env"
Test-Path "C:\BSRE-Automation\google_credentials.json"
```

Expected:

```text
True
```

### Task Tetap `Running` / `0x41301`

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
- proses Python masih berjalan;
- proses sebelumnya belum selesai.
```

Jangan membuat instance task baru sebelum mengetahui penyebab proses sebelumnya belum selesai.

## 13. Rekomendasi Konfigurasi Production

Untuk VPS atau Windows Server:

```text
Task Name                  : BSRE Daily Certificate Sync
Schedule                   : Daily 01:00
Run whether user logged on : Yes
Run with highest privileges: Yes
Missed schedule recovery   : Yes
Restart on failure         : Every 10 minutes
Maximum retry              : 3 times
Concurrent execution       : Do not start a new instance
```

Ringkasan `Action`:

```text
Program/script:
powershell.exe

Arguments:
-NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"

Start in:
C:\BSRE-Automation
```

## 14. Checklist Task Scheduler

Sebelum automation dianggap siap:

```text
[ ] run_bsre.ps1 berhasil dijalankan manual
[ ] virtual environment tersedia
[ ] .env tersedia
[ ] google_credentials.json tersedia
[ ] API BSrE dapat diakses
[ ] Google Sheets dapat diakses
[ ] Task Scheduler sudah dibuat
[ ] Program/script = powershell.exe
[ ] Arguments sudah benar
[ ] Start in = C:\BSRE-Automation
[ ] Run whether user is logged on or not aktif
[ ] Run with highest privileges aktif
[ ] Do not start a new instance aktif
[ ] Test manual dari Task Scheduler berhasil
[ ] Last Run Result = 0x0
[ ] File log baru berhasil dibuat
```

---

# Logging

Log automation PowerShell disimpan di:

```text
C:\BSRE-Automation\logs\
```

Format filename:

```text
bsre_DD-Bbb-YYYY_HH-mm-ss.log
```

Contoh:

```text
bsre_11-Sep-2026_18-00-01.log
```

Contoh footer:

```text
End Time   : 11-Sep-2026_18:42:12
Duration   : 00:42:11
BSRE Sync SUCCESS : 2026-09-11 18:42:12
============================================================
```

Jika proses gagal:

```text
BSRE Sync FAILED - Exit Code: 1 : 2026-09-11 18:10:22
============================================================
```

---

# Unit Testing

Repository menyediakan unit test untuk memastikan logic utama pada **kedua mode operasi** tetap bekerja setelah source code diubah:

```text
cek_nik_bsre_spreadseheet_merge.py
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

Unit test saat ini berada pada:

```text
tests/test_both_bsre_modes.py
```

Test menggunakan module bawaan Python:

```text
unittest
unittest.mock
```

sehingga **tidak membutuhkan `pytest`**.

Unit test dirancang agar aman dijalankan pada komputer lokal maupun VPS karena menggunakan **mock/fake object**. Selama unit test berjalan:

- tidak melakukan request nyata ke API BSrE;
- tidak mengubah Google Sheets asli;
- tidak melakukan write ke spreadsheet produksi;
- response API digantikan dengan `FakeResponse`;
- worksheet Google Sheets digantikan dengan `FakeWorksheet`;
- Google Sheets service metadata digantikan dengan fake service;
- delay `time.sleep()` dimock agar test berjalan cepat;
- progress `tqdm` dimock agar tidak mengganggu output test.

Walaupun koneksi eksternal dimock, dependency aplikasi tetap harus ter-install karena kedua file Python utama tetap di-import saat test dijalankan.

---

## File Unit Test

Struktur unit test saat ini:

```text
BSRE-Automation/
├── cek_nik_bsre_spreadseheet_merge.py
├── cek_nik_bsre_spreadseheet_merge_all_rows.py
└── tests/
    └── test_both_bsre_modes.py
```

File:

```text
tests/test_both_bsre_modes.py
```

menguji kedua script sekaligus dan saat ini berisi **15 test method**.

---

## Apa yang Diuji

### 1. Normalisasi Tanggal pada Kedua Script

Test memastikan berbagai format tanggal berikut:

```text
2026-08-12
12-08-2026
12/08/2026
12-Agu-2026
12-Aug-2026
12 Agustus 2026
12 August 2026
```

dinormalisasi menjadi:

```text
2026-08-12
```

Tujuannya agar perbedaan format tampilan tidak dianggap sebagai perubahan data.

---

### 2. Perbandingan Tanggal

Contoh:

```text
Lama : 12-Agu-2026
Baru : 2026-08-12
```

Expected:

```text
Tidak berubah
```

Sedangkan:

```text
Lama : 12-Agu-2026
Baru : 2027-08-12
```

Expected:

```text
Berubah
```

---

### 3. Perbandingan Nilai Teks

Test memastikan spasi di awal atau akhir tidak menyebabkan false-positive.

Contoh:

```text
" Verified "
"Verified"
```

Expected:

```text
Tidak berubah
```

Sedangkan:

```text
Issued
Expired
```

Expected:

```text
Berubah
```

---

### 4. Helper Pengambilan Nilai Cell

Test memastikan fungsi pengambilan nilai cell:

- mengembalikan nilai pada index yang valid;
- mengembalikan string kosong jika index berada di luar panjang row.

Ini mencegah error ketika suatu row memiliki jumlah kolom yang tidak lengkap.

---

### 5. Mapping Status `ISSUE`

Mock API:

```json
{
  "status": "ISSUE"
}
```

Expected:

```text
update             = True
status_api         = ISSUE
status_pengguna    = Verified
status_sertifikat  = Issued
```

Test dijalankan terhadap **kedua script**.

---

### 6. Status `NOT_REGISTERED`

Mock API:

```json
{
  "status": "NOT_REGISTERED"
}
```

Expected:

```text
update = False
```

serta:

```text
status_pengguna   = None
status_sertifikat = None
```

Artinya status lama pada kolom O/P tidak dihapus atau ditimpa.

---

### 7. Pemilihan Sertifikat Terbaru

Jika API profile mengembalikan:

```text
12-08-2026
12-08-2028
12-08-2027
```

script harus memilih:

```text
12-08-2028
```

sebagai tanggal berakhir terbaru.

Tanggal terbit kemudian dihitung menjadi:

```text
2026-08-12
```

berdasarkan logic:

```text
Tanggal Terbit = Tanggal Berakhir - 2 Tahun
```

---

### 8. Profile Tanpa Sertifikat

Jika API mengembalikan daftar sertifikat kosong:

```json
{
  "success": true,
  "data": {
    "sertifikat": []
  }
}
```

Expected:

```text
status           = NO_CERTIFICATE
tanggal_terbit   = ""
tanggal_berakhir = ""
```

---

### 9. Profile HTTP `404`

Jika endpoint profile mengembalikan HTTP:

```text
404
```

Expected:

```text
status = NOT_FOUND
```

---

### 10. Deteksi Row Visible pada Filtered Mode

Test memvalidasi metadata:

```text
hiddenByFilter
hiddenByUser
```

Contoh:

```text
Row 1 = header
Row 2 = visible
Row 3 = hiddenByFilter
Row 4 = hiddenByUser
Row 5 = visible
```

Expected row yang dianggap terlihat:

```text
1, 2, 5
```

Row yang hidden tidak ikut diproses.

---

### 11. Filtered Mode Hanya Memanggil API untuk Row Visible

Test membuat data:

```text
Row 2 = visible
Row 3 = hiddenByFilter
```

Expected:

```text
API status  -> hanya dipanggil untuk Row 2
API profile -> hanya dipanggil untuk Row 2
```

Dengan demikian perubahan pada logic filter dapat terdeteksi sebelum script dipakai ke spreadsheet produksi.

---

### 12. All-Rows Mode Memproses Seluruh Row

Untuk script:

```text
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

jika terdapat:

```text
Row 2
Row 3
```

Expected:

```text
API status  -> dipanggil untuk Row 2 dan Row 3
API profile -> dipanggil untuk Row 2 dan Row 3
```

Mode ini tidak bergantung pada metadata filter Google Sheets.

---

### 13. Differential Update Hanya Menulis Cell yang Berubah

Contoh:

```text
Row 3 sebelum:
O = Verified
P = Issued
Q = 2024-08-12
R = 2026-08-12

Hasil API:
O = Verified
P = Expired
Q = 2024-08-12
R = 2026-08-12
```

Expected batch update:

```text
P3 = Expired
```

Bukan:

```text
O3
P3
Q3
R3
```

Test juga memastikan format tanggal tidak diubah jika Q/R memang tidak mengalami perubahan.

---

# Menjalankan Unit Test di Windows

Jalankan command dari **root repository**, bukan dari dalam folder `tests`.

Contoh:

```powershell
cd C:\BSRE-Automation
```

## Dengan Virtual Environment

Direkomendasikan jika repository menggunakan `venv`:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

## Dengan Python Global

Jika dependency sudah ter-install secara global:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Command tersebut akan mencari file:

```text
tests/test_*.py
```

dan menjalankan seluruh test yang ditemukan.

---

## Menjalankan Hanya `test_both_bsre_modes.py` di Windows

Dengan virtual environment:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_both_bsre_modes.py" -v
```

Dengan Python global:

```powershell
python -m unittest discover -s tests -p "test_both_bsre_modes.py" -v
```

Penggunaan `unittest discover` direkomendasikan agar root repository tetap berada pada Python import path dan kedua module utama dapat ditemukan dengan benar.

---

# Menjalankan Unit Test di macOS

Masuk ke root repository:

```bash
cd /path/ke/BSRE-Automation
```

## Dengan Virtual Environment

```bash
./venv/bin/python -m unittest discover -s tests -p "test_*.py" -v
```

Jika virtual environment sudah diaktifkan dengan:

```bash
source venv/bin/activate
```

cukup jalankan:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Dengan Python Global

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## Menjalankan Hanya `test_both_bsre_modes.py` di macOS

Dengan virtual environment:

```bash
./venv/bin/python -m unittest discover -s tests -p "test_both_bsre_modes.py" -v
```

Dengan Python global:

```bash
python3 -m unittest discover -s tests -p "test_both_bsre_modes.py" -v
```

---

# Membaca Hasil Unit Test

Jika seluruh test berhasil, output akhir akan seperti:

```text
----------------------------------------------------------------------
Ran 15 tests in X.XXXs

OK
```

Beberapa test akan tampil seperti:

```text
test_normalisasi_tanggal_pada_kedua_script ... ok
test_issue ... ok
test_not_registered_tidak_update ... ok
test_ambil_row_terlihat_melewati_hidden ... ok
test_proses_filtered_hanya_memanggil_api_untuk_row_visible ... ok
test_proses_all_rows_memanggil_api_untuk_semua_row ... ok
test_all_rows_hanya_update_cell_yang_berubah ... ok
```

Arti status:

| Status  | Arti                                                                    |
| ------- | ----------------------------------------------------------------------- |
| `ok`    | Test berhasil                                                           |
| `FAIL`  | Test berjalan, tetapi hasil aktual berbeda dari expected                |
| `ERROR` | Test gagal dieksekusi karena exception, dependency, atau masalah import |

---

# Workflow Testing yang Direkomendasikan

Sebelum menjalankan script setelah melakukan perubahan source code:

```text
Edit source
    |
    v
Jalankan Unit Test
    |
    +-- FAIL / ERROR --> Perbaiki source atau test
    |
    `-- OK
         |
         v
   Jalankan script manual
         |
         v
   Verifikasi hasil
         |
         v
   Deploy / Task Scheduler
```

Windows:

```powershell
git pull
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

macOS:

```bash
git pull
./venv/bin/python -m unittest discover -s tests -p "test_*.py" -v
```

---

# Troubleshooting Unit Test

## `ModuleNotFoundError: No module named 'cek_nik_bsre_spreadseheet_merge'`

Pastikan terminal berada pada **root repository**.

Windows:

```text
C:\BSRE-Automation>
```

macOS:

```text
/path/ke/BSRE-Automation/
```

Kemudian gunakan:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

atau pada macOS:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Jangan menjalankan test setelah berpindah working directory ke:

```text
BSRE-Automation/tests/
```

karena module utama berada pada root repository.

---

## `ModuleNotFoundError: No module named 'cek_nik_bsre_spreadseheet_merge_all_rows'`

Penyebabnya sama: Python tidak menemukan module all-rows pada root repository.

Pastikan command dijalankan dari:

```text
BSRE-Automation/
```

dan bukan dari:

```text
BSRE-Automation/tests/
```

---

## `ModuleNotFoundError: No module named 'gspread'`

Dependency aplikasi belum tersedia pada interpreter Python yang digunakan untuk menjalankan test.

Windows dengan venv:

```powershell
.\venv\Scripts\python.exe -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

Windows global:

```powershell
python -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

macOS dengan venv:

```bash
./venv/bin/python -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

macOS global:

```bash
python3 -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

---

## Apakah Unit Test Memerlukan `.env` dan `google_credentials.json`?

Untuk unit test saat ini, credential produksi **tidak digunakan untuk koneksi nyata**.

Test mengganti nilai konfigurasi serta koneksi eksternal menggunakan mock/fake object.

Artinya unit test tidak akan:

```text
mengakses Google Sheets produksi
mengubah data produksi
mengirim request nyata ke API BSrE
```

Namun kedua script utama tetap menjalankan:

```python
load_dotenv()
```

saat module di-import.

Unit test ini bertujuan menguji **logic aplikasi**, bukan menguji validitas credential atau konektivitas ke environment produksi.

---

# Row yang Diproses

## Filtered Mode

Script:

```text
cek_nik_bsre_spreadseheet_merge.py
```

membaca:

```text
hiddenByFilter
hiddenByUser
```

Row dilewati jika salah satunya bernilai `true`.

Contoh:

```text
1000 row total
↓
Filter OPD tertentu
↓
120 row terlihat
↓
Hanya 120 row diperiksa ke API BSrE
```

## All-Rows Mode

Script:

```text
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

memproses seluruh row data tanpa memperhatikan filter/hidden state.

---

# Proses API BSrE

Untuk setiap NIK yang diproses, script melakukan dua request utama.

## Status Sertifikat

```http
GET /api/user/status/{nik}
```

Digunakan untuk menentukan:

```text
Status Pengguna
Status Sertifikat
```

## Profile Sertifikat

```http
GET /api/user/profile/{nik}
```

Jika terdapat beberapa sertifikat, script memilih `berlaku_sampai` paling baru.

---

# Perhitungan Tanggal Sertifikat

```text
Tanggal Terbit = Tanggal Berakhir - 2 Tahun
```

Contoh:

```text
Tanggal berakhir : 12-08-2028
Tanggal terbit   : 12-08-2026
```

> Mekanisme ini menggunakan asumsi masa berlaku sertifikat dua tahun. Jika API BSrE menyediakan tanggal penerbitan eksplisit atau kebijakan berubah, logic perlu disesuaikan.

---

# Statistik Eksekusi

Contoh statistik:

```text
======================================================================
 HASIL PENGECEKAN
======================================================================

Total row data            : 18399
Total row diproses        : 18399
Total row berubah         : 124
Total row tanpa perubahan : 18275
Total cell berubah        : 167

--- PERUBAHAN CELL ---
Status Pengguna (O)       : 25
Status Sertifikat (P)     : 87
Tanggal terbit (Q)        : 21
Tanggal berakhir (R)      : 34

--- STATISTIK STATUS ---
ISSUE                     : 7397
EXPIRED                   : 66
REVOKE                    : 8
RENEW                     : 10
NO_CERTIFICATE            : 164
NOT_REGISTERED            : 10748
Tidak diubah              : 6
```

---

# Troubleshooting Operasional

## `google_credentials.json tidak ditemukan`

Pastikan file tersedia pada root repository atau path di `.env` benar.

```env
GOOGLE_CREDENTIALS=google_credentials.json
```

## `SPREADSHEET_ID belum diisi`

```env
SPREADSHEET_ID=xxxxxxxxxxxxxxxx
```

## Error 403 Google Sheets

Pastikan Service Account sudah di-share ke spreadsheet dengan permission **Editor**.

## Error 401 BSrE

Periksa:

```env
BSRE_USERNAME=
BSRE_PASSWORD=
```

## Header `NIK` Tidak Ditemukan

Worksheet harus memiliki header:

```text
NIK
```

---

# Keamanan

File berikut tidak boleh disimpan ke repository:

```text
.env
google_credentials.json
*.env
*credentials*.json
```

Log juga sebaiknya diabaikan:

```gitignore
logs/
*.log
```

Rekomendasi:

```gitignore
# Environment / Secrets
.env
*.env

# Google Service Account
google_credentials.json
*credentials*.json

# Logs
logs/
*.log

# Python Virtual Environment
venv/
.venv/

# Python Cache
__pycache__/
*.py[cod]

# VS Code
.vscode/

# OS Files
Thumbs.db
.DS_Store
```

Jika credential pernah masuk Git history:

1. rotate/revoke credential;
2. buat credential baru;
3. hapus secret dari Git history jika diperlukan;
4. pastikan file sudah masuk `.gitignore`.

---

---

# Heartbeat Progress dan Task Scheduler untuk Proses Panjang

Bagian ini merupakan catatan operasional tambahan untuk mode **All Rows**, terutama ketika jumlah data besar dan proses dijalankan melalui Windows Task Scheduler.

## Heartbeat Setiap 500 Row

Untuk proses yang membutuhkan waktu lama, script All Rows dapat menggunakan heartbeat agar file log tetap menunjukkan bahwa proses masih aktif tanpa mencetak setiap NIK.

Konfigurasi heartbeat:

```python
HEARTBEAT_INTERVAL = 500
```

Heartbeat dicetak setiap 500 row yang telah selesai diproses dan menampilkan:

```text
Progress
Persentase
Elapsed time
ETA
```

Contoh:

```text
Total row data       : 18405
Total row diproses   : 18405
Mode                 : SEMUA ROW
Update               : HANYA CELL O/P/Q/R YANG BERUBAH
Heartbeat            : SETIAP 500 ROW

Progress : 500 / 18405 (2.72%) | Elapsed: 00:04:14 | ETA: 02:31:38
Progress : 1000 / 18405 (5.43%) | Elapsed: 00:08:29 | ETA: 02:27:44
Progress : 1500 / 18405 (8.15%) | Elapsed: 00:12:46 | ETA: 02:23:58
...
Progress : 18000 / 18405 (97.80%) | Elapsed: 02:31:42 | ETA: 00:03:24
Progress : 18405 / 18405 (100.00%) | Elapsed: 02:35:09 | ETA: 00:00:00

Mengupdate Google Spreadsheet...
```

`ETA` dihitung ulang berdasarkan rata-rata waktu pemrosesan row yang sudah selesai.

Karena response API dan kondisi jaringan dapat berubah, nilai ETA bersifat estimasi dan dapat naik atau turun selama proses berjalan.

Heartbeat tidak mengubah logic pengecekan, differential update, statistik, maupun batch update Google Sheets. Fungsinya hanya memberikan visibility terhadap proses yang berjalan lama.

---

## Mengapa Progress `tqdm` Tidak Muncul di Log Task Scheduler

Pada mode non-interactive seperti Task Scheduler, `stdout` bukan terminal interaktif.

Jika `tqdm` dikonfigurasi dengan:

```python
disable=not sys.stdout.isatty()
```

maka progress bar `tqdm` otomatis tidak ditampilkan pada file log.

Heartbeat digunakan agar log tetap memperlihatkan perkembangan proses tanpa menghasilkan ribuan baris output.

---

# Execution Time Limit Task Scheduler

Proses All Rows dapat membutuhkan waktu lebih dari dua jam karena setiap NIK melakukan request ke API BSrE.

Periksa konfigurasi task:

```powershell
(Get-ScheduledTask -TaskName "BSRE Daily Certificate Sync").Settings |
Format-List ExecutionTimeLimit,AllowHardTerminate,MultipleInstances
```

Jika hasilnya:

```text
ExecutionTimeLimit : PT2H
AllowHardTerminate : True
```

maka Task Scheduler dapat menghentikan proses setelah dua jam.

Untuk workload besar, rekomendasi konfigurasi adalah:

```text
ExecutionTimeLimit : PT0S
```

`PT0S` berarti tidak memberikan batas maksimum durasi eksekusi dari Task Scheduler.

Script akan berhenti ketika proses selesai atau ketika terjadi error yang menyebabkan proses keluar.

## Mengubah Execution Time Limit melalui PowerShell

Jalankan:

```powershell
$TaskName = "BSRE Daily Certificate Sync"

$Task = Get-ScheduledTask -TaskName $TaskName

$Task.Settings.ExecutionTimeLimit = "PT0S"

Set-ScheduledTask -InputObject $Task
```

Validasi:

```powershell
(Get-ScheduledTask -TaskName "BSRE Daily Certificate Sync").Settings |
Format-List ExecutionTimeLimit,AllowHardTerminate
```

Expected:

```text
ExecutionTimeLimit : PT0S
```

`AllowHardTerminate = True` tidak menjadi masalah selama tidak ada batas waktu yang memaksa Task Scheduler menghentikan proses.

---

# LastTaskResult `267014` / `0x41306`

Jika command:

```powershell
Get-ScheduledTaskInfo -TaskName "BSRE Daily Certificate Sync" |
Format-List LastRunTime,LastTaskResult,NextRunTime
```

menghasilkan:

```text
LastTaskResult : 267014
```

nilai tersebut sama dengan:

```text
0x41306
```

Status tersebut menunjukkan bahwa eksekusi task sebelumnya **terminated / dihentikan**.

Jika kondisi tersebut bersamaan dengan:

```text
ExecutionTimeLimit : PT2H
AllowHardTerminate : True
```

maka penyebab yang sangat mungkin adalah proses mencapai batas dua jam lalu dihentikan oleh Task Scheduler.

Gejalanya dapat berupa file log yang berhenti di tengah proses dan tidak memiliki footer seperti:

```text
End Time
Duration
BSRE Sync SUCCESS
BSRE Sync FAILED
```

Hal ini terjadi karena proses `powershell.exe` yang menjalankan `run_bsre.ps1` ikut dihentikan sebelum sempat menulis bagian akhir log.

---

# Test Task Scheduler Secara Manual

Setelah source code dan konfigurasi Task Scheduler diperbarui, task dapat dijalankan manual dengan:

```powershell
Start-ScheduledTask -TaskName "BSRE Daily Certificate Sync"
```

Cek state:

```powershell
Get-ScheduledTask -TaskName "BSRE Daily Certificate Sync"
```

Ketika masih berjalan:

```text
State : Running
```

Setelah selesai:

```text
State : Ready
```

> `Ready` hanya berarti task saat ini tidak sedang berjalan. Status tersebut tidak otomatis berarti eksekusi terakhir berhasil.

Untuk memastikan hasil eksekusi, selalu periksa `LastTaskResult`.

---

# Monitoring Log Secara Real-Time

Ambil file log terbaru:

```powershell
$log = Get-ChildItem "C:\BSRE-Automation\logs\*.log" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
```

Pantau isi log secara real-time:

```powershell
Get-Content $log.FullName -Wait
```

Dengan heartbeat aktif, output akan bertambah setiap 500 row sehingga proses dapat dipantau tanpa mencetak informasi setiap NIK.

Contoh:

```text
Progress : 500 / 18405 (2.72%) | Elapsed: 00:04:14 | ETA: 02:31:38
Progress : 1000 / 18405 (5.43%) | Elapsed: 00:08:29 | ETA: 02:27:44
Progress : 1500 / 18405 (8.15%) | Elapsed: 00:12:46 | ETA: 02:23:58
```

Untuk keluar dari mode monitoring:

```text
Ctrl + C
```

`Ctrl + C` pada terminal monitoring hanya menghentikan `Get-Content -Wait`, bukan scheduled task yang sedang berjalan.

---

# Validasi Setelah Task Selesai

Jalankan:

```powershell
Get-ScheduledTaskInfo -TaskName "BSRE Daily Certificate Sync" |
Format-List LastRunTime,LastTaskResult,NextRunTime
```

Target eksekusi sukses:

```text
LastTaskResult : 0
```

atau pada Task Scheduler GUI:

```text
Last Run Result : 0x0
```

Artinya proses selesai normal.

Kemudian periksa footer file log.

Eksekusi sukses seharusnya memiliki informasi seperti:

```text
End Time   : 12-Sep-2026_14:35:20
Duration   : 03:14:17
BSRE Sync SUCCESS : 2026-09-12 14:35:20
============================================================
```

---

# Pemeriksaan Status Task

Untuk melihat status task:

```powershell
Get-ScheduledTask -TaskName "BSRE Daily Certificate Sync"
```

Contoh ketika masih berjalan:

```text
TaskPath                                       TaskName                          State
--------                                       --------                          -----
\                                              BSRE Daily Certificate Sync       Running
```

Contoh ketika sudah berhenti:

```text
TaskPath                                       TaskName                          State
--------                                       --------                          -----
\                                              BSRE Daily Certificate Sync       Ready
```

Jika state `Ready`, periksa hasil terakhir dengan:

```powershell
Get-ScheduledTaskInfo -TaskName "BSRE Daily Certificate Sync" |
Format-List LastRunTime,LastTaskResult,NextRunTime
```

---

# Verifikasi Konfigurasi Task Scheduler

## Action

Periksa:

```powershell
(Get-ScheduledTask -TaskName "BSRE Daily Certificate Sync").Actions |
Format-List *
```

Konfigurasi yang direkomendasikan:

```text
Execute          : powershell.exe
Arguments        : -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
WorkingDirectory : C:\BSRE-Automation
```

## Settings

Periksa:

```powershell
(Get-ScheduledTask -TaskName "BSRE Daily Certificate Sync").Settings |
Format-List *
```

Rekomendasi utama:

```text
MultipleInstances  : IgnoreNew
ExecutionTimeLimit : PT0S
AllowHardTerminate : True
```

`MultipleInstances : IgnoreNew` mencegah task baru dijalankan apabila instance sebelumnya masih aktif.

---

# Rekomendasi Production untuk Proses All Rows

Untuk jumlah data besar seperti belasan ribu row, rekomendasi konfigurasi:

```text
Task Name                  : BSRE Daily Certificate Sync
Mode                       : All Rows
Heartbeat                  : Every 500 rows
Execution Time Limit       : Unlimited / PT0S
Concurrent execution       : Do not start a new instance
Run with highest privileges: Yes
Logging                    : Enabled
Retry on failure           : Enabled
```

Alur operasional:

```text
Task Scheduler
      |
      v
run_bsre.ps1
      |
      v
Python All-Rows
      |
      +--> Cek API BSrE
      |
      +--> Heartbeat setiap 500 row
      |
      +--> Differential Update O/P/Q/R
      |
      +--> Batch Update Google Sheets
      |
      v
Summary + Footer Log
```

---

# Catatan Operasional

Jangan menjalankan script Python manual dan scheduled task secara bersamaan.

Dua instance yang berjalan paralel dapat:

```text
melakukan request API BSrE secara bersamaan
memproses row yang sama secara bersamaan
melakukan batch update Google Sheets pada waktu yang sama
meningkatkan beban API
meningkatkan risiko race condition
```

Gunakan konfigurasi Task Scheduler:

```text
If the task is already running:
Do not start a new instance
```

atau pastikan:

```text
MultipleInstances : IgnoreNew
```

Jika ingin melakukan test manual melalui Task Scheduler, gunakan:

```powershell
Start-ScheduledTask -TaskName "BSRE Daily Certificate Sync"
```

bukan menjalankan script Python secara paralel dengan task yang sudah aktif.

---

# Quick Validation Checklist

Setelah konfigurasi heartbeat dan Task Scheduler diperbarui:

```text
[ ] Source All Rows sudah menggunakan heartbeat setiap 500 row
[ ] run_bsre.ps1 tetap menggunakan Python dari venv
[ ] ExecutionTimeLimit = PT0S
[ ] MultipleInstances = IgnoreNew
[ ] Task dapat dijalankan manual
[ ] State berubah menjadi Running saat proses aktif
[ ] File log baru terbentuk
[ ] Heartbeat muncul setiap 500 row
[ ] Heartbeat terakhir menunjukkan 100%
[ ] Google Spreadsheet berhasil diupdate
[ ] Statistik akhir muncul
[ ] Footer log muncul
[ ] State kembali menjadi Ready
[ ] LastTaskResult = 0
```

# Penggunaan

Project ini ditujukan untuk otomatisasi administrasi dan sinkronisasi informasi sertifikat elektronik BSrE pada lingkungan yang memiliki otorisasi resmi untuk:

- mengakses API BSrE;
- membaca NIK pengguna;
- mengakses Google Spreadsheet terkait;
- memperbarui status sertifikat elektronik.

Gunakan credential berdasarkan prinsip:

```text
Least Privilege
```

dan hindari menyimpan username, password, token, maupun Service Account credential langsung di source code.

---

# Author

**ajung5**

GitHub:

```text
https://github.com/ajung5
```
