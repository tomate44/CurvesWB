# SPDX-License-Identifier: LGPL-2.1-or-later

def float_range(start, end, number):
    'Generates a number of floats between start and end'
    fr = end - start
    for i in range(number):
        yield start + i * fr / (number - 1)


def scaled_list(numlist, start=0.0, end=1.0):
    'Generates numbers in numlist, scaled between start and end'
    l0, l1 = numlist[0], numlist[-1]
    lr = l1 - l0
    for v in numlist:
        yield start + (end - start) * (v - l0) / lr
