from time import time
from numpy import zeros

def ConjugateGradient(A, b, tol = 1e-5, maxiter = 50):
    '''
    Solve Ax = b using Conjugate Gradient.

    Parameters
    --------
    A: scipy.sparse / numpy matrix, shape (n, n)

    b: numpy array, shape (n, )

    tol: float
        tolerance of the residual

    maxiter: int
        maximum iteration number

    Return
    --------
    x: vector
        the (approximate) solution to Ax = b
    '''
    
    time_start = time()
    n = A.shape[0]
    
    x = zeros(b.shape) 
    r = b.copy()
    p = b.copy()
    normr = r.T @ r
    normr2 = normr
    
    for i in range(1, 1 + maxiter):
        v = A @ p 
        alpha = normr / (p.T @ v)
        x += alpha * p
        r -= alpha * v
        normr2 = r.T @ r        
        if normr2 < tol:
            break 
        beta = normr2 / normr
        normr = normr2
        p = r + beta * p

    time_end = time()
    print('Size = %d  Time = %.2f sec  Iter = %d  Residual = %.6f'%(
                  n, time_end - time_start, i, normr2))

    return x
    