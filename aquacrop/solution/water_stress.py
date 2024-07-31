import numpy as np

from numba import njit, f8, i8, b1
from numba.pycc import CC


from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    # Important: classes are only imported when types are checked, not in production.
    from numpy import ndarray


# temporary name for compiled module
cc = CC("solution_water_stress")

@njit
@cc.export("water_stress", "(f8[:],f8[:],f8,f8,f8[:],f8,f8,f8,f8,f8)")
def water_stress(
    Crop_p_up: "ndarray",
    Crop_p_lo: "ndarray",
    Crop_ETadj: float,
    Crop_beta: float,
    Crop_fshape_w: "ndarray",
    InitCond_tEarlySen: float,
    Dr: float,
    taw: float,
    et0: float,
    beta: float,
) -> Tuple[float, float, float, float, float]:
    """
    Function to calculate water stress coefficients

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=18" target="_blank">Reference Manual: water stress equations</a> (pg. 9-13)


    Arguments:


        Crop_p_up (ndarray): water stress thresholds for start of water stress

        Crop_p_lo (ndarray): water stress thresholds for maximum water stress

        Crop_ETadj (float): 

        Crop_beta (float): 

        Crop_fshape_w (ndarray): shape factors for water stress

        InitCond_tEarlySen (float): days in early senesence

        Dr (Dr): rootzone depletion

        taw (TAW): root zone total available water

        et0 (float): Reference Evapotranspiration

        beta (float): Adjust senescence threshold if early sensescence is triggered


    Returns:

        Ksw (Ksw): Ksw object containint water stress coefficients


    """

    ## Calculate relative root zone water depletion for each stress type ##
    # Number of stress variables
    nstress = len(Crop_p_up)

    # Store stress thresholds
    p_up = np.ones(nstress) * Crop_p_up
    p_lo = np.ones(nstress) * Crop_p_lo
    if Crop_ETadj == 1:
        # Adjust stress thresholds for et0 on currentbeta day (don't do this for
        # pollination water stress coefficient)

        for ii in range(3):
            p_up[ii] = p_up[ii] + (0.04 * (5 - et0)) * (np.log10(10 - 9 * p_up[ii]))
            p_lo[ii] = p_lo[ii] + (0.04 * (5 - et0)) * (np.log10(10 - 9 * p_lo[ii]))

    # Adjust senescence threshold if early sensescence is triggered
    if (beta == True) and (InitCond_tEarlySen > 0):
        p_up[2] = p_up[2] * (1 - Crop_beta / 100)

    # Limit values
    p_up = np.maximum(p_up, np.zeros(4))
    p_lo = np.maximum(p_lo, np.zeros(4))
    p_up = np.minimum(p_up, np.ones(4))
    p_lo = np.minimum(p_lo, np.ones(4))

    # Calculate relative depletion
    Drel = np.zeros(nstress)
    for ii in range(nstress):
        if Dr <= (p_up[ii] * taw):
            # No water stress
            Drel[ii] = 0
        elif (Dr > (p_up[ii] * taw)) and (Dr < (p_lo[ii] * taw)):
            # Partial water stress
            Drel[ii] = 1 - ((p_lo[ii] - (Dr / taw)) / (p_lo[ii] - p_up[ii]))
        elif Dr >= (p_lo[ii] * taw):
            # Full water stress
            Drel[ii] = 1

    ## Calculate root zone water stress coefficients ##
    Ks = np.ones(3)
    for ii in range(3):
        Ks[ii] = 1 - ((np.exp(Drel[ii] * Crop_fshape_w[ii]) - 1) / (np.exp(Crop_fshape_w[ii]) - 1))

    # Ksw = Ksw()

    # Water stress coefficient for leaf expansion
    Ksw_Exp = Ks[0]
    # Water stress coefficient for stomatal closure
    Ksw_Sto = Ks[1]
    # Water stress coefficient for senescence
    Ksw_Sen = Ks[2]
    # Water stress coefficient for pollination failure
    Ksw_Pol = 1 - Drel[3]
    # Mean water stress coefficient for stomatal closure
    Ksw_StoLin = 1 - Drel[1]

    return Ksw_Exp, Ksw_Sto, Ksw_Sen, Ksw_Pol, Ksw_StoLin

if __name__ == "__main__":
    cc.compile()
