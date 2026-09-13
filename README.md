# BSRE Automation

Automasi sinkronisasi **status pengguna dan sertifikat elektronik BSrE** dari API ke Google Spreadsheet berdasarkan NIK.

Project menyediakan dua mode pemrosesan:

- **Filtered / Visible Rows** — hanya memproses row yang terlihat.
- **All Rows** — memproses seluruh row tanpa dipengaruhi filter/hidden row.

Kedua mode menggunakan **differential update**: hanya cell pada kolom **O, P, Q, dan R yang benar-benar berubah** yang ditulis kembali ke Google Sheets.

> **Catatan:** repository ini merupakan utility automation independen. Pastikan penggunaan API, credential, dan data NIK sesuai kewenangan serta kebijakan organisasi Anda.

## Fitur Utama

- Sinkronisasi status pengguna dan sertifikat BSrE.
- Dukungan mode filtered dan all-rows.
- Differential update untuk mengurangi write ke Google Sheets.
- Normalisasi tanggal sebelum perbandingan.
- Batch update Google Sheets.
- Statistik status dan perubahan pada akhir proses.
- Progress heartbeat pada proses all-rows.
- PowerShell wrapper untuk Windows automation.
- Logging per eksekusi.
- Dukungan Windows Task Scheduler.
- Unit test tanpa menulis ke Google Sheets/API produksi.

## Struktur Utama

```text
BSRE-Automation/
├── cek_nik_bsre_spreadseheet_merge.py
├── cek_nik_bsre_spreadseheet_merge_all_rows.py
├── run_bsre.ps1
├── requirements.txt
├── .env.example
├── tests/
├── docs/
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Quick Start

```bash
git clone https://github.com/ajung5/BSRE-Automation.git
cd BSRE-Automation

python -m venv venv
```

Windows:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

Buat konfigurasi dari template:

```text
.env.example → .env
```

Kemudian sesuaikan credential BSrE, Google Service Account, Spreadsheet ID, dan Worksheet.

Menjalankan mode seluruh row:

```bash
python cek_nik_bsre_spreadseheet_merge_all_rows.py
```

Menjalankan mode filtered:

```bash
python cek_nik_bsre_spreadseheet_merge.py
```

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [Installation](docs/INSTALLATION.md) | Instalasi Windows, macOS, dan Linux |
| [Configuration](docs/CONFIGURATION.md) | `.env`, Google Service Account, dan Spreadsheet |
| [Usage](docs/USAGE.md) | Cara menjalankan kedua mode |
| [Architecture](docs/ARCHITECTURE.md) | Alur proses dan differential update |
| [Windows Task Scheduler](docs/WINDOWS_TASK_SCHEDULER.md) | Automation terjadwal di Windows/VPS |
| [Logging](docs/LOGGING.md) | Struktur log dan monitoring proses |
| [Testing](docs/TESTING.md) | Menjalankan unit test |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Diagnosis masalah umum |

## Kolom Spreadsheet

| Kolom | Fungsi |
|---|---|
| NIK | Sumber NIK |
| O | Status Pengguna |
| P | Status Sertifikat |
| Q | Tanggal terbit |
| R | Tanggal berakhir |

Tanggal pada Q/R ditulis sebagai nilai tanggal dan ditampilkan dalam format `dd-mmm-yyyy`.

## Automation Windows

Untuk penggunaan terjadwal, jalankan:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

Wrapper saat ini menjalankan:

```text
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

Panduan lengkap: [Windows Task Scheduler](docs/WINDOWS_TASK_SCHEDULER.md).

## Security

Jangan commit:

- `.env`
- Google Service Account credential
- username/password/token API
- file log
- data NIK atau export spreadsheet produksi

Lihat [SECURITY.md](SECURITY.md).

## Testing

```bash
python -m unittest tests.test_both_bsre_modes
```

Detail: [docs/TESTING.md](docs/TESTING.md).

## License

Project ini menggunakan [MIT License](LICENSE).
