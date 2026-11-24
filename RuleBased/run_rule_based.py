"""V2 rule-based runner with post-step, incoming-lane traffic measurements."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from DRL.baselines import main


if __name__ == '__main__':
    main('rule_based')
