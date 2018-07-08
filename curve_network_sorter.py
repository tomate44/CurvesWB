
def maxRowIndex(m, irow):
    """returns the column index if the maximum of i-th row"""
    max = -1e50
    jmax = 0
    for jcol in range(len(m[0])):
        if m[irow][jcol] > max:
            max = m[irow][jcol]
            jmax = jcol)
    return jmax

    // returns the row index if the maximum of i-th col
    size_t maxColIndex(const math_Matrix& m, size_t jcol)
    {
        double max = DBL_MIN;
        size_t imax = 0;

        for (Standard_Integer irow = 0; irow < m.RowNumber(); ++irow) {
            if (m(irow, static_cast<Standard_Integer>(jcol)) > max) {
                max = m(irow, static_cast<Standard_Integer>(jcol));
                imax = static_cast<size_t>(irow);
            }
        }

        return imax;
    }

    // returns the column index if the minimum of i-th row
    size_t minRowIndex(const math_Matrix& m, size_t irow)
    {
        double min = DBL_MAX;
        size_t jmin = 0;

        for (Standard_Integer jcol = 0; jcol < m.ColNumber(); ++jcol) {
            if (m(static_cast<Standard_Integer>(irow), jcol) < min) {
                min = m(static_cast<Standard_Integer>(irow), jcol);
                jmin = static_cast<size_t>(jcol);
            }
        }

        return jmin;
    }

    // returns the column index if the minimum of i-th row
    size_t minColIndex(const math_Matrix& m, size_t jcol)
    {
        double min = DBL_MAX;
        size_t imin = 0;

        for (Standard_Integer irow = 0; irow < m.RowNumber(); ++irow) {
            if (m(irow, static_cast<Standard_Integer>(jcol)) < min) {
                min = m(irow, static_cast<Standard_Integer>(jcol));
                imin = static_cast<size_t>(irow);
            }
        }

        return imin;
    }

}
