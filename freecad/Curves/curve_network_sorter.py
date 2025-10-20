# SPDX-License-Identifier: Apache-2.0

# This file is a python port of /src/guide_curves/CTiglCurveNetworkSorter.cpp
# from the Tigl library : https://github.com/DLR-SC/tigl under Apache-2 license
import FreeCAD
from freecad.Curves import nurbs_tools

DEBUG = False


def debug(o):
    if not DEBUG:
        return
    FreeCAD.Console.PrintMessage("%s\n" % o)


def maxRowIndex(m, irow):
    """returns the column index of the maximum of i-th row"""
    maxi = -1e50
    jmax = 0
    for jcol in range(len(m[0])):
        if m[irow][jcol] > maxi:
            maxi = m[irow][jcol]
            jmax = jcol
    return jmax


def maxColIndex(m, jcol):
    """returns the row index of the maximum of i-th col"""
    maxi = -1e50
    imax = 0
    for irow in range(len(m)):
        if m[irow][jcol] > maxi:
            maxi = m[irow][jcol]
            imax = irow
    return imax


def minRowIndex(m, irow):
    """returns the column index of the minimum of i-th row"""
    mini = 1e50
    jmin = 0
    for jcol in range(len(m[0])):
        if m[irow][jcol] < mini:
            mini = m[irow][jcol]
            jmin = jcol
    return jmin


def minColIndex(m, jcol):
    """returns the row index of the minimum of i-th col"""
    mini = 1e50
    imin = 0
    for irow in range(len(m)):
        if m[irow][jcol] < mini:
            mini = m[irow][jcol]
            imin = irow
    return imin


def swap(o, i, j):
    """swap o[i] and o[j]"""
    o[i], o[j] = o[j], o[i]


def swap_row(o, i, j):
    """swap rows i and j of 2d array o"""
    o[i], o[j] = o[j], o[i]


def swap_col(o, i, j):
    """swap cols i and j of 2d array o"""
    for row in o:
        row[i], row[j] = row[j], row[i]


class CurveNetworkSorter(object):
    def __init__(self, profiles, guides, parmsIntersProfiles, parmsIntersGuides):
        self.has_performed = False
        if (len(profiles) < 2) or (len(guides) < 2):
            raise ValueError("Not enough guides or profiles")
        else:
            self.profiles = profiles
            self.guides = guides
            self.n_profiles = len(profiles)
            self.n_guides = len(guides)
        self.parmsIntersProfiles = parmsIntersProfiles
        self.parmsIntersGuides = parmsIntersGuides
        if not self.n_profiles == len(self.parmsIntersProfiles):
            raise ValueError("Invalid row size of parmsIntersProfiles matrix.")
        if not self.n_profiles == len(self.parmsIntersGuides):
            raise ValueError("Invalid row size of parmsIntersGuides matrix.")
        if not self.n_guides == len(self.parmsIntersProfiles[0]):
            raise ValueError("Invalid col size of parmsIntersProfiles matrix.")
        if not self.n_guides == len(self.parmsIntersGuides[0]):
            raise ValueError("Invalid col size of parmsIntersGuides matrix.")
        # ????
        # assert(m_parmsIntersGuides.UpperRow() == n_profiles - 1);
        # assert(m_parmsIntersProfiles.UpperRow() == n_profiles - 1);
        # assert(m_parmsIntersGuides.UpperCol() == n_guides - 1);
        # assert(m_parmsIntersProfiles.UpperCol() == n_guides - 1);
        self.profIdx = [str(i) for i in range(self.n_profiles)]
        self.guidIdx = [str(i) for i in range(self.n_guides)]

    def swapProfiles(self, idx1, idx2):
        if (idx1 == idx2):
            return
        swap(self.profiles, idx1, idx2)
        swap(self.profIdx, idx1, idx2)
        swap_row(self.parmsIntersGuides, idx1, idx2)
        swap_row(self.parmsIntersProfiles, idx1, idx2)

    def swapGuides(self, idx1, idx2):
        if (idx1 == idx2):
            return
        swap(self.guides, idx1, idx2)
        swap(self.guidIdx, idx1, idx2)
        swap_col(self.parmsIntersGuides, idx1, idx2)
        swap_col(self.parmsIntersProfiles, idx1, idx2)

    def GetStartCurveIndices(self):  # prof_idx, guid_idx, guideMustBeReversed):
        """find curves, that begin at the same point (have the smallest parameter at their intersection)"""
        for irow in range(len(self.profiles)):
            jmin = minRowIndex(self.parmsIntersProfiles, irow)
            imin = minColIndex(self.parmsIntersGuides, jmin)
            if (imin == irow):
                # we found the start curves
                # prof_idx = imin
                # guid_idx = jmin
                # guideMustBeReversed = False
                return imin, jmin, False
        # there are situation (a loop) when the previous situation does not exist
        # find curves were the start of a profile hits the end of a guide
        for irow in range(len(self.profiles)):
            jmin = minRowIndex(self.parmsIntersProfiles, irow)
            imax = maxColIndex(self.parmsIntersGuides, jmin)
            if (imax == irow):
                # we found the start curves
                # prof_idx = imax
                # guid_idx = jmin
                # guideMustBeReversed = True
                return imax, jmin, True
        # we have not found the starting curve. The network seems invalid
        raise RuntimeError("Cannot find starting curves of curve network.")

    def Perform(self):
        if self.has_performed:
            return

        prof_start = 0
        guide_start = 0
        nGuid = len(self.guides)
        nProf = len(self.profiles)

        guideMustBeReversed = False
        prof_start, guide_start, guideMustBeReversed = self.GetStartCurveIndices()

        # put start curves first in array
        self.swapProfiles(0, prof_start)
        self.swapGuides(0, guide_start)

        if guideMustBeReversed:
            self.reverseGuide(0)

        # perform a bubble sort for the guides,
        # such that the guides intersection of the first profile are ascending
        r = list(range(2, nGuid + 1))
        r.reverse()
        for n in r:  # (int n = nGuid; n > 1; n = n - 1) {
            for j in range(1, n - 1):  # (int j = 1; j < n - 1; ++j) {
                if self.parmsIntersProfiles[0][j] > self.parmsIntersProfiles[0][j + 1]:
                    self.swapGuides(j, j + 1)
        # perform a bubble sort of the profiles,
        # such that the profiles are in ascending order of the first guide
        r = list(range(2, nProf + 1))
        r.reverse()
        for n in r:  # (int n = nProf; n > 1; n = n - 1) {
            for i in range(1, n - 1):  # (int i = 1; i < n - 1; ++i) {
                if self.parmsIntersGuides[i][0] > self.parmsIntersGuides[i + 1][0]:
                    self.swapProfiles(i, i + 1)

        # reverse profiles, if necessary
        for iProf in range(1, nProf):  # (Standard_Integer iProf = 1; iProf < nProf; ++iProf) {
            if self.parmsIntersProfiles[iProf][0] > self.parmsIntersProfiles[iProf][nGuid - 1]:
                self.reverseProfile(iProf)
                debug("reversing profile #%d\n" % iProf)
        # reverse guide, if necessary
        for iGuid in range(1, nGuid):  # (Standard_Integer iGuid = 1; iGuid < nGuid; ++iGuid) {
            if self.parmsIntersGuides[0][iGuid] > self.parmsIntersGuides[nProf - 1][iGuid]:
                self.reverseGuide(iGuid)
                debug("reversing guide #%d\n" % iGuid)
        self.has_performed = True

    def reverseProfile(self, profileIdx):
        pIdx = int(profileIdx)
        profile = self.profiles[profileIdx]
        if profile is not None:  # .IsNull()
            firstParm = profile.FirstParameter
            lastParm = profile.LastParameter
        else:
            firstParm = self.parmsIntersProfiles[pIdx][int(minRowIndex(self.parmsIntersProfiles, pIdx))]
            lastParm = self.parmsIntersProfiles[pIdx][int(maxRowIndex(self.parmsIntersProfiles, pIdx))]
        # compute new parameters
        for icol in range(len(self.guides)):  # (int icol = 0; icol < static_cast<int>(NGuides()); ++icol) {
            self.parmsIntersProfiles[pIdx][icol] = -self.parmsIntersProfiles[pIdx][icol] + firstParm + lastParm
        if profile is not None:  # .IsNull()
            profile = nurbs_tools.bspline_copy(profile, reverse=True, scale=1.0)
            self.profiles[profileIdx] = profile
        self.profIdx[profileIdx] = "-" + self.profIdx[profileIdx]

    def reverseGuide(self, guideIdx):
        gIdx = int(guideIdx)
        guide = self.guides[guideIdx]
        if guide is not None:  # .IsNull()
            firstParm = guide.FirstParameter
            lastParm = guide.LastParameter
        else:
            firstParm = self.parmsIntersGuides[int(minColIndex(self.parmsIntersGuides, gIdx))][gIdx]
            lastParm = self.parmsIntersGuides[int(maxColIndex(self.parmsIntersGuides, gIdx))][gIdx]
        # compute new parameters
        for irow in range(len(self.profiles)):
            self.parmsIntersGuides[irow][gIdx] = -self.parmsIntersGuides[irow][gIdx] + firstParm + lastParm
        if guide is not None:  # .IsNull()
            guide = nurbs_tools.bspline_copy(guide, reverse=True, scale=1.0)
            self.guides[guideIdx] = guide
        self.guidIdx[guideIdx] = "-" + self.guidIdx[guideIdx]
