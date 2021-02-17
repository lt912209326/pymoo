import os
import warnings

import numpy as np

from pymoo.model.indicator import Indicator
from pymoo.performance_indicator.distance_indicator import derive_ideal_and_nadir_from_pf
from pymoo.util.misc import at_least_2d_array
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from pymoo.vendor.hv import HyperVolume as _HyperVolume


def hypervolume_by_command(path_to_hv, X, ref_point):
    """
    A method to manually call the Hypervolume calculation if it is installed.
    http://lopez-ibanez.eu/hypervolume


    Parameters
    ----------
    path_to_hv : Path to the compiled executable
    X : Points to calculate the Hypervolume
    ref_point : Reference Point

    """

    ref_point_as_str = " ".join(format(x, ".3f") for x in ref_point)

    current_folder = os.path.dirname(os.path.abspath(__file__))

    path_to_input = os.path.join(current_folder, "in.dat")
    np.savetxt(path_to_input, X)

    path_to_output = os.path.join(current_folder, "out.dat")

    command = "%s -r \"%s\" %s > %s" % (path_to_hv, ref_point_as_str, path_to_input, path_to_output)
    # print(command)
    os.system(command)

    with open(path_to_output, 'r') as f:
        val = f.read()

    os.remove(path_to_input)
    os.remove(path_to_output)

    try:
        hv = float(val)
    except:
        warnings.warn(val)
        return - np.inf

    return hv


class Hypervolume(Indicator):

    def __init__(self, ref_point=None, pf=None, nds=True, norm_ref_point=True, ideal=None, nadir=None, **kwargs):
        pf = at_least_2d_array(pf, extend_as="row")
        ideal, nadir = derive_ideal_and_nadir_from_pf(pf, ideal=ideal, nadir=nadir)

        super().__init__(ideal=ideal, nadir=nadir, **kwargs)

        # whether the input should be checked for domination or not
        self.nds = nds

        # the reference point that shall be used - either derived from pf or provided
        ref_point = ref_point
        if ref_point is None:
            if pf is not None:
                ref_point = pf.max(axis=0)

        # we also have to normalize the reference point to have the same scales
        if norm_ref_point:
            ref_point = self.normalization.forward(ref_point)

        self.ref_point = ref_point
        assert self.ref_point is not None, "For Hypervolume a reference point needs to be provided!"

    def _do(self, F):
        if self.nds:
            non_dom = NonDominatedSorting().do(F, only_non_dominated_front=True)
            F = np.copy(F[non_dom, :])

        # calculate the hypervolume using a vendor library
        hv = _HyperVolume(self.ref_point)
        val = hv.compute(F)
        return val
