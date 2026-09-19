# Revision Notes — Strict Differential Write

Perubahan utama:

1. Menghapus seluruh pemanggilan aktif `worksheet.format("Q2:R", ...)` dari mode all-rows dan filtered.
2. Google Sheets hanya menerima `batch_update` untuk cell individual O/P/Q/R yang benar-benar berubah.
3. Menambahkan log exact cell range:
   - `Cell yang diperbarui:`
   - contoh `P128`, `Q128`, `R128`.
4. Menambahkan invariant:
   `total_cell_berubah == len(update_cells)`.
5. Menambahkan regression test untuk:
   - perubahan status individual;
   - perubahan Q/R tanpa format massal;
   - mode all-rows;
   - mode filtered;
   - exact-cell logging.
6. README dan dokumentasi logging disesuaikan.

Validasi:
- Python syntax: PASS
- Regression tests: 17 PASS, 0 failure, 0 error
- AST guard: tidak ada pemanggilan aktif `worksheet.format(...)`

Tidak perlu mengubah:
- run_bsre.ps1
- .env
- credentials
- requirements.txt
- Windows Task Scheduler

Deploy VPS:
1. Backup source saat ini.
2. Replace dua file Python dan `tests/test_both_bsre_modes.py`.
3. Opsional: replace README.md dan docs/LOGGING.md.
4. Jalankan:
   `.\venv\Scripts\python.exe -m unittest tests.test_both_bsre_modes -v`
5. Jika OK, jalankan:
   `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"`
6. Periksa log terbaru dan cocokkan `Total cell berubah` dengan daftar `Cell yang diperbarui`.
