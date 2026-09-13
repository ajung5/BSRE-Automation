# Logging

## Windows Automation

`run_bsre.ps1` membuat file log di:

```text
C:\BSRE-Automation\logs\
```

Nama file dibuat berdasarkan waktu eksekusi.

Contoh pola:

```text
bsre_DD-Mmm-YYYY_HHmmss.log
```

Wrapper mencatat:

- waktu mulai;
- output stdout/stderr Python;
- waktu selesai;
- durasi;
- status `SUCCESS`, `FAILED`, atau `ERROR`;
- exit code jika proses gagal.

## All-Rows Heartbeat

Pada mode all-rows, heartbeat ditulis secara periodik untuk proses panjang.

Contoh:

```text
Progress : 500 / 18405 (2.72%) | Elapsed: 00:04:12 | ETA: 02:30:11
```

Interval pada source saat ini:

```text
500 row
```

## Statistik Akhir

Output all-rows menampilkan:

- total row data;
- total row diproses;
- total row berubah;
- total row tanpa perubahan;
- total cell berubah;
- perubahan kolom O/P/Q/R;
- statistik status API;
- statistik profile;
- NIK kosong/error.

## Retention

Folder `logs/` sudah seharusnya diabaikan Git.

Untuk server produksi, pertimbangkan:

- retention period;
- rotasi log;
- kapasitas disk;
- backup hanya jika diperlukan;
- pembatasan akses karena log dapat mengandung metadata operasional.
