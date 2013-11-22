'''
Helper functions.

@author: anze.vavpetic@ijs.si
'''
from math import sqrt

def avg(x):
    return sum(x)/float(len(x))

def std(x):
    n = float(len(x))
    return sqrt((sum(i*i for i in x) - sum(x)**2/n)/n)
