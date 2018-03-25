

class bsplineBasis:
    '''Computes basis functions of a bspline curve, and its derivatives'''
    def __init__(self):
        self.knots = [0.0, 0.0, 1.0, 1.0]
        self.degree = 1

    def findSpan(self,u):
        """ Determine the knot span index.
        - input: parameter u (float)
        - output: the knot span index (int)
        Nurbs Book Algo A2.1 p.68
        """
        n = len(self.knots)-self.degree-1
        if u == self.knots[n+1]:
            return(n-1)
        low = self.degree
        high = n+1
        mid = int((low+high)/2)
        while (u < self.knots[mid] or u >= self.knots[mid+1]):
            if (u < self.knots[mid]):
                high = mid
            else:
                low = mid
            mid = int((low+high)/2)
        return(mid)

    def basisFuns(self, i, u):
        """ Compute the nonvanishing basis functions.
        - input: start index i (int), parameter u (float)
        - output: basis functions values N (list of floats)
        Nurbs Book Algo A2.2 p.70
        """
        N = [0. for x in range(self.degree+1)]
        N[0] = 1.0
        left = [0.0]
        right = [0.0]
        for j in range(1,self.degree+1):
            left.append(u-self.knots[i+1-j])
            right.append(self.knots[i+j]-u)
            saved = 0.0
            for r in range(j):
                temp = N[r] / (right[r+1] + left[j-r])
                N[r] = saved + right[r+1] * temp
                saved = left[j-r]*temp
            N[j] = saved
        return(N)

    def dersBasisFuns(self, i, u, n):
        """ Compute nonzero basis functions and their derivatives.
        First section is A2.2 modified to store functions and knot differences.
        - input: start index i (int), parameter u (float), number of derivatives n (int)
        - output: basis functions and derivatives ders (array2d of floats)
        Nurbs Book Algo A2.3 p.72
        """
        ders = [[0.0 for x in range(self.degree+1)] for y in range(n+1)]
        ndu = [[1.0 for x in range(self.degree+1)] for y in range(self.degree+1)] 
        ndu[0][0] = 1.0
        left = [0.0]
        right = [0.0]
        for j in range(1,self.degree+1):
            left.append(u-self.knots[i+1-j])
            right.append(self.knots[i+j]-u)
            saved = 0.0
            for r in range(j):
                ndu[j][r] = right[r+1] + left[j-r]
                temp = ndu[r][j-1] / ndu[j][r]
                ndu[r][j] = saved + right[r+1] * temp
                saved = left[j-r]*temp
            ndu[j][j] = saved

        for j in range(0,self.degree+1):
            ders[0][j] = ndu[j][self.degree]
        for r in range(0,self.degree+1):
            s1 = 0
            s2 = 1
            a = [[0.0 for x in range(self.degree+1)] for y in range(2)]
            a[0][0] = 1.0
            for k in range(1,n+1):
                d = 0.0
                rk = r-k
                pk = self.degree-k
                if r >= k:
                    a[s2][0] = a[s1][0] / ndu[pk+1][rk]
                    d = a[s2][0] * ndu[rk][pk]
                if rk >= -1:
                    j1 = 1
                else:
                    j1 = -rk
                if (r-1) <= pk:
                    j2 = k-1
                else:
                    j2 = self.degree-r
                for j in range(j1,j2+1):
                    a[s2][j] = (a[s1][j]-a[s1][j-1]) / ndu[pk+1][rk+j]
                    d += a[s2][j] * ndu[rk+j][pk]
                if r <= pk:
                    a[s2][k] = -a[s1][k-1] / ndu[pk+1][r]
                    d += a[s2][k] * ndu[r][pk]
                ders[k][r] = d
                j = s1
                s1 = s2
                s2 = j
        r = self.degree
        for k in range(1,n+1):
            for j in range(0,self.degree+1):
                ders[k][j] *= r
            r *= (self.degree-k)
        return(ders)

    def evaluate(self, u, d):
        """ Compute the derivative d of the basis functions.
        - input: parameter u (float), derivative d (int)
        - output: derivative d of the basis functions (list of floats)
        """
        n = len(self.knots)-self.degree-1
        f = [0.0 for x in range(n)]
        span = self.findSpan(u)
        ders = self.dersBasisFuns(span, u, d)
        for i,val in enumerate(ders[d]):
            f[span-self.degree+i] = val
        return(f)

def test():
    bb = bsplineBasis()
    bb.knots = [0.,0.,0.,0.,1.,2.,3.,3.,3.,3.]
    bb.degree = 3
    parm = 3.0

    span = bb.findSpan(parm)
    print("Span index : %d"%span)
    f0 = bb.evaluate(parm,d=0)
    f1 = bb.evaluate(parm,d=1)
    f2 = bb.evaluate(parm,d=2)
    print("Basis functions    : %r"%f0)
    print("First derivatives  : %r"%f1)
    print("Second derivatives : %r"%f2)
    
    # compare to splipy results
    try:
        import splipy
    except ImportError:
        print("splipy is not installed.")
        return(False)
    
    basis1 = splipy.BSplineBasis(order=bb.degree+1, knots=bb.knots)
    
    print("splipy results :")
    print(basis1.evaluate(parm,d=0).A1.tolist())
    print(basis1.evaluate(parm,d=1).A1.tolist())
    print(basis1.evaluate(parm,d=2).A1.tolist())

