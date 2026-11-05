import sys
import matplotlib.pyplot as plt
import numpy as np

name = sys.argv[1] if len(sys.argv) > 1 else "dqn_low_seed0"
ret = np.loadtxt(f"logs/{name}.monitor.csv", delimiter=",", skiprows=2, usecols=0)

plt.plot(ret, alpha=0.4, label="episode return")
if len(ret) >= 5:
    plt.plot(np.arange(4, len(ret)), np.convolve(ret, np.ones(5) / 5, mode="valid"),
             label="moving average (5)")
plt.xlabel("episode")
plt.ylabel("return")
plt.title(name)
plt.legend()
plt.savefig(f"logs/{name}.png")
plt.show()
