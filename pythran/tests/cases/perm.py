#pythran export permutations(int list, int)
#def permutations(iterable, r=None):
def permutations(iterable, r):
    """permutations(range(3), 2) --> (0,1) (0,2) (1,0) (1,2) (2,0) (2,1)"""
    out=[]
    pool = tuple(iterable)
    n = len(pool)
    r = n
    indices = range(n)
    cycles = range(n-r+1, n+1)[::-1]
    out.append( tuple([pool[i] for i in indices[:r]]))
    while n:
        for i in reversed(xrange(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                out.append( tuple([pool[i] for i in indices[:r]]))
                break
        else:
            return out
    return out
