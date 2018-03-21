

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
        

bb = bsplineBasis()
bb.U = [0.,0.,0.,1.,2.,3.,4.,4.,5.,5.,5.]
bb.p = 2
span = bb.findSpan(2.5)
print(span)




