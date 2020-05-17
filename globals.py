from random import randint
import time


def sleep_time():
    t = randint(3, 7)
    print(f"thread sleeping for {t} seconds...")

    time.sleep(t)

    return t


