def asdf(x):
    return x**5


def fdsa(x):
    return asdf(x)/2.

if __name__ == '__main__':
    from multiprocessing import Pool
    pool = Pool(4)


    print pool.map(fdsa, range(5))
