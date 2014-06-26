from random import random

__author__ = 'flex109'


def binomial_probability(n, p, k):
    def fact(num):
        if num == 1 or num == 0:
            return 1
        return num * fact(num-1)

    def factorial(num):
        return float(fact(num))

    return (factorial(n)/(factorial(k)*factorial(n-k))) * p**k * (1-p)**(n-k)

def get_binomial_result(low, high, p):
    n = high-low
    roll = random()
    prob_sum = 0.0
    for i in range(0, n+1):
        prob_sum += binomial_probability(n, p, i)
        if roll < prob_sum:
            return low + i

    raise ArithmeticError()
