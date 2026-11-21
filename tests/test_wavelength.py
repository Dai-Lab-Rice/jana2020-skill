import contextlib
import io
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from filter_m90_wavelength import filter_m90
from observation_mapping import mantid_records
from plot_extinction_wavelength import analyze_wavelength_dependence


LAYOUT = "sns-tof-hkl"
HKL = (-1, -1, 0)


def indices(hkl):
    return "".join(f"{index:4d}" for index in hkl)


def hkl_payload(wavelength, field_18=1.82440, d=1.2500):
    return (
        f"{12483.52:8.2f}{27.00:8.2f}{1:4d}{wavelength:8.5f}{0.1:8.5f}"
        + f"{0.2:9.5f}" * 6
        + f"{42:6d}{17:7d}{0.9:7.4f}{7:4d}{field_18:9.5f}{d:8.4f}{100:7.2f}{200:7.2f}\n"
    )


def source_row(wavelength, hkl=HKL):
    return indices(hkl) + hkl_payload(wavelength)


def m90_row(wavelength, tag, hkl=HKL):
    return (
        indices(hkl) + f"{12483.52:15.7E}{27.00:15.7E}{1:4d}{0:4d}{1:4d}"
        + f"{0.1:8.4f}{wavelength:8.4f}" + f"{0.2:8.4f}" * 6 + f"{tag:10d}\n"
    )


def m83_row(tag, hkl=HKL):
    return " ".join(map(str, (*hkl, 0, 0, 0, 0, 1, 0.1, 2.0, 1.0, 0.5, tag))) + "\n"


class WavelengthTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.hkl = root / "source.hkl"
        self.m90 = root / "original.m90"
        self.out = root / "subset.m90"
        self.m83 = root / "observed.m83"
        self.map = root / "observations.csv"
        self.hkl.write_text(source_row(1.09464))

    def write_m90(self, *rows):
        self.m90.write_text(f"nref {len(rows)}\nData  1\n" + "".join(rows))

    def write_map(self, *rows):
        body = "".join(",".join(map(str, row)) + "\n" for row in rows)
        self.map.write_text("sequence,h,k,l,wavelength_A,d_A\n" + body)

    def repeat_source(self):
        self.hkl.write_text(source_row(1.09464) + source_row(1.85752))
        self.write_map((1001, *HKL, 1.09464, 1.25), (2001, *HKL, 1.85752, 1.25))

    def filter(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return filter_m90(self.hkl, self.m90, self.out, hkl_layout=LAYOUT, **kwargs)

    def analyze(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return analyze_wavelength_dependence(
                self.hkl, self.m83, observations=self.map, hkl_layout=LAYOUT,
            )

    def test_field_6_controls_cutoff_and_preserves_intensity_boundary(self):
        self.assertTrue(self.hkl.read_text().startswith(f"{-1:4d}{-1:4d}{0:4d}" + "12483.52"))
        record, = mantid_records(self.hkl, LAYOUT)
        self.assertEqual(record, dict(hkl=HKL, intensity=12483.52, lam=1.09464, d=1.25))
        self.assertEqual(mantid_records(self.hkl, "corelli-garnet"), [record])
        self.write_m90(m90_row(1.0946, 1001))
        self.assertEqual(self.filter(max_lambda=1.8), 1)
        self.assertEqual(self.out.read_bytes(), self.m90.read_bytes())
        self.assertEqual(self.filter(max_d=1.2), 0)

    def test_repeated_hkl_uses_full_tags_and_renumbers_survivors(self):
        self.repeat_source()
        self.write_m90(m90_row(1.8575, 2001), m90_row(1.0946, 1001))
        with self.assertRaisesRegex(ValueError, "Repeated HKL"):
            self.filter(max_lambda=1.8)
        self.assertFalse(self.out.exists())
        self.assertEqual(self.filter(max_lambda=1.8, observations=self.map), 1)
        self.assertEqual(self.out.read_text(), "nref 1\nData  1\n" + m90_row(1.0946, 1001))
        self.assertEqual(self.filter(min_lambda=1.8, observations=self.map), 1)
        self.assertEqual(self.out.read_text(), "nref 1\nData  1\n" + m90_row(1.8575, 1001))

    def test_m83_observed_subset_uses_verified_full_map(self):
        self.repeat_source()
        self.m83.write_text("Listing header\n" + m83_row(2001))
        row, = self.analyze()
        self.assertEqual((row["sequence"], row["lam"], row["intensity_ratio"]), (2001, 1.85752, 4.0))

    def test_m83_checks_unlisted_entries_against_source(self):
        self.repeat_source()
        self.write_map((1001, *HKL, 1.5, 1.25), (2001, *HKL, 1.85752, 1.25))
        self.m83.write_text(m83_row(2001))
        with self.assertRaisesRegex(ValueError, "companion source"):
            self.analyze()

    def test_m83_rejects_unknown_tag_and_tag_hkl_mismatch(self):
        self.repeat_source()
        self.m83.write_text(m83_row(3001))
        with self.assertRaisesRegex(ValueError, "Missing observation map entry"):
            self.analyze()
        self.m83.write_text(m83_row(2001, hkl=(1, 2, 3)))
        with self.assertRaisesRegex(ValueError, "Sequence/HKL mismatch"):
            self.analyze()

    def test_rejects_wavelength_mismatch_even_for_an_excluded_row(self):
        self.repeat_source()
        self.write_m90(m90_row(1.0946, 1001), m90_row(1.8576, 2001))
        with self.assertRaisesRegex(ValueError, r"original\.m90:4: wavelength mismatch.*2001"):
            self.filter(max_lambda=1.8, observations=self.map)
        self.assertFalse(self.out.exists())

    def test_rejects_duplicate_native_tags(self):
        self.repeat_source()
        self.write_m90(m90_row(1.0946, 1001), m90_row(1.8575, 1001))
        with self.assertRaisesRegex(ValueError, "Duplicate native sequence tag"):
            self.filter(observations=self.map)
        self.assertFalse(self.out.exists())
        self.m83.write_text(m83_row(2001) * 2)
        with self.assertRaisesRegex(ValueError, "Duplicate native sequence tag"):
            self.analyze()

    def test_rejects_duplicate_map_tags(self):
        self.repeat_source()
        self.write_map((2001, *HKL, 1.09464, 1.25), (2001, *HKL, 1.85752, 1.25))
        self.m83.write_text(m83_row(2001))
        with self.assertRaisesRegex(ValueError, r"observations\.csv:3: duplicate/invalid"):
            self.analyze()

    def test_rejects_satellite_and_malformed_rows_with_source_location(self):
        satellite = indices(HKL + (1, -1, 2)) + hkl_payload(1.09464)
        for invalid in (satellite, "   1   2   3  123.45\n", source_row(float("nan"))):
            with self.subTest(row=invalid):
                self.hkl.write_text(source_row(1.09464) + invalid)
                with self.assertRaisesRegex(ValueError, r"source\.hkl:2:"):
                    mantid_records(self.hkl, LAYOUT)

    def test_all_zero_terminator(self):
        self.hkl.write_text(source_row(1.09464) + indices((0, 0, 0)) + " 0" * 19 + "\n")
        self.assertEqual(len(mantid_records(self.hkl, LAYOUT)), 1)

    def test_both_clis_require_layout(self):
        self.write_m90(m90_row(1.0946, 1001))
        self.m83.write_text(m83_row(1001))
        for script, args in (
            ("filter_m90_wavelength.py", ["--m90-in", str(self.m90), "--m90-out", str(self.out)]),
            ("plot_extinction_wavelength.py", ["--m83", str(self.m83)]),
        ):
            with self.subTest(script=script):
                command = [sys.executable, str(SCRIPTS / script), "--hkl", str(self.hkl), *args]
                missing = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(missing.returncode, 2, missing.stderr)
                self.assertIn("--hkl-layout", missing.stderr)
                valid = subprocess.run([*command, "--hkl-layout", LAYOUT], capture_output=True, text=True)
                self.assertEqual(valid.returncode, 0, valid.stderr)


if __name__ == "__main__":
    unittest.main()
