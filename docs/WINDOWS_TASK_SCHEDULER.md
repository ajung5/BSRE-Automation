# Windows Task Scheduler

Panduan ini digunakan untuk menjalankan mode **all rows** secara otomatis menggunakan Windows Task Scheduler.

## Alur

```text
Task Scheduler
      │
      ▼
powershell.exe
      │
      ▼
run_bsre.ps1
      │
      ▼
venv\Scripts\python.exe
      │
      ▼
cek_nik_bsre_spreadseheet_merge_all_rows.py
      │
      ├── API BSrE
      ├── Google Sheets
      └── logs\
```

## 1. Lokasi Project

Wrapper saat ini menggunakan:

```powershell
$BaseDir = "C:\BSRE-Automation"
```

Pastikan repository berada pada lokasi tersebut atau ubah `$BaseDir` pada `run_bsre.ps1`.

## 2. Test Manual

Sebelum membuat scheduled task:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

Pastikan:

- virtual environment tersedia;
- `.env` dapat dibaca;
- credential Google tersedia;
- API dapat diakses;
- Google Spreadsheet dapat diakses;
- file log berhasil dibuat.

## 3. Create Task

Buka:

```text
Win + R
taskschd.msc
```

Pilih:

```text
Create Task...
```

### General

Contoh:

```text
Name        : BSRE Daily Certificate Sync
Description : Sinkronisasi harian status pengguna dan sertifikat BSrE
```

Rekomendasi:

```text
Run whether user is logged on or not
Run with highest privileges
```

## 4. Trigger

Contoh jadwal harian:

```text
Daily
01:00
Every 1 day
Enabled
```

Sesuaikan jadwal dengan kebutuhan organisasi.

## 5. Action

Program:

```text
powershell.exe
```

Arguments:

```text
-NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

Start in:

```text
C:\BSRE-Automation
```

## 6. Settings

Direkomendasikan:

```text
Allow task to be run on demand
Run task as soon as possible after a scheduled start is missed
```

Pertimbangkan konfigurasi instance agar tidak menjalankan dua proses sinkronisasi besar secara bersamaan.

## 7. Validasi

Klik kanan task:

```text
Run
```

Kemudian periksa:

```text
Last Run Result
C:\BSRE-Automation\logs\
```

Nilai exit code `0` menunjukkan proses Python selesai tanpa error yang diteruskan oleh wrapper.

## 8. Security

Account Windows yang menjalankan task harus memiliki akses hanya sesuai kebutuhan ke:

```text
C:\BSRE-Automation\
.env
google_credentials.json
venv\
logs\
```

Jangan gunakan akun dengan privilege lebih tinggi daripada yang diperlukan.
