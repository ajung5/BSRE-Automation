# Documentation Migration Checklist

Gunakan checklist berikut ketika menerapkan paket ini ke repository:

- [ ] Backup / buat branch dokumentasi.
- [ ] Ganti `README.md` lama dengan README baru.
- [ ] Tambahkan folder `docs/`.
- [ ] Tambahkan `SECURITY.md`.
- [ ] Tambahkan `CONTRIBUTING.md`.
- [ ] Tambahkan `CHANGELOG.md`.
- [ ] Tambahkan `LICENSE`.
- [ ] Tambahkan `.env.example`.
- [ ] Tambahkan `requirements.txt`.
- [ ] Update `.gitignore`.
- [ ] Tambahkan GitHub issue templates.
- [ ] Jalankan `python -m unittest discover -s tests -p "test_*.py"`.
- [ ] Verifikasi semua link relatif pada README.
- [ ] Pastikan tidak ada secret/data NIK yang ikut staged.
