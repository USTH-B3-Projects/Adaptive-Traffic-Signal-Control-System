"""V2 fixed-time runner; historical log paths are never reused."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from DRL.baselines import main


if __name__ == '__main__':
    main('fixed_time')
