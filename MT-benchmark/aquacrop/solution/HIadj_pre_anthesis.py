import numpy as np

from numba import njit, f8, i8, b1
from numba.pycc import CC


# temporary name for compiled module
cc = CC("solution_HIadj_pre_anthesis")


@cc.export("HIadj_pre_anthesis", (f8,f8,f8,f8))
def HIadj_pre_anthesis(
    NewCond_B: float,
    NewCond_B_NS: float,
    NewCond_CC: float,
    Crop_dHI_pre: float
    ) -> float:
    """
    Function to calculate adjustment to harvest index for pre-anthesis water
    stress

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=119" target="_blank">Reference Manual: harvest index calculations</a> (pg. 110-126)


    Arguments:

        NewCond_B (float): biomass growth

        NewCond_B_NS (float): biomass growth (no stress)

        NewCond_CC (float): canopy cover

        Crop_dHI_pre (float): Crop_dHI_pre


    Returns:


        NewCond_Fpre (float): adjustment to harvest index for pre-anthesis water stress


    """

    ## Store initial conditions in structure for updating ##
    # NewCond = InitCond

    # check that there is an adjustment to be made
    if Crop_dHI_pre > 0:
        ## Calculate adjustment ##
        # Get parameters
        Br = NewCond_B / NewCond_B_NS
        Br_range = np.log(Crop_dHI_pre) / 5.62
        Br_upp = 1
        Br_low = 1 - Br_range
        Br_top = Br_upp - (Br_range / 3)

        # Get biomass ratios
        ratio_low = (Br - Br_low) / (Br_top - Br_low)
        ratio_upp = (Br - Br_top) / (Br_upp - Br_top)

        # Calculate adjustment factor
        if (Br >= Br_low) and (Br < Br_top):
            NewCond_Fpre = 1 + (
                ((1 + np.sin((1.5 - ratio_low) * np.pi)) / 2) * (Crop_dHI_pre / 100)
            )
        elif (Br > Br_top) and (Br <= Br_upp):
            NewCond_Fpre = 1 + (
                ((1 + np.sin((0.5 + ratio_upp) * np.pi)) / 2) * (Crop_dHI_pre / 100)
            )
        else:
            NewCond_Fpre = 1
    else:
        NewCond_Fpre = 1

    if NewCond_CC <= 0.01:
        # No green canopy cover left at start of flowering so no harvestable
        # crop will develop
        NewCond_Fpre = 0

    return NewCond_Fpre

if __name__ == "__main__":
    cc.compile()
