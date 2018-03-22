

class bsplineBasis:
    '''Computes basis functions of a bspline curve, and its derivatives'''
    def __init__(self):
        self.U = [0.0, 0.0, 1.0, 1.0]
        self.p = 2

    def findSpan(self,u):
        """ Determine the knot span index.
        - input: parameter u (float)
        - output: the knot span index (int)
        Nurbs Book Algo A2.1 p.68
        """
        n = len(self.U)-self.p-1
        if u == self.U[n+1]:
            return(n)
        low = self.p
        high = n+1
        mid = int((low+high)/2)
        while (u < self.U[mid] or u >= self.U[mid+1]):
            if (u < self.U[mid]):
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
        N = [1.0] + [0.]*(self.p)
        left = [0.0]
        right = [0.0]
        for j in range(1,self.p+1):
            left.append(u-self.U[i+1-j])
            right.append(self.U[i+j]-u)
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
        ders = [[0.0]*(self.p+1)] * (n+1)
        #print(ders)
        ndu = [[0.0]*(self.p+1)] * (self.p+1)
        ndu[0][0] = 1.0
        left = [0.0]
        right = [0.0]
        for j in range(1,self.p+1):
            left.append(u-self.U[i+1-j])
            right.append(self.U[i+j]-u)
            saved = 0.0
            for r in range(j):
                ndu[j][r] = right[r+1] + left[j-r]
                temp = ndu[r][j-1] / ndu[j][r]
                ndu[r][j] = saved + right[r+1] * temp
                saved = left[j-r]*temp
            ndu[j][j] = saved
        print("ndu: %r"%ndu)
        for j in range(0,self.p+1):
            ders[0][j] = ndu[j][self.p]
        for r in range(0,self.p+1):
            s1 = 0
            s2 = 1
            a = [[0.0]*(self.p+1)] * 2
            a[0][0] = 1.0
            for k in range(1,n+1):
                d = 0.0
                rk = r-k
                pk = self.p-k
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
                    j2 = self.p-r
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
        r = self.p
        for k in range(1,n+1):
            for j in range(0,self.p+1):
                ders[k][j] *= r
            r *= (self.p-k)
        return(ders)

bb = bsplineBasis()
bb.U = [0.,0.,0.,1.,2.,3.,4.,4.,5.,5.,5.]
bb.p = 2
span = bb.findSpan(2.5)
print(span)
bas = bb.basisFuns(span,2.5)
print(bas)
ders = bb.dersBasisFuns(span,2.5,2)
print(ders)


