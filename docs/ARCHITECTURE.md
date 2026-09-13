# Architecture

## Overview

BSRE Automation menghubungkan tiga komponen utama:

```text
Google Spreadsheet
        │
        ▼
Python Automation
        │
        ├── BSrE Status API
        └── BSrE Profile API
```

## Filtered Mode

```text
Google Spreadsheet
        │
        ▼
Deteksi row terlihat
        │
        ├── hidden/filter → skip
        ▼
Ambil NIK
        │
        ├── status API
        └── profile API
        │
        ▼
Normalisasi hasil
        │
        ▼
Bandingkan O/P/Q/R
        │
        ├── sama → tidak ditulis
        └── berubah → batch update
```

Mode ini menggunakan Google Sheets API tambahan untuk menentukan row yang terlihat.

## All-Rows Mode

```text
Google Spreadsheet
        │
        ▼
Ambil seluruh row
        │
        ▼
Ambil NIK
        │
        ├── status API
        └── profile API
        │
        ▼
Bandingkan O/P/Q/R
        │
        ▼
Batch update cell yang berubah
```

## Differential Update

Tujuan differential update:

- mengurangi jumlah write ke Google Sheets;
- mencegah penulisan ulang data yang sama;
- mempertahankan efisiensi pada dataset besar;
- memudahkan statistik perubahan aktual.

## Date Normalization

Nilai tanggal dibandingkan dalam format canonical:

```text
YYYY-MM-DD
```

Beberapa bentuk tanggal yang dinormalisasi antara lain:

```text
2026-08-12
12-08-2026
12/08/2026
12-Agu-2026
12-Aug-2026
12 Agustus 2026
```

## All-Rows Progress Monitoring

Mode all-rows memiliki heartbeat periodik. Source saat ini menggunakan interval:

```text
500 row
```

Heartbeat menampilkan:

```text
Progress
Elapsed
ETA
```

agar proses panjang tetap dapat dipantau melalui log.
