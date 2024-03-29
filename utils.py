import numpy as np

# NaN and None are interchangeable for numpy
def isNull(_n):
    return (_n is None) or np.isnan(_n)

# This function transforms the error into a value that ranges from 1 (if the error is 0) and asymptotes to -1 ( if the error is infinite)
def constraintFunction(error, tolerance):
    if isNull(error):
        return -1.0
    else:
        return 2.0 / ( 1.0 + (error / tolerance)**2 ) - 1.0