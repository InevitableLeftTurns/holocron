def clamp(n: int, low: int, high: int):
    if n < low:
        return low
    elif n > high:
        return high
    else:
        return n
