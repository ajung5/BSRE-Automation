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

| Kolom | Fungsi |
|---|---|
| `NIK` | Sumber NIK yang diperiksa |
| `O` | Status Pengguna |
| `P` | Status Sertifikat |
| `Q` | Tanggal terbit |
| `R` | Tanggal berakhir |

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

| Status API | Status Pengguna | Status Sertifikat |
|---|---|---|
| `ISSUE` | Verified | Issued |
| `REVOKE` | Verified | Revoke |
| `RENEW` | Verified | Renew |
| `NO_CERTIFICATE` | Verified | New |
| `EXPIRED` | Verified | Expired |
| `NOT_REGISTERED` | Tidak diubah | Tidak diubah |

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

Repository menyediakan unit test untuk memastikan logic utama tetap bekerja setelah source code diubah.

Unit test **tidak dimaksudkan untuk mengetes credential atau koneksi produksi**. Test menggunakan mock/fake object sehingga:

- tidak mengubah Google Sheets asli;
- tidak melakukan write ke spreadsheet produksi;
- tidak membutuhkan API BSrE nyata;
- request API pada test digantikan dengan response mock;
- koneksi Google Sheets pada integration-style unit test digantikan dengan worksheet/service palsu.

Walaupun tidak mengakses layanan eksternal, dependency Python aplikasi tetap harus ter-install karena kedua module utama di-import oleh test.

---

## File Unit Test

Folder:

```text
test/
```

### `test_cek_nik_bsre.py`

Test awal untuk memvalidasi fungsi utama script filtered.

### `test_both_bsre_modes.py`

Test suite untuk memastikan **kedua script** mempunyai logic yang benar dan konsisten:

```text
cek_nik_bsre_spreadseheet_merge.py
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

---

## Apa yang Diuji

### 1. Normalisasi Tanggal

Memastikan berbagai format:

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

Tujuannya agar format tanggal yang berbeda tidak dianggap sebagai perubahan data.

---

### 2. Differential Update

Memastikan nilai yang sama tidak dianggap berubah.

Contoh:

```text
Lama : 12-Agu-2026
Baru : 2026-08-12
```

Hasil:

```text
Tidak berubah
```

Sedangkan:

```text
Lama : Issued
Baru : Expired
```

harus dianggap:

```text
Berubah
```

---

### 3. Mapping Status API BSrE

Memastikan response:

```json
{
  "status": "ISSUE"
}
```

menghasilkan:

```text
Status Pengguna    = Verified
Status Sertifikat  = Issued
update             = True
```

---

### 4. `NOT_REGISTERED`

Memastikan `NOT_REGISTERED` tidak menghapus atau menimpa status O/P.

Expected:

```text
update = False
```

---

### 5. Pemilihan Sertifikat Terbaru

Jika API profile mengembalikan:

```text
12-08-2026
12-08-2027
12-08-2028
```

test memastikan script memilih:

```text
12-08-2028
```

sebagai tanggal berakhir terbaru.

Tanggal terbit kemudian menjadi:

```text
12-08-2026
```

karena logic aplikasi menggunakan:

```text
Tanggal Terbit = Tanggal Berakhir - 2 Tahun
```

---

### 6. `NO_CERTIFICATE`

Memastikan profile tanpa sertifikat menghasilkan:

```text
status = NO_CERTIFICATE
```

dan tanggal kosong.

---

### 7. Profile `404 / NOT_FOUND`

Memastikan HTTP `404` dipetakan menjadi:

```text
status = NOT_FOUND
```

---

### 8. Filtered Mode

Test memastikan:

```text
hiddenByFilter = true
```

atau:

```text
hiddenByUser = true
```

tidak ikut diproses.

Contoh:

```text
Row 2 = visible
Row 3 = hiddenByFilter
```

Expected:

```text
API dipanggil untuk Row 2
API TIDAK dipanggil untuk Row 3
```

Ini melindungi behavior utama:

```text
cek_nik_bsre_spreadseheet_merge.py
```

---

### 9. All-Rows Mode

Test memastikan:

```text
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

memproses seluruh row data tanpa bergantung pada filter Google Sheets.

Jika terdapat dua row:

```text
Row 2
Row 3
```

Expected:

```text
API dipanggil untuk Row 2
API dipanggil untuk Row 3
```

---

### 10. Update Hanya Cell yang Berubah

Contoh test:

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

Test ini penting untuk mencegah regression pada mekanisme differential update.

---

# Menjalankan Unit Test di Windows

Pastikan terminal berada di **root repository**:

```powershell
cd C:\BSRE-Automation
```

## Menjalankan Semua Test

Jika menggunakan virtual environment:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s test -p "test_*.py" -v
```

Jika menggunakan Python global:

```powershell
python -m unittest discover -s test -p "test_*.py" -v
```

Command ini akan mencari seluruh file:

```text
test/test_*.py
```

dan menjalankannya.

---

## Menjalankan Hanya Test Kedua Mode

Dengan Python global:

```powershell
python test\test_both_bsre_modes.py
```

Dengan virtual environment:

```powershell
.\venv\Scripts\python.exe test\test_both_bsre_modes.py
```

---

## Menjalankan Test Lama Saja

```powershell
python test\test_cek_nik_bsre.py
```

---

# Menjalankan Unit Test di macOS

Masuk ke root repository:

```bash
cd /path/ke/BSRE-Automation
```

## Menjalankan Semua Test

Dengan Python global:

```bash
python3 -m unittest discover -s test -p "test_*.py" -v
```

Dengan virtual environment:

```bash
./venv/bin/python -m unittest discover -s test -p "test_*.py" -v
```

---

## Menjalankan Hanya Test Kedua Mode

```bash
python3 test/test_both_bsre_modes.py
```

atau dengan virtual environment:

```bash
./venv/bin/python test/test_both_bsre_modes.py
```

---

## Menjalankan Test Lama Saja

```bash
python3 test/test_cek_nik_bsre.py
```

---

# Membaca Hasil Unit Test

Jika semua test berhasil:

```text
test_ambil_nilai_cell ... ok
test_normalisasi_tanggal_pada_kedua_script ... ok
test_issue ... ok
test_not_registered_tidak_update ... ok
test_proses_filtered_hanya_memanggil_api_untuk_row_visible ... ok
test_proses_all_rows_memanggil_api_untuk_semua_row ... ok
test_all_rows_hanya_update_cell_yang_berubah ... ok

----------------------------------------------------------------------
Ran XX tests in X.XXXs

OK
```

Arti:

```text
ok
```

berarti test tersebut lolos.

Jika terdapat:

```text
FAIL
```

berarti hasil aktual berbeda dari expected value test.

Jika terdapat:

```text
ERROR
```

berarti test gagal dieksekusi, misalnya karena import/dependency bermasalah atau terdapat exception pada source.

---

# Workflow Testing yang Direkomendasikan

Sebelum menjalankan automation produksi setelah perubahan source:

```text
Edit source
    |
    v
Jalankan unit test
    |
    +-- FAIL / ERROR --> perbaiki source/test
    |
    `-- OK
         |
         v
   Jalankan manual
         |
         v
   Verifikasi Google Sheets
         |
         v
   Deploy ke Task Scheduler
```

Di Windows:

```powershell
git pull
.\venv\Scripts\python.exe -m unittest discover -s test -p "test_*.py" -v
```

Jika hasil:

```text
OK
```

baru lanjutkan pengujian manual atau automation.

Di macOS:

```bash
git pull
./venv/bin/python -m unittest discover -s test -p "test_*.py" -v
```

---

# Troubleshooting Unit Test

## `ModuleNotFoundError: No module named 'cek_nik_bsre_spreadseheet_merge'`

Pastikan menjalankan test dari **root repository**, bukan dari dalam folder `test`.

Benar:

```text
C:\BSRE-Automation>
```

kemudian:

```powershell
python -m unittest discover -s test -p "test_*.py" -v
```

Jangan terlebih dahulu masuk ke:

```text
C:\BSRE-Automation\test>
```

karena module utama berada satu level di atas folder test.

Pada macOS juga jalankan dari:

```text
BSRE-Automation/
```

bukan:

```text
BSRE-Automation/test/
```

---

## `ModuleNotFoundError: No module named 'gspread'`

Dependency belum tersedia pada interpreter yang menjalankan test.

Windows:

```powershell
python -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

macOS:

```bash
python3 -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

Jika menggunakan virtual environment, pastikan install dilakukan menggunakan interpreter venv.

---

## Apakah Unit Test Memerlukan `.env`?

Untuk test yang menggunakan mock, credential asli tidak diperlukan untuk mengakses API atau Google Sheets.

Namun script utama tetap melakukan:

```python
load_dotenv()
```

ketika di-import.

Test kemudian mengganti nilai konfigurasi dan koneksi yang diperlukan dengan mock/fake object.

Karena itu unit test tidak boleh dianggap sebagai pengujian credential produksi.

Untuk memastikan credential dan koneksi produksi bekerja, lakukan test terpisah atau jalankan script secara manual pada environment yang memang memiliki izin.

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
