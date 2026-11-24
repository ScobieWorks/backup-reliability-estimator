# backup-reliability-estimator

A lightweight, pure‑Python command‑line tool that estimates the reliability of a backup policy.  It reads a JSON policy file describing backup frequencies, retention counts, and failure rates, and outputs:

* Survival probability per frequency.
* Combined survival probability (at least one backup succeeds).
* Expected recovery time (age of the surviving backup).

The tool prints a concise table and can optionally write a machine‑readable JSON report.

## Installation

No installation is required – simply copy the `backup_reliability_estimator.py` file to a directory on your ``PATH`` or run it with ``python -m``.

## Usage

```bash
$ python backup_reliability_estimator.py policy.json
```

### Policy file format

```json
{
  "schedule": [86400, 3600],
  "retention": [7, 24],
  "failure_rate": [0.01, 0.05]
}
```

* ``schedule`` – list of backup frequencies in seconds.
* ``retention`` – number of past runs kept for each frequency.
* ``failure_rate`` – probability that a single backup run fails (0‑1).

### Optional JSON output

```bash
$ python backup_reliability_estimator.py policy.json --json-output report.json
```

The JSON report contains the same data as the table, plus the computed metrics.

## Testing

Run the test suite with:

```bash
$ python -m unittest discover -s tests -v
```

The tests cover parsing, validation, core calculations, and JSON output.


## Installation

```bash
pip install git+https://github.com/ScobieWorks/backup-reliability-estimator.git
```


## Command-line usage

```bash
backup-reliability-estimator --help
```

## Limitations
<!-- generated-limitations:692368cd1fe841f09cb808f47ceb6ec15ecdbcf426615850de970a8150dcba89 -->
- The text reader in `backup_reliability_estimator.py` uses UTF-8; supply UTF-8 text for that reading path.
<!-- /generated-limitations -->
