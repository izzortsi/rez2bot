import argparse
import numpy as np

parser = argparse.ArgumentParser()

parser.add_argument("-e", nargs=6, metavar=('b0', 'b1', 'b2', 'b3', 'b4', 'b5'),
                        help="my help message", type=float,
                        default=(1.0, 1.364, 1.618, 1.854, 2.0, 2.364))


args = parser.parse_args()

coefs = np.array(args.e)


# %%
