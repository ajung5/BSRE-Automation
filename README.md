# BSRE Automation

Automasi pengecekan **status pengguna dan sertifikat elektronik BSrE** berdasarkan data NIK pada Google Spreadsheet.

Script membaca NIK dari worksheet, melakukan pengecekan ke API BSrE, lalu memperbarui status pengguna, status sertifikat, tanggal terbit, dan tanggal berakhir secara otomatis pada Google Sheets.

## Fitur

* Membaca data NIK langsung dari Google Spreadsheet.
* Hanya memproses **row yang terlihat**.
* Row yang disembunyikan oleh filter atau secara manual tidak diproses.
* Mengecek status sertifikat melalui API BSrE.
* Mengecek profile sertifikat untuk memperoleh tanggal berlaku.
* Memetakan status API BSrE ke status yang lebih mudah dibaca.
* Melakukan batch update ke Google Sheets.
* Menampilkan statistik hasil pengecekan pada akhir proses.
* Menyediakan PowerShell wrapper untuk menjalankan script menggunakan virtual environment.
* Menyimpan output setiap eksekusi ke file log terpisah.

---

## Alur Kerja

```text
Google Spreadsheet
        |
        v
Ambil row yang terlihat
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
              Batch Update
              Google Sheets
```

---

## Struktur Repository

```text
BSRE-Automation/
├── cek_nik_bsre_spreadseheet_merge.py
├── run_bsre.ps1
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

## Persyaratan

### Sistem

Disarankan menggunakan:

* Windows 10 / Windows 11 / Windows Server
* Python 3.10+
* PowerShell
* Google Service Account
* Credential API BSrE yang valid

### Python Dependency

Dependency yang digunakan oleh aplikasi:

```text
gspread
requests
python-dateutil
python-dotenv
tqdm
google-auth
google-api-python-client
```

---

# Instalasi

## 1. Clone Repository

```powershell
git clone https://github.com/ajung5/BSRE-Automation.git C:\BSRE-Automation
```

Masuk ke directory:

```powershell
cd C:\BSRE-Automation
```

---

## 2. Membuat Virtual Environment

```powershell
python -m venv venv
```

Aktifkan:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Install Dependency

```powershell
pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

---

# Konfigurasi

## File `.env`

Buat file:

```text
.env
```

pada root directory repository.

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

> Jangan commit file `.env` karena berisi credential dan konfigurasi sensitif.

---

# Google Service Account

Simpan credential Google Service Account dengan nama:

```text
google_credentials.json
```

pada root repository.

Contoh:

```text
C:\BSRE-Automation\google_credentials.json
```

Nama/path file harus sesuai dengan:

```env
GOOGLE_CREDENTIALS=google_credentials.json
```

---

## Memberikan Hak Akses Spreadsheet

Buka file:

```text
google_credentials.json
```

kemudian cari alamat:

```json
"client_email": "service-account-name@project-id.iam.gserviceaccount.com"
```

Share Google Spreadsheet tujuan ke alamat tersebut.

Berikan permission:

```text
Editor
```

karena aplikasi perlu mengubah data spreadsheet.

---

# Menjalankan Script

## Cara 1 — Python Langsung

Aktifkan virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Kemudian:

```powershell
python .\cek_nik_bsre_spreadseheet_merge.py
```

---

## Cara 2 — Menggunakan Python dari Virtual Environment

Tidak perlu mengaktifkan venv terlebih dahulu:

```powershell
.\venv\Scripts\python.exe .\cek_nik_bsre_spreadseheet_merge.py
```

---

# Menjalankan dengan PowerShell Wrapper

Repository menyediakan:

```text
run_bsre.ps1
```

Wrapper ini menggunakan directory default:

```powershell
$BaseDir = "C:\BSRE-Automation"
```

Jika repository disimpan di lokasi berbeda, sesuaikan:

```powershell
$BaseDir = "PATH_REPOSITORY"
```

Contoh menjalankan:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

---

## Fungsi `run_bsre.ps1`

Wrapper akan:

1. menentukan lokasi project;
2. menggunakan Python dari virtual environment;
3. memastikan directory `logs` tersedia;
4. membuat file log untuk setiap eksekusi;
5. menjalankan script Python;
6. menangkap `stdout` dan `stderr`;
7. mencatat status proses;
8. mencatat exit code jika proses gagal.

---

# Logging

Log disimpan di:

```text
C:\BSRE-Automation\logs\
```

Format filename:

```text
bsre_DD-Bbb-YYYY_HH-mm-ss.log
```

Contoh:

```text
bsre_10-Sep-2026_08-04-30.log
```

Contoh isi:

```text
============================================================
BSRE Sync Start : 2026-09-10 08:04:30
============================================================

...

BSRE Sync SUCCESS : 2026-09-10 08:05:42

============================================================
```

Jika gagal:

```text
BSRE Sync FAILED - Exit Code: 1
```

### Catatan Windows

Karakter:

```text
:
```

tidak dapat digunakan pada nama file Windows.

Karena itu waktu filename menggunakan:

```text
HH-mm-ss
```

bukan:

```text
HH:mm:ss
```

---

# Row yang Diproses

Salah satu fitur penting script ini adalah hanya memproses **row yang terlihat**.

Script membaca metadata Google Sheets:

```text
hiddenByFilter
```

dan:

```text
hiddenByUser
```

Row akan dilewati apabila:

```text
hiddenByFilter = true
```

atau:

```text
hiddenByUser = true
```

Dengan mekanisme ini, pengguna dapat menentukan subset data yang akan diproses langsung melalui filter Google Sheets.

Contoh:

```text
1000 row total
↓
Filter OPD tertentu
↓
120 row terlihat
↓
Hanya 120 row yang diperiksa ke API BSrE
```

---

# Proses API BSrE

Untuk setiap NIK yang terlihat, script melakukan dua request utama.

## Status Sertifikat

```http
GET /api/user/status/{nik}
```

Digunakan untuk menentukan:

```text
Status Pengguna
Status Sertifikat
```

---

## Profile Sertifikat

```http
GET /api/user/profile/{nik}
```

Digunakan untuk mendapatkan informasi sertifikat.

Jika terdapat beberapa sertifikat, script memilih sertifikat dengan:

```text
berlaku_sampai
```

yang paling baru.

---

# Perhitungan Tanggal Sertifikat

API profile digunakan untuk mendapatkan:

```text
berlaku_sampai
```

Kemudian tanggal terbit saat ini dihitung dengan:

```text
Tanggal Terbit = Tanggal Berakhir - 2 Tahun
```

Contoh:

```text
Tanggal berakhir : 12-08-2028
```

maka:

```text
Tanggal terbit   : 12-08-2026
```

> Mekanisme ini menggunakan asumsi masa berlaku sertifikat selama dua tahun. Jika API BSrE menyediakan tanggal penerbitan secara eksplisit atau kebijakan masa berlaku berubah, logika ini sebaiknya diperbarui.

---

# Statistik Eksekusi

Setelah seluruh data selesai diproses, script menampilkan ringkasan.

Contoh:

```text
======================================================================
 HASIL PENGECEKAN
======================================================================

Row terlihat             : 120
Row hidden               : 880
Total row yang diubah    : 110
```

### Statistik Status

```text
ISSUE
EXPIRED
REVOKE
RENEW
NO_CERTIFICATE
NOT_REGISTERED
Tidak diubah
```

### Statistik Profile/Tanggal

```text
Tanggal ditemukan
Tidak ada sertifikat
NIK tidak ditemukan
Tanggal tidak valid
NIK kosong
Error gabungan
```

---

# Troubleshooting

## `google_credentials.json tidak ditemukan`

Pastikan file:

```text
google_credentials.json
```

tersedia di root repository.

Atau periksa konfigurasi:

```env
GOOGLE_CREDENTIALS=google_credentials.json
```

---

## `SPREADSHEET_ID belum diisi`

Pastikan `.env` berisi:

```env
SPREADSHEET_ID=xxxxxxxxxxxxxxxx
```

ID dapat diperoleh dari URL Google Sheets.

Contoh:

```text
https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit
```

Maka:

```env
SPREADSHEET_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz
```

---

## Error 403

Contoh:

```text
APIError: [403]: The caller does not have permission
```

Penyebab paling umum adalah Service Account belum memiliki akses ke spreadsheet.

Solusi:

1. buka `google_credentials.json`;
2. cari `client_email`;
3. share Google Spreadsheet ke email tersebut;
4. berikan permission **Editor**.

---

## Error 401 BSrE

Contoh:

```text
UNAUTHORIZED
```

Periksa:

```env
BSRE_USERNAME=
BSRE_PASSWORD=
```

Pastikan credential masih aktif dan diizinkan mengakses API BSrE.

---

## Kolom `NIK` Tidak Ditemukan

Header spreadsheet harus memiliki nama:

```text
NIK
```

Script mendeteksi posisi header tersebut secara dinamis.

Jika NIK tidak berada di kolom `C`, script akan memberikan peringatan tetapi tetap menggunakan posisi kolom yang ditemukan.

---

# Keamanan

File berikut **tidak boleh disimpan ke repository**:

```text
.env
google_credentials.json
*.env
*credentials*.json
```

`.gitignore` repository saat ini sudah mencakup credential utama tersebut.

Disarankan juga mengabaikan log:

```gitignore
logs/
*.log
```

karena log dapat mengandung informasi operasional.

---

## Rekomendasi `.gitignore`

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

---

## Jika Credential Pernah Terlanjur Masuk Git

Menghapus file saja tidak cukup apabila secret pernah masuk ke commit.

Segera:

1. **rotate/revoke credential**;
2. buat credential baru;
3. hapus credential dari Git history jika diperlukan;
4. tambahkan file ke `.gitignore`.

---

# Penggunaan

Project ini ditujukan untuk otomatisasi administrasi dan sinkronisasi informasi sertifikat elektronik BSrE pada lingkungan yang memiliki otorisasi resmi untuk:

* mengakses API BSrE;
* membaca NIK pengguna;
* mengakses Google Spreadsheet terkait;
* memperbarui status sertifikat elektronik.

Gunakan seluruh credential berdasarkan prinsip:

```text
Least Privilege
```

dan hindari menyimpan username, password, token, maupun Service Account credential langsung di source code.

---

# Author

**ajung5**

GitHub:

https://github.com/ajung5
