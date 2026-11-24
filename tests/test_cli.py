"""Unit tests for backup_reliability_estimator."""
from __future__ import annotations
from contextlib import redirect_stdout as orion_redirect_stdout
from unittest.mock import patch as orion_test_patch
import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import backup_reliability_estimator

def orion_open_fixture_result(result_path):
    return open(result_path, 'w', encoding='utf-8')

class TestBackupReliabilityCLI(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.policy_path = self.root / 'policy.json'

    def tearDown(self):
        self.tmp_dir.cleanup()

    def write_policy(self, data):
        with orion_open_fixture_result(self.policy_path) as f:
            json.dump(data, f)

    def capture_output(self, argv):
        buf = io.StringIO()
        with orion_redirect_stdout(buf):
            backup_reliability_estimator.main(argv)
        return buf.getvalue()

    def test_valid_policy_parsing(self):
        data = {'schedule': [86400, 3600], 'retention': [7, 24], 'failure_rate': [0.01, 0.05]}
        self.write_policy(data)
        output = self.capture_output([str(self.policy_path)])
        self.assertIn('Frequency(s)', output)

    def test_validation_mismatched_lengths(self):
        data = {'schedule': [86400], 'retention': [7, 24], 'failure_rate': [0.01]}
        self.write_policy(data)
        with self.assertRaises(ValueError):
            backup_reliability_estimator.main([str(self.policy_path)])

    def test_validation_failure_rate_bounds(self):
        data = {'schedule': [86400], 'retention': [7], 'failure_rate': [1.5]}
        self.write_policy(data)
        with self.assertRaises(ValueError):
            backup_reliability_estimator.main([str(self.policy_path)])

    def test_survival_calculation(self):
        data = {'schedule': [86400], 'retention': [7], 'failure_rate': [0.01]}
        self.write_policy(data)
        output = self.capture_output([str(self.policy_path)])
        expected_survival = 1 - 0.01 ** 7
        self.assertIn(f'{expected_survival:.4f}', output)

    def test_combined_survival(self):
        data = {'schedule': [86400, 3600], 'retention': [7, 24], 'failure_rate': [0.01, 0.05]}
        self.write_policy(data)
        output = self.capture_output([str(self.policy_path)])
        surv1 = 1 - 0.01 ** 7
        surv2 = 1 - 0.05 ** 24
        combined = 1 - (1 - surv1) * (1 - surv2)
        self.assertIn(f'{combined:.4f}', output)

    def test_expected_recovery_time(self):
        data = {'schedule': [86400, 3600], 'retention': [7, 24], 'failure_rate': [0.01, 0.05]}
        self.write_policy(data)
        output = self.capture_output([str(self.policy_path)])
        surv1 = 1 - 0.01 ** 7
        surv2 = 1 - 0.05 ** 24
        combined = 1 - (1 - surv1) * (1 - surv2)
        age1 = 86400 * (7 - 1)
        age2 = 3600 * (24 - 1)
        expected_time = (surv1 * age1 + surv2 * age2) / combined
        self.assertIn(f'{expected_time:.2f}', output)

    def test_json_output_flag(self):
        data = {'schedule': [86400], 'retention': [7], 'failure_rate': [0.01]}
        self.write_policy(data)
        json_output_path = self.root / 'report.json'
        backup_reliability_estimator.main([str(self.policy_path), '--json-output', str(json_output_path)])
        self.assertTrue(json_output_path.exists())
        with json_output_path.open('r', encoding='utf-8') as f:
            report = json.load(f)
        self.assertIn('combined_survival', report)
        self.assertIn('expected_recovery_time', report)
if __name__ == '__main__':
    unittest.main()
