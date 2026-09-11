import gspread
import requests
import time
import os
import sys
import re

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from tqdm import tqdm
from google.oauth2.service_account import Credentials


# ============================================================
# KONFIGURASI
# ============================================================

load_dotenv()


# ============================================================
# BSrE API
# ============================================================

BASE_URL = os.getenv("BSRE_BASE_URL")
USERNAME = os.getenv("BSRE_USERNAME")
PASSWORD = os.getenv("BSRE_PASSWORD")


# ============================================================
# GOOGLE SHEETS & SPREADSHEET KONFIGURASI
# ============================================================

GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")


# ============================================================
# MAPPING STATUS API
# ============================================================

STATUS_MAPPING = {
    "ISSUE": "Issued",
    "REVOKE": "Revoke",
    "RENEW": "Renew",
    "NO_CERTIFICATE": "New",
    "EXPIRED": "Expired",
}


# ============================================================
# DELAY API
# ============================================================

REQUEST_DELAY = 0.1


# ============================================================
# MAPPING BULAN UNTUK NORMALISASI TANGGAL
# ============================================================

BULAN_MAPPING = {
    "jan": 1,
    "januari": 1,
    "january": 1,
    "feb": 2,
    "februari": 2,
    "february": 2,
    "mar": 3,
    "maret": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "mei": 5,
    "may": 5,
    "jun": 6,
    "juni": 6,
    "june": 6,
    "jul": 7,
    "juli": 7,
    "july": 7,
    "agu": 8,
    "agustus": 8,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "okt": 10,
    "oktober": 10,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "des": 12,
    "desember": 12,
    "dec": 12,
    "december": 12,
}


# ============================================================
# HELPER
# ============================================================


def ambil_nilai_cell(row, index):
    """
    Mengambil nilai cell dari row secara aman.
    Index menggunakan zero-based index.

    O = 14
    P = 15
    Q = 16
    R = 17
    """
    if len(row) > index:
        return str(row[index]).strip()

    return ""



def normalisasi_tanggal(value):
    """
    Menormalisasi berbagai format tanggal menjadi YYYY-MM-DD
    agar tanggal yang sama tidak dianggap berubah hanya karena
    format tampilannya berbeda.

    Contoh yang didukung:
    - 2026-08-12
    - 12-08-2026
    - 12/08/2026
    - 12-Agu-2026
    - 12-Aug-2026
    - 12 Agustus 2026
    - 12 August 2026
    """
    if value is None:
        return ""

    value = str(value).strip()

    if not value:
        return ""

    # Bersihkan spasi ganda.
    value = re.sub(r"\s+", " ", value)

    # Format numerik yang umum.
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Format dengan nama bulan, baik menggunakan '-' '/' maupun spasi.
    value_normalized = value.replace("/", "-").replace(" ", "-")
    value_normalized = re.sub(r"-+", "-", value_normalized)
    parts = value_normalized.split("-")

    if len(parts) == 3:
        try:
            # dd-mmm-yyyy / dd-bulan-yyyy
            if len(parts[0]) <= 2:
                hari = int(parts[0])
                bulan_text = parts[1].strip().lower().rstrip(".")
                tahun = int(parts[2])

                bulan = BULAN_MAPPING.get(bulan_text)

                if bulan:
                    return f"{tahun:04d}-{bulan:02d}-{hari:02d}"

            # yyyy-mmm-dd / yyyy-bulan-dd
            if len(parts[0]) == 4:
                tahun = int(parts[0])
                bulan_text = parts[1].strip().lower().rstrip(".")
                hari = int(parts[2])

                bulan = BULAN_MAPPING.get(bulan_text)

                if bulan:
                    return f"{tahun:04d}-{bulan:02d}-{hari:02d}"

        except (ValueError, TypeError):
            pass

    # Jika format tidak dikenali, kembalikan string asli.
    # Dengan demikian nilai yang benar-benar berbeda tetap akan di-update.
    return value



def nilai_teks_berubah(nilai_lama, nilai_baru):
    """
    Membandingkan nilai teks setelah trim.
    Perbandingan tetap case-sensitive agar nilai di Sheet mengikuti
    format canonical dari hasil API.
    """
    lama = "" if nilai_lama is None else str(nilai_lama).strip()
    baru = "" if nilai_baru is None else str(nilai_baru).strip()

    return lama != baru



def nilai_tanggal_berubah(nilai_lama, nilai_baru):
    """
    Membandingkan tanggal setelah dinormalisasi.
    """
    return normalisasi_tanggal(nilai_lama) != normalisasi_tanggal(nilai_baru)


# ============================================================
# KONEKSI GOOGLE
# ============================================================


def koneksi_google():
    if not GOOGLE_CREDENTIALS:
        raise ValueError(
            "\nGOOGLE_CREDENTIALS belum diisi pada file .env."
        )

    if not os.path.exists(GOOGLE_CREDENTIALS):
        raise FileNotFoundError(
            f"\nFile credential Google tidak ditemukan: {GOOGLE_CREDENTIALS}\n"
            "Pastikan path GOOGLE_CREDENTIALS pada file .env sudah benar."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS,
        scopes=scopes,
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

    return client, spreadsheet, worksheet


# ============================================================
# CEK PROFILE BSrE (TANGGAL)
# ============================================================


def cek_profile_sertifikat(nik):
    if not BASE_URL or not USERNAME or not PASSWORD:
        return None

    url = f"{BASE_URL}/api/user/profile/{nik}"

    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            success = data.get("success", False)

            if not success:
                return {
                    "status": "NO_DATA",
                    "tanggal_terbit": "",
                    "tanggal_berakhir": "",
                }

            profile_data = data.get("data", {})
            certificates = profile_data.get("sertifikat", [])

            if not certificates:
                return {
                    "status": "NO_CERTIFICATE",
                    "tanggal_terbit": "",
                    "tanggal_berakhir": "",
                }

            daftar_sertifikat_valid = []

            for certificate in certificates:
                berlaku_sampai = certificate.get("berlaku_sampai", "")

                if not berlaku_sampai:
                    continue

                try:
                    tanggal_expired = datetime.strptime(
                        berlaku_sampai,
                        "%d-%m-%Y",
                    )

                    daftar_sertifikat_valid.append(
                        {
                            "tanggal": tanggal_expired,
                            "data": certificate,
                        }
                    )

                except ValueError:
                    continue

            if not daftar_sertifikat_valid:
                return {
                    "status": "NO_CERTIFICATE_DATE",
                    "tanggal_terbit": "",
                    "tanggal_berakhir": "",
                }

            # Ambil sertifikat dengan tanggal berakhir paling akhir.
            daftar_sertifikat_valid.sort(
                key=lambda x: x["tanggal"],
                reverse=True,
            )

            certificate_terbaru = daftar_sertifikat_valid[0]
            tanggal_expired = certificate_terbaru["tanggal"]

            # Mengikuti logika script sebelumnya:
            # tanggal terbit dihitung 2 tahun sebelum tanggal berakhir.
            tanggal_issue = tanggal_expired - relativedelta(years=2)

            # Gunakan format ISO agar Google Sheets menerima sebagai tanggal.
            tanggal_terbit = tanggal_issue.strftime("%Y-%m-%d")
            tanggal_berakhir = tanggal_expired.strftime("%Y-%m-%d")

            return {
                "status": "SUCCESS",
                "tanggal_terbit": tanggal_terbit,
                "tanggal_berakhir": tanggal_berakhir,
            }

        if response.status_code == 401:
            print(f"\nUNAUTHORIZED - NIK {nik} (Profile)")
            return None

        if response.status_code == 404:
            return {
                "status": "NOT_FOUND",
                "tanggal_terbit": "",
                "tanggal_berakhir": "",
            }

        print(
            f"\nHTTP ERROR {response.status_code} - NIK {nik} (Profile)"
        )
        return None

    except Exception as e:
        print(f"\nERROR PROFILE - NIK {nik}: {e}")
        return None


# ============================================================
# CEK STATUS SERTIFIKAT BSrE
# ============================================================


def cek_status_sertifikat(nik):
    if not BASE_URL or not USERNAME or not PASSWORD:
        return None

    url = f"{BASE_URL}/api/user/status/{nik}"

    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            status_api = str(data.get("status", "")).strip().upper()

            if status_api == "NOT_REGISTERED":
                return {
                    "update": False,
                    "status_api": status_api,
                    "status_pengguna": None,
                    "status_sertifikat": None,
                }

            if status_api in STATUS_MAPPING:
                return {
                    "update": True,
                    "status_api": status_api,
                    "status_pengguna": "Verified",
                    "status_sertifikat": STATUS_MAPPING[status_api],
                }

            return {
                "update": False,
                "status_api": status_api,
                "status_pengguna": None,
                "status_sertifikat": None,
            }

        if response.status_code == 401:
            print(f"\nUNAUTHORIZED - NIK {nik} (Status)")
            return None

        print(
            f"\nHTTP ERROR {response.status_code} - NIK {nik} (Status)"
        )
        return None

    except Exception as e:
        print(f"\nERROR STATUS - NIK {nik}: {e}")
        return None


# ============================================================
# PROSES GOOGLE SHEETS
# ============================================================


def proses_google_sheet():
    print("\n" + "=" * 70)
    print(" CEK STATUS DAN TANGGAL SERTIFIKAT ELEKTRONIK BSrE")
    print("=" * 70 + "\n")

    if not SPREADSHEET_ID or SPREADSHEET_ID == "ISI_ID_GOOGLE_SPREADSHEET":
        raise ValueError("\nSPREADSHEET_ID belum diisi.")

    if not WORKSHEET_NAME:
        raise ValueError("\nWORKSHEET_NAME belum diisi.")

    print("Menghubungkan ke Google Spreadsheet...")
    client, spreadsheet, worksheet = koneksi_google()
    print("Berhasil terhubung.\n")

    print("Mengambil seluruh data spreadsheet...")
    data = worksheet.get_all_values()

    if not data:
        print("Spreadsheet kosong.")
        return

    header = data[0]

    try:
        kolom_nik_index = header.index("NIK") + 1
    except ValueError:
        raise ValueError("\nKolom 'NIK' tidak ditemukan.")

    if kolom_nik_index != 3:
        print(
            f"\nPERINGATAN: Kolom NIK ditemukan di posisi "
            f"{kolom_nik_index}, bukan kolom C.\n"
        )

    # ========================================================
    # HEADER Q & R - UPDATE HANYA JIKA BERBEDA
    # ========================================================

    header_updates = []

    header_q_lama = ambil_nilai_cell(header, 16)
    header_r_lama = ambil_nilai_cell(header, 17)

    if header_q_lama != "Tanggal terbit":
        header_updates.append(
            {
                "range": "Q1",
                "values": [["Tanggal terbit"]],
            }
        )

    if header_r_lama != "Tanggal berakhir":
        header_updates.append(
            {
                "range": "R1",
                "values": [["Tanggal berakhir"]],
            }
        )

    if header_updates:
        worksheet.batch_update(
            header_updates,
            value_input_option="USER_ENTERED",
        )

    # Semua row diproses, termasuk row hidden atau terkena filter.
    # Baris 1 adalah header, sehingga data dimulai dari baris 2.
    total_row = len(data) - 1
    semua_row_data = list(range(2, len(data) + 1))

    print(f"\nTotal row data       : {total_row}")
    print(f"Total row diproses   : {len(semua_row_data)}")
    print("Mode                 : SEMUA ROW")
    print("Update               : HANYA CELL O/P/Q/R YANG BERUBAH\n")

    # Semua cell yang benar-benar berubah akan dikumpulkan di sini
    # lalu ditulis sekaligus menggunakan batch update.
    update_cells = []
    row_yang_diubah = set()

    # ========================================================
    # STATISTIK PERUBAHAN CELL
    # ========================================================

    perubahan_o = 0
    perubahan_p = 0
    perubahan_q = 0
    perubahan_r = 0

    jumlah_row_tanpa_perubahan = 0

    # ========================================================
    # STATISTIK PROFILE
    # ========================================================

    jumlah_sukses = 0
    jumlah_tidak_ada_sertifikat = 0
    jumlah_tidak_ditemukan = 0
    jumlah_tanggal_tidak_valid = 0
    jumlah_no_data = 0

    # ========================================================
    # STATISTIK STATUS
    # ========================================================

    jumlah_issue = 0
    jumlah_revoke = 0
    jumlah_renew = 0
    jumlah_no_certificate = 0
    jumlah_expired = 0
    jumlah_not_registered = 0
    jumlah_tidak_diubah = 0

    jumlah_nik_kosong = 0
    jumlah_error = 0

    # ========================================================
    # LOOP SELURUH ROW
    # ========================================================

    for nomor_baris in tqdm(
        semua_row_data,
        total=len(semua_row_data),
        desc="Checking NIK",
        disable=not sys.stdout.isatty(),
    ):
        if nomor_baris > len(data):
            continue

        row = data[nomor_baris - 1]

        if len(row) >= kolom_nik_index:
            nik = str(row[kolom_nik_index - 1]).strip()
        else:
            nik = ""

        if not nik or nik.lower() in {"nan", "none"}:
            jumlah_nik_kosong += 1
            continue

        # ====================================================
        # REQUEST KEDUA API
        # ====================================================

        hasil_status = cek_status_sertifikat(nik)
        hasil_profile = cek_profile_sertifikat(nik)

        if hasil_status is None or hasil_profile is None:
            jumlah_error += 1
            time.sleep(REQUEST_DELAY)
            continue

        row_updated_in_this_iter = False

        # ====================================================
        # NILAI SAAT INI DI GOOGLE SHEETS
        # ====================================================

        # O = index 14
        # P = index 15
        # Q = index 16
        # R = index 17

        status_pengguna_lama = ambil_nilai_cell(row, 14)
        status_sertifikat_lama = ambil_nilai_cell(row, 15)
        tanggal_terbit_lama = ambil_nilai_cell(row, 16)
        tanggal_berakhir_lama = ambil_nilai_cell(row, 17)

        # ====================================================
        # UPDATE STATUS - KOLOM O & P
        # ====================================================

        if hasil_status["update"]:
            status_pengguna_baru = hasil_status["status_pengguna"]
            status_sertifikat_baru = hasil_status["status_sertifikat"]

            # Update O hanya jika benar-benar berubah.
            if nilai_teks_berubah(
                status_pengguna_lama,
                status_pengguna_baru,
            ):
                update_cells.append(
                    {
                        "range": f"O{nomor_baris}",
                        "values": [[status_pengguna_baru]],
                    }
                )

                perubahan_o += 1
                row_updated_in_this_iter = True

            # Update P hanya jika benar-benar berubah.
            if nilai_teks_berubah(
                status_sertifikat_lama,
                status_sertifikat_baru,
            ):
                update_cells.append(
                    {
                        "range": f"P{nomor_baris}",
                        "values": [[status_sertifikat_baru]],
                    }
                )

                perubahan_p += 1
                row_updated_in_this_iter = True

            status_api = hasil_status["status_api"]

            if status_api == "ISSUE":
                jumlah_issue += 1
            elif status_api == "REVOKE":
                jumlah_revoke += 1
            elif status_api == "RENEW":
                jumlah_renew += 1
            elif status_api == "NO_CERTIFICATE":
                jumlah_no_certificate += 1
            elif status_api == "EXPIRED":
                jumlah_expired += 1

        else:
            if hasil_status.get("status_api") == "NOT_REGISTERED":
                jumlah_not_registered += 1
            else:
                jumlah_tidak_diubah += 1

        # ====================================================
        # PROFILE TANGGAL - KOLOM Q & R
        # ====================================================

        status_prof = hasil_profile.get("status", "")

        tanggal_terbit_baru = None
        tanggal_berakhir_baru = None

        if status_prof == "SUCCESS":
            tanggal_terbit_baru = hasil_profile["tanggal_terbit"]
            tanggal_berakhir_baru = hasil_profile["tanggal_berakhir"]
            jumlah_sukses += 1

        elif status_prof == "NO_CERTIFICATE":
            jumlah_tidak_ada_sertifikat += 1
            tanggal_terbit_baru = ""
            tanggal_berakhir_baru = ""

        elif status_prof == "NOT_FOUND":
            jumlah_tidak_ditemukan += 1
            tanggal_terbit_baru = ""
            tanggal_berakhir_baru = ""

        elif status_prof == "NO_CERTIFICATE_DATE":
            jumlah_tanggal_tidak_valid += 1

        elif status_prof == "NO_DATA":
            jumlah_no_data += 1

        # ====================================================
        # BANDINGKAN Q - TANGGAL TERBIT
        # ====================================================

        if tanggal_terbit_baru is not None:
            if nilai_tanggal_berubah(
                tanggal_terbit_lama,
                tanggal_terbit_baru,
            ):
                update_cells.append(
                    {
                        "range": f"Q{nomor_baris}",
                        "values": [[tanggal_terbit_baru]],
                    }
                )

                perubahan_q += 1
                row_updated_in_this_iter = True

        # ====================================================
        # BANDINGKAN R - TANGGAL BERAKHIR
        # ====================================================

        if tanggal_berakhir_baru is not None:
            if nilai_tanggal_berubah(
                tanggal_berakhir_lama,
                tanggal_berakhir_baru,
            ):
                update_cells.append(
                    {
                        "range": f"R{nomor_baris}",
                        "values": [[tanggal_berakhir_baru]],
                    }
                )

                perubahan_r += 1
                row_updated_in_this_iter = True

        # ====================================================
        # CATAT ROW BERUBAH / TIDAK BERUBAH
        # ====================================================

        if row_updated_in_this_iter:
            row_yang_diubah.add(nomor_baris)
        else:
            jumlah_row_tanpa_perubahan += 1

        time.sleep(REQUEST_DELAY)

    # ========================================================
    # UPDATE GOOGLE SHEETS BATCH
    # ========================================================

    print("\nMengupdate Google Spreadsheet...\n")

    if update_cells:
        worksheet.batch_update(
            update_cells,
            value_input_option="USER_ENTERED",
        )

        # Format tanggal hanya diperlukan apabila Q/R memang berubah.
        if perubahan_q > 0 or perubahan_r > 0:
            try:
                worksheet.format(
                    "Q2:R",
                    {
                        "numberFormat": {
                            "type": "DATE",
                            "pattern": "dd-mmm-yyyy",
                        }
                    },
                )
            except Exception as e:
                print(f"Peringatan format tanggal: {e}")

        print(
            f"Berhasil mengupdate {len(update_cells)} cell "
            "yang benar-benar berubah."
        )

    else:
        print("Tidak ada perubahan data. Tidak ada cell O/P/Q/R yang diupdate.")

    # ========================================================
    # HASIL AKHIR
    # ========================================================

    total_cell_berubah = (
        perubahan_o
        + perubahan_p
        + perubahan_q
        + perubahan_r
    )

    print("\n" + "=" * 70)
    print(" HASIL PENGECEKAN")
    print("=" * 70 + "\n")

    print(f"Total row data            : {total_row}")
    print(f"Total row diproses        : {len(semua_row_data)}")
    print(f"Total row berubah         : {len(row_yang_diubah)}")
    print(f"Total row tanpa perubahan : {jumlah_row_tanpa_perubahan}")
    print(f"Total cell berubah        : {total_cell_berubah}\n")

    print("--- PERUBAHAN CELL ---")
    print(f"Status Pengguna (O)       : {perubahan_o}")
    print(f"Status Sertifikat (P)     : {perubahan_p}")
    print(f"Tanggal terbit (Q)        : {perubahan_q}")
    print(f"Tanggal berakhir (R)      : {perubahan_r}\n")

    print("--- STATISTIK STATUS ---")
    print(f"ISSUE              : {jumlah_issue}")
    print(f"EXPIRED            : {jumlah_expired}")
    print(f"REVOKE             : {jumlah_revoke}")
    print(f"RENEW              : {jumlah_renew}")
    print(f"NO_CERTIFICATE     : {jumlah_no_certificate}")
    print(f"NOT_REGISTERED     : {jumlah_not_registered}")
    print(f"Tidak diubah       : {jumlah_tidak_diubah}\n")

    print("--- STATISTIK PROFILE ---")
    print(f"Tanggal ditemukan         : {jumlah_sukses}")
    print(f"Tidak ada sertifikat      : {jumlah_tidak_ada_sertifikat}")
    print(f"NIK tidak ditemukan       : {jumlah_tidak_ditemukan}")
    print(f"Tanggal tidak valid       : {jumlah_tanggal_tidak_valid}")
    print(f"Profile tanpa data        : {jumlah_no_data}\n")

    print(f"NIK kosong                : {jumlah_nik_kosong}")
    print(f"Error gabungan            : {jumlah_error}\n")

    print("Kolom O = Status Pengguna")
    print("Kolom P = Status Sertifikat")
    print("Kolom Q = Tanggal terbit")
    print("Kolom R = Tanggal berakhir\n")

    print("Semua row tetap diperiksa ke API BSrE.")
    print("Google Sheets hanya diupdate pada cell O/P/Q/R yang berubah.\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    try:
        proses_google_sheet()

    except KeyboardInterrupt:
        print("\nProses dihentikan oleh pengguna.")

    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70 + "\n")
        print(str(e))
        print()