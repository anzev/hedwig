'''
Helper functions.

@author: anze.vavpetic@ijs.si
'''
from math import sqrt


def avg(x):
    n = float(len(x))
    if n:
        return sum(x)/n
    else:
        return 0


def std(x):
    n = float(len(x))
    if n:
        return sqrt((sum(i*i for i in x) - sum(x)**2/n)/n)
    else:
        return 0
