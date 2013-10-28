# encoding: utf-8
#cython: cdivision=True
#cython: boundscheck=False
# cython: wraparound=False

import numpy as np

cimport numpy as np
cimport cython

np.import_array()

def chi2_distance(long[:] x,
                  long[:] y):
    """Chi-square histogram distance.

    Ignores bins with no elements.

    """
    cdef long i
    cdef long n = len(x)
    cdef long x_elt
    cdef long y_elt
    cdef double x_max = 0
    cdef double y_max = 0
    cdef double x_norm_elt
    cdef double y_norm_elt
    cdef double d
    cdef double s
    cdef double result = 0
    for i in range(n):
        x_max = max(x_max, x[i])
        y_max = max(y_max, y[i])
    if x_max == 0 or y_max == 0:
        raise Exception('empty histogram')
    for i in range(n):
        x_elt = x[i]
        y_elt = y[i]
        if x_elt == 0 and y_elt == 0:
            continue
        x_norm_elt = x_elt / x_max
        y_norm_elt = y_elt / y_max
        d = x_norm_elt - y_norm_elt
        s = x_norm_elt + y_norm_elt
        result += (d * d) / s
    return result / 2