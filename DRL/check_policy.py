import sys

import numpy as np
import torch
from stable_baselines3 import DQN

rng = np.random.default_rng(0)
obs = None
for path in sys.argv[1:]:
    model = DQN.load(path)
    obs = rng.random((20000, model.observation_space.shape[0])).astype(np.float32)
    with torch.no_grad():
        q = model.q_net(torch.as_tensor(obs)).numpy()
    share = float((q.argmax(axis=1) == 1).mean())
    print(f"{path}: SWITCH chosen {share:.1%} of random observations, mean Q(SWITCH)-Q(KEEP) = {(q[:, 1] - q[:, 0]).mean():+.3f}")
    