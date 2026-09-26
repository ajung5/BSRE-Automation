# Revision Notes — Date Idempotency & Scheduler Safety

Tanggal: 26 September 2026

## Root cause yang diperbaiki

### 1. Destructive clearing Q/R

Versi sebelumnya mengubah:

```text
NO_CERTIFICATE / NOT_FOUND
        ↓
tanggal baru = ""
        ↓
existing date != ""
        ↓
Q/R ditulis ulang menjadi kosong
```

Patch mengubah policy menjadi **preserve existing date** untuk profile yang tidak menyediakan tanggal usable.

### 2. False positive akibat representasi tanggal

Nilai Sheet dapat tampil berbeda dari ISO API walaupun tanggalnya sama. Normalisasi sekarang mencakup lebih banyak format sehingga contoh berikut dianggap ekuivalen:

```text
12-Agu-2026
12-Aug-2026
12/08/2026
12/08/26
12.08.2026
2026-08-12
2026-08-12 00:00:00
2026-08-12T00:00:00
```

### 3. Issue date hanya dihitung dari expiry

Patch memprioritaskan actual issue/start field bila response API memilikinya. Jika tidak tersedia, behavior lama `expiry - 2 years` tetap digunakan.

### 4. Concurrent scheduled/manual execution

`run_bsre.ps1` sekarang memakai named mutex `Global\BSRE-Automation-Sync`. Instance kedua keluar dengan code `2` dan membuat log `SKIPPED_ALREADY_RUNNING`.

### 5. False SUCCESS pada all-rows exception

Unhandled exception pada mode all-rows sekarang memanggil `sys.exit(1)`, sehingga PowerShell menerima exit code gagal yang benar.

## Invariant setelah patch

- No change => no write.
- Same date, different display format => no write.
- Profile not usable => existing Q/R preserved.
- Only changed O/P/Q/R cell enters `batch_update`.
- No mass formatting/value write to `Q2:R`.
- One sync process at a time.
