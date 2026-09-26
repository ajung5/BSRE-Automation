import os
import unittest
from datetime import datetime
from unittest.mock import patch

import cek_nik_bsre_spreadseheet_merge as filtered_app
import cek_nik_bsre_spreadseheet_merge_all_rows as all_rows_app


APPS = (
    ("FILTERED", filtered_app),
    ("ALL_ROWS", all_rows_app),
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class FakeWorksheet:
    def __init__(self, data):
        self.title = "Data"
        self._data = data
        self.batch_updates = []
        self.formats = []

    def get_all_values(self):
        return self._data

    def batch_update(self, data, value_input_option=None):
        self.batch_updates.append({
            "data": data,
            "value_input_option": value_input_option,
        })
        return {}

    def format(self, range_name, format_data):
        # Disediakan hanya agar regression test dapat memastikan method ini
        # tidak pernah dipakai oleh production code.
        self.formats.append({
            "range": range_name,
            "format": format_data,
        })
        return {}


class FakeExecute:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class FakeSpreadsheets:
    def __init__(self, payload):
        self.payload = payload

    def get(self, **kwargs):
        return FakeExecute(self.payload)


class FakeSheetsService:
    def __init__(self, payload):
        self.payload = payload

    def spreadsheets(self):
        return FakeSpreadsheets(self.payload)


def make_header():
    header = [""] * 18
    header[2] = "NIK"
    header[14] = "Status Pengguna"
    header[15] = "Status Sertifikat"
    header[16] = "Tanggal terbit"
    header[17] = "Tanggal berakhir"
    return header


def make_row(
    nik,
    status_pengguna="Verified",
    status_sertifikat="Issued",
    tanggal_terbit="2024-08-12",
    tanggal_berakhir="2026-08-12",
):
    row = [""] * 18
    row[2] = nik
    row[14] = status_pengguna
    row[15] = status_sertifikat
    row[16] = tanggal_terbit
    row[17] = tanggal_berakhir
    return row


def success_status(nik):
    return {
        "update": True,
        "status_api": "ISSUE",
        "status_pengguna": "Verified",
        "status_sertifikat": "Issued",
    }


def success_profile(
    tanggal_terbit="2024-08-12",
    tanggal_berakhir="2026-08-12",
):
    return {
        "status": "SUCCESS",
        "tanggal_terbit": tanggal_terbit,
        "tanggal_berakhir": tanggal_berakhir,
        "sumber_tanggal_terbit": "fallback_expiry_minus_2_years",
        "sumber_tanggal_berakhir": "berlaku_sampai",
    }


def patch_all_rows(worksheet, profile_result, status_func=success_status):
    return (
        patch.object(
            all_rows_app,
            "koneksi_google",
            return_value=(None, None, worksheet),
        ),
        patch.object(
            all_rows_app,
            "cek_status_sertifikat",
            side_effect=status_func,
        ),
        patch.object(
            all_rows_app,
            "cek_profile_sertifikat",
            return_value=profile_result,
        ),
        patch.object(all_rows_app.time, "sleep", return_value=None),
        patch.object(
            all_rows_app,
            "tqdm",
            side_effect=lambda iterable, **kwargs: iterable,
        ),
    )


def run_all_rows(worksheet, profile_result, status_func=success_status):
    old = (all_rows_app.SPREADSHEET_ID, all_rows_app.WORKSHEET_NAME)
    all_rows_app.SPREADSHEET_ID = "test-spreadsheet"
    all_rows_app.WORKSHEET_NAME = "Data"
    contexts = patch_all_rows(worksheet, profile_result, status_func)
    try:
        with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4]:
            all_rows_app.proses_google_sheet()
    finally:
        all_rows_app.SPREADSHEET_ID, all_rows_app.WORKSHEET_NAME = old


def visible_metadata(total_rows=2):
    # total_rows termasuk header pada metadata helper ini.
    return {
        "sheets": [{
            "data": [{
                "startRow": 0,
                "rowMetadata": [{} for _ in range(total_rows)],
            }]
        }]
    }


def run_filtered(worksheet, profile_result, metadata=None, status_func=success_status):
    if metadata is None:
        metadata = visible_metadata(len(worksheet._data))
    service = FakeSheetsService(metadata)

    old = (filtered_app.SPREADSHEET_ID, filtered_app.WORKSHEET_NAME)
    filtered_app.SPREADSHEET_ID = "test-spreadsheet"
    filtered_app.WORKSHEET_NAME = "Data"
    try:
        with (
            patch.object(
                filtered_app,
                "koneksi_google",
                return_value=(None, None, worksheet, service),
            ),
            patch.object(
                filtered_app,
                "cek_status_sertifikat",
                side_effect=status_func,
            ),
            patch.object(
                filtered_app,
                "cek_profile_sertifikat",
                return_value=profile_result,
            ),
            patch.object(filtered_app.time, "sleep", return_value=None),
            patch.object(
                filtered_app,
                "tqdm",
                side_effect=lambda iterable, **kwargs: iterable,
            ),
        ):
            filtered_app.proses_google_sheet()
    finally:
        filtered_app.SPREADSHEET_ID, filtered_app.WORKSHEET_NAME = old


class TestDateNormalization(unittest.TestCase):
    def test_equivalent_date_formats(self):
        values = [
            "2026-08-12",
            "2026/08/12",
            "2026.08.12",
            "12-08-2026",
            "12/08/2026",
            "12.08.2026",
            "12-08-26",
            "12/08/26",
            "12.08.26",
            "12-Agu-2026",
            "12-Aug-2026",
            "12 Agustus 2026",
            "12 August 2026",
            "2026-08-12 00:00:00",
            "2026-08-12T00:00:00",
        ]

        for app_name, app in APPS:
            for value in values:
                with self.subTest(app=app_name, value=value):
                    self.assertEqual(
                        app.normalisasi_tanggal(value),
                        "2026-08-12",
                    )

    def test_same_date_different_display_is_not_change(self):
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                self.assertFalse(
                    app.nilai_tanggal_berubah(
                        "12-Agu-2026",
                        "2026-08-12",
                    )
                )
                self.assertFalse(
                    app.nilai_tanggal_berubah(
                        "12/08/26",
                        "2026-08-12",
                    )
                )
                self.assertFalse(
                    app.nilai_tanggal_berubah(
                        "2026-08-12 00:00:00",
                        "2026-08-12",
                    )
                )

    def test_different_dates_are_change(self):
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                self.assertTrue(
                    app.nilai_tanggal_berubah(
                        "12-Agu-2026",
                        "2027-08-12",
                    )
                )


class TestCertificateDateExtraction(unittest.TestCase):
    def test_real_issue_date_field_is_preferred(self):
        cert = {
            "berlaku_mulai": "15-08-2024",
            "berlaku_sampai": "12-08-2026",
        }
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                result = app.ekstrak_tanggal_sertifikat(cert)
                self.assertEqual(result["tanggal_terbit"], "2024-08-15")
                self.assertEqual(result["tanggal_berakhir"], "2026-08-12")
                self.assertEqual(result["sumber_tanggal_terbit"], "berlaku_mulai")

    def test_legacy_fallback_issue_date_is_preserved(self):
        cert = {"berlaku_sampai": "12-08-2026"}
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                result = app.ekstrak_tanggal_sertifikat(cert)
                self.assertEqual(result["tanggal_terbit"], "2024-08-12")
                self.assertEqual(
                    result["sumber_tanggal_terbit"],
                    "fallback_expiry_minus_2_years",
                )

    def test_invalid_expiry_is_rejected(self):
        cert = {"berlaku_sampai": "not-a-date"}
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                self.assertIsNone(app.ekstrak_tanggal_sertifikat(cert))


class TestProfileApiHandling(unittest.TestCase):
    def test_no_certificate_returns_none_dates(self):
        payload = {"success": True, "data": {"sertifikat": []}}
        for app_name, app in APPS:
            old = (app.BASE_URL, app.USERNAME, app.PASSWORD)
            app.BASE_URL = "https://example.test"
            app.USERNAME = "u"
            app.PASSWORD = "p"
            try:
                with patch.object(app.requests, "get") as mock_get:
                    mock_get.return_value = FakeResponse(200, payload)
                    result = app.cek_profile_sertifikat("123")
                with self.subTest(app=app_name):
                    self.assertEqual(result["status"], "NO_CERTIFICATE")
                    self.assertIsNone(result["tanggal_terbit"])
                    self.assertIsNone(result["tanggal_berakhir"])
            finally:
                app.BASE_URL, app.USERNAME, app.PASSWORD = old

    def test_not_found_returns_none_dates(self):
        for app_name, app in APPS:
            old = (app.BASE_URL, app.USERNAME, app.PASSWORD)
            app.BASE_URL = "https://example.test"
            app.USERNAME = "u"
            app.PASSWORD = "p"
            try:
                with patch.object(app.requests, "get") as mock_get:
                    mock_get.return_value = FakeResponse(404, {})
                    result = app.cek_profile_sertifikat("123")
                with self.subTest(app=app_name):
                    self.assertEqual(result["status"], "NOT_FOUND")
                    self.assertIsNone(result["tanggal_terbit"])
                    self.assertIsNone(result["tanggal_berakhir"])
            finally:
                app.BASE_URL, app.USERNAME, app.PASSWORD = old

    def test_latest_expiry_is_selected(self):
        payload = {
            "success": True,
            "data": {
                "sertifikat": [
                    {"berlaku_sampai": "12-08-2026"},
                    {
                        "berlaku_mulai": "01-09-2026",
                        "berlaku_sampai": "01-09-2028",
                    },
                ]
            },
        }
        for app_name, app in APPS:
            old = (app.BASE_URL, app.USERNAME, app.PASSWORD)
            app.BASE_URL = "https://example.test"
            app.USERNAME = "u"
            app.PASSWORD = "p"
            try:
                with patch.object(app.requests, "get") as mock_get:
                    mock_get.return_value = FakeResponse(200, payload)
                    result = app.cek_profile_sertifikat("123")
                with self.subTest(app=app_name):
                    self.assertEqual(result["status"], "SUCCESS")
                    self.assertEqual(result["tanggal_terbit"], "2026-09-01")
                    self.assertEqual(result["tanggal_berakhir"], "2028-09-01")
            finally:
                app.BASE_URL, app.USERNAME, app.PASSWORD = old


class TestAllRowsNonDestructiveDates(unittest.TestCase):
    def _worksheet(self, q="12-Agu-2024", r="12-Agu-2026"):
        return FakeWorksheet([
            make_header(),
            make_row("1111111111111111", tanggal_terbit=q, tanggal_berakhir=r),
        ])

    def test_same_date_different_format_produces_zero_write(self):
        worksheet = self._worksheet()
        run_all_rows(worksheet, success_profile("2024-08-12", "2026-08-12"))
        self.assertEqual(worksheet.batch_updates, [])
        self.assertEqual(worksheet.formats, [])

    def test_no_certificate_preserves_existing_dates(self):
        worksheet = self._worksheet()
        run_all_rows(
            worksheet,
            {
                "status": "NO_CERTIFICATE",
                "tanggal_terbit": None,
                "tanggal_berakhir": None,
            },
        )
        self.assertEqual(worksheet.batch_updates, [])

    def test_not_found_preserves_existing_dates(self):
        worksheet = self._worksheet()
        run_all_rows(
            worksheet,
            {
                "status": "NOT_FOUND",
                "tanggal_terbit": None,
                "tanggal_berakhir": None,
            },
        )
        self.assertEqual(worksheet.batch_updates, [])

    def test_no_data_preserves_existing_dates(self):
        worksheet = self._worksheet()
        run_all_rows(
            worksheet,
            {
                "status": "NO_DATA",
                "tanggal_terbit": None,
                "tanggal_berakhir": None,
            },
        )
        self.assertEqual(worksheet.batch_updates, [])

    def test_no_certificate_date_preserves_existing_dates(self):
        worksheet = self._worksheet()
        run_all_rows(
            worksheet,
            {
                "status": "NO_CERTIFICATE_DATE",
                "tanggal_terbit": None,
                "tanggal_berakhir": None,
            },
        )
        self.assertEqual(worksheet.batch_updates, [])

    def test_only_changed_date_cell_is_written(self):
        worksheet = self._worksheet(q="2024-08-12", r="2026-08-12")
        run_all_rows(
            worksheet,
            success_profile("2024-08-12", "2027-08-12"),
        )
        self.assertEqual(len(worksheet.batch_updates), 1)
        data = worksheet.batch_updates[0]["data"]
        self.assertEqual(
            data,
            [{"range": "R2", "values": [["2027-08-12"]]}],
        )
        self.assertEqual(worksheet.formats, [])


class TestFilteredMode(unittest.TestCase):
    def test_hidden_row_is_not_processed(self):
        worksheet = FakeWorksheet([
            make_header(),
            make_row("1111111111111111"),
            make_row("2222222222222222"),
        ])
        metadata = {
            "sheets": [{
                "data": [{
                    "startRow": 0,
                    "rowMetadata": [
                        {},
                        {},
                        {"hiddenByFilter": True},
                    ],
                }]
            }]
        }
        calls = []

        def status(nik):
            calls.append(nik)
            return success_status(nik)

        run_filtered(
            worksheet,
            success_profile(),
            metadata=metadata,
            status_func=status,
        )
        self.assertEqual(calls, ["1111111111111111"])

    def test_no_certificate_preserves_existing_dates(self):
        worksheet = FakeWorksheet([
            make_header(),
            make_row(
                "1111111111111111",
                tanggal_terbit="12-Agu-2024",
                tanggal_berakhir="12-Agu-2026",
            ),
        ])
        run_filtered(
            worksheet,
            {
                "status": "NO_CERTIFICATE",
                "tanggal_terbit": None,
                "tanggal_berakhir": None,
            },
        )
        self.assertEqual(worksheet.batch_updates, [])
        self.assertEqual(worksheet.formats, [])

    def test_same_date_different_format_produces_zero_write(self):
        worksheet = FakeWorksheet([
            make_header(),
            make_row(
                "1111111111111111",
                tanggal_terbit="12/08/24",
                tanggal_berakhir="2026-08-12 00:00:00",
            ),
        ])
        run_filtered(
            worksheet,
            success_profile("2024-08-12", "2026-08-12"),
        )
        self.assertEqual(worksheet.batch_updates, [])


class TestStaticRegressionGuards(unittest.TestCase):
    def test_no_mass_format_in_production_scripts(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for filename in (
            "cek_nik_bsre_spreadseheet_merge.py",
            "cek_nik_bsre_spreadseheet_merge_all_rows.py",
        ):
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as handle:
                source = handle.read()
            with self.subTest(filename=filename):
                self.assertNotIn('worksheet.format("Q2:R"', source)
                self.assertNotIn("worksheet.format('Q2:R'", source)

    def test_all_rows_returns_nonzero_on_unhandled_error(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "cek_nik_bsre_spreadseheet_merge_all_rows.py")
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("sys.exit(1)", source)

    def test_scheduler_wrapper_has_single_instance_guard(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "run_bsre.ps1")
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("System.Threading.Mutex", source)
        self.assertIn("WaitOne(0", source)
        self.assertIn("BSRE Sync SKIPPED", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
