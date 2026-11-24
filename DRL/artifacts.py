"""V2 output boundaries: historical artifacts must never be overwritten."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOTS = tuple(ROOT / p for p in (
    'models/seed100', 'evaluation/seed100', 'results/seed100', 'runs/ppo_seed100'))
REPORT = ROOT / 'results/comparison_result/drl_seed100_v2_report.md'


def output_path(path):
    path = Path(path).resolve()
    if path != REPORT and not any(path == p or p in path.parents for p in OUTPUT_ROOTS):
        raise ValueError(f'V2 output must stay in seed100 directories: {path}')
    return path


def empty_directory(path):
    path = output_path(path)
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f'Refusing to reuse non-empty run directory: {path}')
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_csv(path, rows):
    path = output_path(path)
    rows = list(rows)
    if not rows:
        raise ValueError('Cannot write an empty metric table')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
