import numpy as np
from scipy import sparse 
#from scipy.sparse.linalg import cg
from solver import ConjugateGradient as cg
try:
    from numba import jit
    USE_JIT = True
    print('Numba acceleration enabled.')
except:
    USE_JIT = False
    print('Numba is not installed. Install Numba to speed up your experience.')



def CenterConv(A, a = 4, b = -1):
    '''
    Given a matrix A, compute its convolution B:
    B[x,y] = a * A[x,y] + b * (A[x-1,y] + A[x+1,y] + A[x,y-1] + A[x,y+1])

    Dtypes of A,B should be float. Borders are ignored.
    '''
    B = (a/b) * A
    B[1:-1,1:-1] += A[:-2 ,1:-1]
    B[1:-1,1:-1] += A[2:  ,1:-1]
    B[1:-1,1:-1] += A[1:-1, :-2]
    B[1:-1,1:-1] += A[1:-1,2:  ]
    B *= b    
    return B
    


def GuidanceField(bg, fg, gradient = 'mixed'):
    assert gradient in ('foreground', 'mixed'), 'Unsupported choice of gradient field.'
    if gradient == 'foreground':
        nabla = CenterConv(fg, 4, -1)

    elif gradient == 'mixed':
        def dominate(x, y):
            return np.where(np.abs(x) > np.abs(y), x, y)
    
        nabla = np.zeros(bg.shape)
        nabla[1:-1,1:-1] += dominate(bg[1:-1,1:-1] - bg[:-2 ,1:-1], fg[1:-1,1:-1] - fg[:-2 ,1:-1])
        nabla[1:-1,1:-1] += dominate(bg[1:-1,1:-1] - bg[2:  ,1:-1], fg[1:-1,1:-1] - fg[2:  ,1:-1])
        nabla[1:-1,1:-1] += dominate(bg[1:-1,1:-1] - bg[1:-1, :-2], fg[1:-1,1:-1] - fg[1:-1, :-2])
        nabla[1:-1,1:-1] += dominate(bg[1:-1,1:-1] - bg[1:-1,2:  ], fg[1:-1,1:-1] - fg[1:-1,2:  ])
        
    return nabla



def CountIndices(mask, boundary, indices):
    '''Index each pixel in the region.'''
    s = 0 # counter
    for i in range(1, mask.shape[0] - 1):
        for j in range(1, mask.shape[1] - 1):
            if mask[i,j] and not boundary[i,j]: # white: in the region
                indices[i,j] = s 
                s += 1
    return s
if USE_JIT:
    CountIndices = jit(CountIndices)



def ConstructSystem(bg, nabla, mask, boundary, indices, csr_x, csr_y, csr_data, aim, t):
    '''Construct the Poisson linear system.
    Note that the input ndarrays here are all references (pointers).'''   
    s = 0 # reset counter
    for i in range(1, mask.shape[0] - 1):
        for j in range(1, mask.shape[1] - 1):
            if mask[i,j] and not boundary[i,j]: # white: in the region
                # row s of the linear system 
                aim[s] = nabla[i,j]
                for d in ((-1,0), (1,0), (0,-1), (0,1)):
                    u, v = i + d[0], j + d[1]
                    csr_data[s] = 4
                    if mask[u,v]:
                        if boundary[u,v]: # known values are on the right hand side
                            aim[s] += bg[u,v] 
                        else: # add csr entries
                            csr_x[t] = s 
                            csr_y[t] = indices[u,v]
                            csr_data[t] = -1
                            t += 1
                s += 1
    return t
if USE_JIT:
    ConstructSystem = jit(ConstructSystem)



def RenderResult(background, mask, boundary, channel, x, y, sol):
    '''Render the solution to the background image.'''
    s = 0 # reset counter
    for i in range(1, mask.shape[0] - 1):
        for j in range(1, mask.shape[1] - 1):
            if mask[i,j] and not boundary[i,j]: # white: in the region
                background[x+i-1,y+j-1,channel] = sol[s]
                s += 1
if USE_JIT:
    RenderResult = jit(RenderResult)



def PoissonBlending(background, foreground, mask, x, y, gradient = 'mixed', dtype = 'int'):
    '''Parameters
    ---------
    background: background image

    foreground: foreground image 

    mask: boolean ndarray
        the target region of Ω on the foreground image

    x , y: the topleft coordinate where we place the foreground image

    gradient: 'foreground' / 'mixed'
        the gradient field choice

    dtype: 'int' / 'float'
        the returned image's ndarray dtype
    '''

    foreground, background, mask, x, y = Preprocess(foreground, background, mask, x, y)

    # neighbors: the number of neighbors that fall in the region Ω for each pixel
    neighbors = CenterConv(mask, 0, 1)

    # boundaries of the region are pixels with 1~3 neighbors
    boundary = np.where(np.abs(neighbors - 2) < 2, 1, 0)

    # index each pixel in the region
    indices = np.zeros(mask.shape, dtype='int32')
    s = CountIndices(mask, boundary, indices)  # number of pixels in the region

    for channel in range(3): 
        # solve the Poisson equation channel-wise
        bg = background[x: x + mask.shape[0] - 2, y: y + mask.shape[1] - 2, channel]
        fg = foreground[:,:,channel]
        bg = np.pad(bg, ((1,1),(1,1)), mode = 'edge')
        fg = np.pad(fg, ((1,1),(1,1)), mode = 'edge')


        # compute the guidance field
        nabla = GuidanceField(bg, fg, gradient)

        # construct the sparse linear system with size  s x s
        # diagonal entry
        t = 5 * s  # upper bound for nonzero entries
        csr_x    = np.arange(t, dtype = 'int32')
        csr_y    = np.arange(t, dtype = 'int32')
        csr_data = np.zeros(t, dtype = 'float64')
        aim      = np.zeros(s, dtype = 'float64')
        
        # construct the sparse linear system with size  s x s
        # the arrays csr_x, csr_y, csr_data, aim get modified in this function
        t = ConstructSystem(bg, nabla, mask, boundary, indices, csr_x, csr_y, csr_data, aim, s)

        csr_x = csr_x[:t]
        csr_y = csr_y[:t]
        csr_data = csr_data[:t]

        csr = sparse.csr_matrix((csr_data, (csr_x, csr_y)), shape = (s,s), dtype = 'float64')

        # solve the equation "csr * x = aim"
        sol = cg(csr, aim, tol = 1e-5, maxiter = 200)
        # sol = sol[0]    # need this line when using scipy.sparse.linalg.cg

        RenderResult(background, mask, boundary, channel, x, y, sol)

    # from matplotlib import pyplot as plt 
    # plt.imshow(background)
    # plt.show()
    if dtype == 'int':
        background = np.round(background * 255).clip(0, 255).astype('uint8')
    elif dtype == 'float':
        background = background.cilp(0,1)
    return background



def Preprocess(foreground, background, mask, x, y):
    """
    Parameters
    --------
    foreground: ndarray, the input foreground image
    
    backgorund: ndarray, the input background image

    mask: boolean ndarray
        the target region of Ω on the foreground image

    x , y: the topleft coordinate where we place the foreground image
    """    

    # modify the format
    if background.dtype == 'uint8': background = background / 255. 
    if foreground.dtype == 'uint8': foreground = foreground / 255. 

    # crop the foreground image
    if x < 0:
        foreground = foreground[-x:, :]
        mask       =       mask[-x:, :]
        x = 0
    if y < 0:
        foreground = foreground[:, -y:]
        mask       =       mask[:, -y:]
        y = 0
    if x + foreground.shape[0] > background.shape[0]:
        foreground = foreground[:(background.shape[0] - x)]
        mask       =       mask[:(background.shape[0] - x)]
    if y + foreground.shape[1] > background.shape[1]:
        foreground = foreground[:, :(background.shape[1] - y)]
        mask       =       mask[:, :(background.shape[1] - y)]

    mask = np.pad(mask, ((1,1),(1,1))).astype('uint8')

    return foreground, background, mask, x, y


if __name__ == '__main__':
    # an illustration of central difference
    def f(x,y):
        return x*x*y*y 
    h = .001
    x , y = 1 , 1
    print(
        (-4*f(x,y)+f(x-h,y)+f(x+h,y)+f(x,y-h)+f(x,y+h))/h/h
    )