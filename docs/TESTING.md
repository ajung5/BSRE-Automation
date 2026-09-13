# Testing

Test suite saat ini menggunakan Python standard library `unittest` dan `unittest.mock`.

File test:

```text
tests/test_both_bsre_modes.py
```

## Menjalankan Test

Dari root repository:

```bash
python -m unittest tests.test_both_bsre_modes
```

Atau discovery:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Scope

Test dirancang untuk memvalidasi logic utama tanpa menulis ke Google Sheets produksi atau memanggil API BSrE nyata.

Area yang diuji antara lain:

- normalisasi tanggal;
- perbandingan nilai;
- mapping status;
- response handling;
- logic kedua mode.

## Sebelum Commit

Direkomendasikan menjalankan:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Pastikan semua test lulus sebelum perubahan source digabungkan.
