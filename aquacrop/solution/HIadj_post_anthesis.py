import numpy as np

from numba import njit, f8, i8, b1
from numba.pycc import CC

try:
    from ..entities.crop import CropStructNT_type_sig
    from ..entities.waterStressCoefficients import KswNT_type_sig
except:
    from entities.crop import CropStructNT_type_sig
    from entities.waterStressCoefficients import KswNT_type_sig

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    # Important: classes are only imported when types are checked, not in production.
    from aquacrop.entities.crop import CropStructNT
    from entities.waterStressCoefficients import KswNT

# temporary name for compiled module
cc = CC("solution_HIadj_post_anthesis")


@cc.export("HIadj_post_anthesis", (i8,f8,f8,i8,f8,f8,f8,f8,CropStructNT_type_sig,KswNT_type_sig,))
def HIadj_post_anthesis(
    NewCond_DelayedCDs: int,
    NewCond_sCor1: float,
    NewCond_sCor2: float,
    NewCond_DAP: int,
    NewCond_Fpre: float,
    NewCond_CC: float,
    NewCond_fpost_upp: float,
    NewCond_fpost_dwn: float,
    Crop: "CropStructNT", 
    Ksw: "KswNT",
    ) -> Tuple[float, float, float, float, float]:
    """
    Function to calculate adjustment to harvest index for post-anthesis water
    stress

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=119" target="_blank">Reference Manual: harvest index calculations</a> (pg. 110-126)


    Arguments:


        NewCond_DelayedCDs (int): delayed calendar days

        NewCond_sCor1 (float): canopy exapnsion

        NewCond_sCor2 (float): stomatal closure

        NewCond_DAP (int): days since planting

        NewCond_Fpre (float): delayed calendar days

        NewCond_CC (float): current canopy cover

        NewCond_fpost_upp (float): delayed calendar days

        NewCond_fpost_dwn (float): delayed calendar days

        Crop (CropStructNT): Crop paramaters

        Ksw (KswNT): water stress paramaters

    Returns:


        NewCond (InitialCondition): InitCond object containing updated model paramaters


    """

    ## Store initial conditions in a structure for updating ##
    # NewCond = InitCond

    InitCond_DelayedCDs = NewCond_DelayedCDs*1
    InitCond_sCor1 = NewCond_sCor1*1
    InitCond_sCor2 = NewCond_sCor2*1

    ## Calculate harvest index adjustment ##
    # 1. Adjustment for leaf expansion
    tmax1 = Crop.CanopyDevEndCD - Crop.HIstartCD
    dap = NewCond_DAP - InitCond_DelayedCDs
    if (
        (dap <= (Crop.CanopyDevEndCD + 1))
        and (tmax1 > 0)
        and (NewCond_Fpre > 0.99)
        and (NewCond_CC > 0.001)
        and (Crop.a_HI > 0)
    ):
        dCor = 1 + (1 - Ksw.exp) / Crop.a_HI
        NewCond_sCor1 = InitCond_sCor1 + (dCor / tmax1)
        DayCor = dap - 1 - Crop.HIstartCD
        NewCond_fpost_upp = (tmax1 / DayCor) * NewCond_sCor1

    # 2. Adjustment for stomatal closure
    tmax2 = Crop.YldFormCD
    dap = NewCond_DAP - InitCond_DelayedCDs
    if (
        (dap <= (Crop.HIendCD + 1))
        and (tmax2 > 0)
        and (NewCond_Fpre > 0.99)
        and (NewCond_CC > 0.001)
        and (Crop.b_HI > 0)
    ):
        # print(Ksw.sto)
        dCor = np.power(Ksw.sto, 0.1) * (1 - (1 - Ksw.sto) / Crop.b_HI)
        NewCond_sCor2 = InitCond_sCor2 + (dCor / tmax2)
        DayCor = dap - 1 - Crop.HIstartCD
        NewCond_fpost_dwn = (tmax2 / DayCor) * NewCond_sCor2

    # Determine total multiplier
    if (tmax1 == 0) and (tmax2 == 0):
        NewCond_Fpost = 1
    else:
        if tmax2 == 0:
            NewCond_Fpost = NewCond_fpost_upp
        else:
            if tmax1 == 0:
                NewCond_Fpost = NewCond_fpost_dwn
            elif tmax1 <= tmax2:
                NewCond_Fpost = NewCond_fpost_dwn * (
                    ((tmax1 * NewCond_fpost_upp) + (tmax2 - tmax1)) / tmax2
                )
            else:
                NewCond_Fpost = NewCond_fpost_upp * (
                    ((tmax2 * NewCond_fpost_dwn) + (tmax1 - tmax2)) / tmax1
                )

    return (
            NewCond_sCor1,
            NewCond_sCor2,
            NewCond_fpost_upp,
            NewCond_fpost_dwn,
            NewCond_Fpost)

if __name__ == "__main__":
    cc.compile()
