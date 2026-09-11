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
- Menyediakan unit test untuk memvalidasi kedua mode tanpa mengubah Google Sheets atau mengakses API BSrE nyata.

---

# Struktur Repository

```text
BSRE-Automation/
├── cek_nik_bsre_spreadseheet_merge.py
├── cek_nik_bsre_spreadseheet_merge_all_rows.py
├── run_bsre.ps1
├── tests/
│   └── test_both_bsre_modes.py
├── .gitignore
├── README.md
├── .env                       # tidak disimpan ke Git
├── google_credentials.json    # tidak disimpan ke Git
├── venv/                      # tidak disimpan ke Git
└── logs/
```

---

# Kolom Google Spreadsheet

| Kolom | Fungsi |
|---|---|
| `NIK` | Sumber NIK yang diperiksa |
| `O` | Status Pengguna |
| `P` | Status Sertifikat |
| `Q` | Tanggal terbit |
| `R` | Tanggal berakhir |

Script memastikan:

```text
Q1 = Tanggal terbit
R1 = Tanggal berakhir
```

---

# Differential Update

Script membandingkan hasil terbaru dari API dengan nilai yang sudah ada di spreadsheet.

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

Tanggal dinormalisasi sebelum dibandingkan sehingga nilai seperti:

```text
12-Agu-2026
2026-08-12
12/08/2026
```

dianggap sebagai tanggal yang sama.

---

# Mapping Status BSrE

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

Direkomendasikan:

- Python 3.10+
- Windows 10/11 atau Windows Server untuk automation
- macOS/Linux untuk penggunaan manual
- PowerShell untuk wrapper Windows
- Google Service Account
- credential API BSrE yang valid

Dependency:

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

# Instalasi Windows

```powershell
git clone https://github.com/ajung5/BSRE-Automation.git C:\BSRE-Automation
cd C:\BSRE-Automation

python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

---

# Instalasi macOS

```bash
git clone https://github.com/ajung5/BSRE-Automation.git
cd BSRE-Automation

python3 -m venv venv
source venv/bin/activate

python3 -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

---

# Konfigurasi `.env`

```env
BSRE_BASE_URL=https://example-bsre-api
BSRE_USERNAME=your_username
BSRE_PASSWORD=your_password

GOOGLE_CREDENTIALS=google_credentials.json
SPREADSHEET_ID=your_google_spreadsheet_id
WORKSHEET_NAME=Nama Worksheet
```

> Jangan commit `.env` atau credential Google Service Account ke repository.

---

# Menjalankan Script Manual

## Windows — Filtered

```powershell
cd C:\BSRE-Automation
python .\cek_nik_bsre_spreadseheet_merge.py
```

Dengan venv:

```powershell
.\venv\Scripts\python.exe .\cek_nik_bsre_spreadseheet_merge.py
```

## Windows — All Rows

```powershell
python .\cek_nik_bsre_spreadseheet_merge_all_rows.py
```

atau:

```powershell
.\venv\Scripts\python.exe .\cek_nik_bsre_spreadseheet_merge_all_rows.py
```

## macOS — Filtered

```bash
python3 cek_nik_bsre_spreadseheet_merge.py
```

## macOS — All Rows

```bash
python3 cek_nik_bsre_spreadseheet_merge_all_rows.py
```

---

# PowerShell Wrapper

Repository menyediakan:

```text
run_bsre.ps1
```

Wrapper menjalankan:

```text
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

Contoh:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

Wrapper:

1. memakai Python dari virtual environment;
2. memastikan folder `logs` tersedia;
3. membuat file log setiap eksekusi;
4. menjalankan script all-rows;
5. menangkap `stdout` dan `stderr`;
6. mencatat status proses;
7. mencatat waktu selesai dan durasi;
8. mengembalikan exit code ke Task Scheduler.

---

# Logging

Contoh footer log:

```text
End Time   : 11-Sep-2026_18:42:12
Duration   : 00:42:11
BSRE Sync SUCCESS : 2026-09-11 18:42:12
============================================================
```

---

# Unit Testing

Repository menyediakan:

```text
tests/test_both_bsre_modes.py
```

Test tersebut menguji kedua script:

```text
cek_nik_bsre_spreadseheet_merge.py
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

Unit test menggunakan `unittest` dan `unittest.mock`, sehingga:

- tidak membutuhkan `pytest`;
- tidak melakukan request nyata ke API BSrE;
- tidak mengubah Google Sheets produksi;
- tidak melakukan write ke spreadsheet asli;
- tidak memerlukan credential produksi untuk melakukan request;
- menggunakan fake worksheet, fake response, dan mock API.

Dependency aplikasi tetap harus terpasang karena kedua module utama tetap di-import saat test dijalankan.

---

## Cakupan Unit Test

`tests/test_both_bsre_modes.py` memiliki **15 test method**.

### Normalisasi tanggal

Memastikan format:

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

### Differential comparison

Memastikan:

```text
12-Agu-2026
2026-08-12
```

dianggap tanggal yang sama.

Dan:

```text
Issued
Expired
```

dianggap berbeda.

### Mapping ISSUE

Mock:

```json
{"status": "ISSUE"}
```

Expected:

```text
update             = True
status_api         = ISSUE
status_pengguna    = Verified
status_sertifikat  = Issued
```

### NOT_REGISTERED

Expected:

```text
update = False
```

Artinya kolom O/P tidak ditimpa.

### Pemilihan sertifikat terbaru

Jika profile mock memiliki:

```text
12-08-2026
12-08-2028
12-08-2027
```

script harus memilih:

```text
12-08-2028
```

### NO_CERTIFICATE

Memastikan profile tanpa sertifikat menghasilkan:

```text
status = NO_CERTIFICATE
```

### HTTP 404

Memastikan HTTP 404 dipetakan menjadi:

```text
status = NOT_FOUND
```

### Filtered Mode

Memastikan row:

```text
hiddenByFilter = true
```

atau:

```text
hiddenByUser = true
```

tidak diproses oleh script filtered.

### All Rows Mode

Memastikan script all-rows tetap memproses seluruh row.

### Differential Cell Update

Jika hanya:

```text
P3 = Issued -> Expired
```

yang berubah, expected batch update hanya:

```text
P3 = Expired
```

bukan seluruh O3:R3.

---

# Menjalankan Unit Test di Windows

**Jalankan dari root repository:**

```powershell
cd C:\BSRE-Automation
```

Dengan virtual environment:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Dengan Python global:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Menjalankan hanya file test saat ini:

```powershell
python -m unittest discover -s tests -p "test_both_bsre_modes.py" -v
```

Dengan venv:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_both_bsre_modes.py" -v
```

> Direkomendasikan menggunakan `unittest discover`, bukan menjalankan file test dari dalam folder `tests`, agar module utama di root repository dapat di-import dengan benar.

---

# Menjalankan Unit Test di macOS

Masuk ke root repository:

```bash
cd /path/ke/BSRE-Automation
```

Dengan virtual environment:

```bash
./venv/bin/python -m unittest discover -s tests -p "test_*.py" -v
```

Dengan Python global:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Menjalankan hanya file test saat ini:

```bash
python3 -m unittest discover -s tests -p "test_both_bsre_modes.py" -v
```

---

# Hasil Unit Test

Jika seluruh test berhasil:

```text
----------------------------------------------------------------------
Ran 15 tests in X.XXXs

OK
```

| Status | Arti |
|---|---|
| `ok` | Test berhasil |
| `FAIL` | Hasil aktual berbeda dari expected |
| `ERROR` | Terjadi exception, error import, atau dependency |

---

# Workflow yang Direkomendasikan

```text
Edit source
    |
    v
Unit Test
    |
    +-- FAIL / ERROR --> Perbaiki
    |
    `-- OK
         |
         v
Test manual
         |
         v
Verifikasi Google Sheets
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

Pastikan test dijalankan dari root repository.

Windows:

```text
C:\BSRE-Automation>
```

macOS:

```text
.../BSRE-Automation/
```

Gunakan `unittest discover`:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

atau:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## `ModuleNotFoundError: No module named 'gspread'`

Install dependency dengan interpreter yang digunakan untuk test.

Windows:

```powershell
python -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

macOS:

```bash
python3 -m pip install gspread requests python-dateutil python-dotenv tqdm google-auth google-api-python-client
```

---

# Keamanan

Jangan commit:

```text
.env
google_credentials.json
*.env
*credentials*.json
*.log
```

Rekomendasi `.gitignore`:

```gitignore
.env
*.env
google_credentials.json
*credentials*.json

logs/
*.log

venv/
.venv/

__pycache__/
*.py[cod]

.vscode/

Thumbs.db
.DS_Store
```

---

# Author

**ajung5**

GitHub: `https://github.com/ajung5`
