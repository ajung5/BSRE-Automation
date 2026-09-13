# Contributing

Kontribusi dan perbaikan dipersilakan.

## Principles

- Jangan commit credential atau data produksi.
- Pertahankan differential update kecuali ada alasan desain yang jelas.
- Perubahan logic harus disertai test bila relevan.
- Hindari perubahan yang memutus kompatibilitas tanpa dokumentasi migrasi.
- Pertahankan mode filtered dan all-rows sebagai behavior yang eksplisit.

## Workflow

1. Buat branch.
2. Lakukan perubahan.
3. Jalankan unit test.
4. Review `.env`, credential, dan log agar tidak ikut commit.
5. Buat Pull Request dengan deskripsi dampak perubahan.

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Commit Convention

Contoh:

```text
feat: add retry strategy for profile requests
fix: prevent unnecessary date updates
docs: move task scheduler guide to docs
test: add expired certificate mapping case
refactor: simplify spreadsheet comparison
```

## Pull Request

Jelaskan:

- tujuan perubahan;
- file yang terdampak;
- behavior sebelum/sesudah;
- hasil test;
- risiko/migration note jika ada.
