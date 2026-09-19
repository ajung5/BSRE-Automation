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

## Audit Exact Cell yang Diperbarui

Ketika terdapat perubahan, script mencatat alamat setiap cell yang benar-benar dikirim ke Google Sheets.

Contoh:

```text
Mengupdate Google Spreadsheet...

Berhasil mengupdate 4 cell yang benar-benar berubah.

Cell yang diperbarui:
- P128
- Q128
- R128
- P947
```

Jumlah item pada bagian `Cell yang diperbarui` harus sama dengan:

```text
Total cell berubah
```

Source juga memiliki invariant internal:

```text
total_cell_berubah == len(update_cells)
```

Jika invariant tersebut tidak terpenuhi, script melempar `RuntimeError` agar inkonsistensi tidak tersembunyi di log.

## Tidak Ada Write/Format Massal Q2:R

Automation tidak menjalankan:

```python
worksheet.format("Q2:R", ...)
```

dan tidak mengirim update value ke seluruh range `Q2:R`.

Q/R hanya ditulis apabila cell individual memang berbeda setelah normalisasi tanggal.

Contoh:

```text
Q128
R128
```

berarti hanya dua alamat tersebut yang dikirim dalam `batch_update`.

Format tampilan tanggal sebaiknya dikonfigurasi satu kali langsung pada Google Spreadsheet.

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

## Regression Guard

Test suite memverifikasi bahwa:

```text
P berubah     -> Pn saja
Q berubah     -> Qn saja
R berubah     -> Rn saja
Q + R berubah -> Qn dan Rn saja
```

dan:

```text
worksheet.formats == []
```

ketika Q/R berubah.

Dengan demikian, penambahan kembali formatting massal akan menyebabkan regression test gagal.

## Retention

Folder `logs/` sudah seharusnya diabaikan Git.

Untuk server produksi, pertimbangkan:

- retention period;
- rotasi log;
- kapasitas disk;
- backup hanya jika diperlukan;
- pembatasan akses karena log dapat mengandung metadata operasional.
