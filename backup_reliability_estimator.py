"""Backup Reliability Estimator.

This module implements a command‑line tool that reads a JSON policy file
containing three lists: ``schedule`` (seconds between runs), ``retention``
(number of past runs kept), and ``failure_rate`` (probability a single run
fails).  It computes per‑frequency survival probabilities, the combined
survival probability assuming independence, and the expected recovery time.

The tool prints a concise table and can optionally write a machine‑readable
JSON report to a file specified with ``--json-output``.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import List, Dict, Any

def parse_policy(policy_path: Path) -> Dict[str, List[Any]]:
    """Load and validate a policy JSON file.

    The JSON must contain three lists of equal length: ``schedule``,
    ``retention`` and ``failure_rate``.  ``failure_rate`` values must be in
    the inclusive range [0, 1].
    """
    with policy_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    schedule = data.get('schedule')
    retention = data.get('retention')
    failure_rate = data.get('failure_rate')
    if not (isinstance(schedule, list) and isinstance(retention, list) and isinstance(failure_rate, list)):
        raise ValueError('Policy must contain lists for schedule, retention, and failure_rate')
    if not len(schedule) == len(retention) == len(failure_rate):
        raise ValueError('schedule, retention, and failure_rate lists must be of equal length')
    for fr in failure_rate:
        if not 0.0 <= fr <= 1.0:
            raise ValueError('failure_rate values must be between 0 and 1')
    return {'schedule': schedule, 'retention': retention, 'failure_rate': failure_rate}

def compute_survival(schedule: List[int], retention: List[int], failure_rate: List[float]) -> List[float]:
    """Return a list of survival probabilities for each frequency."""
    return [1 - fr ** r for fr, r in zip(failure_rate, retention)]

def compute_combined_survival(survivals: List[float]) -> float:
    """Compute the probability that at least one frequency succeeds.

    Assumes independence across frequencies.
    """
    prod = 1.0
    for s in survivals:
        prod *= 1 - s
    return 1 - prod

def compute_expected_recovery_time(schedule: List[int], retention: List[int], survivals: List[float], combined_survival: float) -> float:
    """Estimate the expected age of the surviving backup.

    The age of the newest retained run for a frequency is
    ``frequency * (retention - 1)``.  The expected time is the weighted
    average of these ages, weighted by the survival probability of each
    frequency.
    """
    if combined_survival == 0:
        return float('inf')
    weighted_sum = 0.0
    for freq, ret, surv in zip(schedule, retention, survivals):
        age = freq * (ret - 1)
        weighted_sum += surv * age
    return weighted_sum / combined_survival

def format_table(schedule: List[int], retention: List[int], failure_rate: List[float], survivals: List[float], combined_survival: float, expected_time: float) -> str:
    """Return a human‑readable table as a string."""
    lines = []
    header = f"{'Frequency(s)':>12} | {'Retention':>8} | {'Failure Rate':>12} | {'Survival Prob':>13}"
    lines.append(header)
    lines.append('-' * len(header))
    for freq, ret, fr, surv in zip(schedule, retention, failure_rate, survivals):
        lines.append(f'{freq:12d} | {ret:8d} | {fr:12.4f} | {surv:13.4f}')
    lines.append('')
    lines.append(f'Combined Survival Probability: {combined_survival:.4f}')
    lines.append(f'Expected Recovery Time (s): {expected_time:.2f}')
    return '\n'.join(lines)

def write_json_report(result_path: Path, data: Dict[str, Any]) -> None:
    """Write a JSON report to *result_path*.

    The function uses the built‑in ``open``; no ``Path.write_text`` is used.
    """
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def main(argv: List[str] | None=None) -> None:
    parser = argparse.ArgumentParser(description='Backup Reliability Estimator')
    parser.add_argument('policy', type=Path, help='Path to JSON policy file')
    parser.add_argument('--json-output', type=Path, help='Path to write JSON report')
    args = parser.parse_args(argv)
    policy = parse_policy(args.policy)
    schedule = policy['schedule']
    retention = policy['retention']
    failure_rate = policy['failure_rate']
    survivals = compute_survival(schedule, retention, failure_rate)
    combined_survival = compute_combined_survival(survivals)
    expected_time = compute_expected_recovery_time(schedule, retention, survivals, combined_survival)
    table = format_table(schedule, retention, failure_rate, survivals, combined_survival, expected_time)
    print(table)
    if args.json_output:
        report = {'schedule': schedule, 'retention': retention, 'failure_rate': failure_rate, 'survivals': survivals, 'combined_survival': combined_survival, 'expected_recovery_time': expected_time}
        write_json_report(args.json_output, report)
if __name__ == '__main__':
    main()
