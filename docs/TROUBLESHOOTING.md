# Troubleshooting

## `ModuleNotFoundError`

Pastikan virtual environment aktif dan dependency sudah terpasang:

```bash
python -m pip install -r requirements.txt
```

Untuk test, jalankan dari root repository:

```bash
python -m unittest tests.test_both_bsre_modes
```

Jangan menjalankan file test dari directory yang menyebabkan root project tidak berada di Python import path.

## Google Sheets `403`

Periksa:

1. Google Service Account benar.
2. Spreadsheet sudah di-share ke `client_email`.
3. Permission minimal `Editor`.
4. `SPREADSHEET_ID` benar.

## Worksheet Tidak Ditemukan

Pastikan:

```env
WORKSHEET_NAME=...
```

sama persis dengan nama tab Google Sheets.

## API Timeout / Unauthorized

Periksa:

- `BSRE_BASE_URL`;
- username/password;
- konektivitas host;
- firewall/proxy;
- availability API;
- authorization akun.

Jangan menulis credential ke issue GitHub atau log publik.

## Task Scheduler Berjalan tetapi Log Berhenti di Awal

Periksa:

- Python path di `run_bsre.ps1`;
- virtual environment;
- `.env`;
- credential JSON;
- akses network account Task Scheduler;
- apakah process masih berjalan;
- heartbeat pada mode all-rows.

## Task Scheduler Tidak Menjalankan Script

Periksa konfigurasi:

```text
Program/script : powershell.exe
Arguments      : -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
Start in       : C:\BSRE-Automation
```

Periksa juga `Last Run Result` dan Windows Task Scheduler History.

## Data Tidak Berubah

Differential update sengaja tidak menulis cell jika hasil API sama dengan nilai spreadsheet.

Periksa statistik:

```text
Total row berubah
Total row tanpa perubahan
Total cell berubah
```

Nilai `0` pada perubahan bukan otomatis berarti proses gagal.
