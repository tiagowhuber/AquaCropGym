import numpy as np

from numba import njit, f8, i8, b1
from numba.pycc import CC


try:
    from ..entities.waterStressCoefficients import KswNT_type_sig
    from ..entities.temperatureStressCoefficients import KstNT_type_sig

except:
    from entities.waterStressCoefficients import KswNT_type_sig
    from entities.temperatureStressCoefficients import KstNT_type_sig

    
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Important: classes are only imported when types are checked, not in production.
    from aquacrop.entities.waterStressCoefficients import KswNT
    from aquacrop.entities.temperatureStressCoefficients import KstNT



# temporary name for compiled module
cc = CC("solution_HIadj_pollination")

@cc.export("HIadj_pollination", (f8,f8,f8,f8,f8,KswNT_type_sig,KstNT_type_sig,f8))
def HIadj_pollination(
    NewCond_CC: float,
    NewCond_Fpol: float,
    Crop_FloweringCD: float, 
    Crop_CCmin: float, 
    Crop_exc: float, 
    Ksw: "KswNT", 
    Kst: "KstNT", 
    HIt: float,
) -> float:
    """
    Function to calculate adjustment to harvest index for failure of
    pollination due to water or temperature stress

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=119" target="_blank">Reference Manual: harvest index calculations</a> (pg. 110-126)


    Arguments:


        NewCond_CC (float): InitCond object containing model paramaters

        NewCond_Fpol (float): InitCond object containing model paramaters

        Crop_FloweringCD (float): Length of flowering stage

        Crop_CCmin (float): minimum canopy cover

        Crop_exc (float): 

        Ksw (KswNT): Ksw object containing water stress paramaters

        Kst (KstNT): Kst object containing tempature stress paramaters

        HIt (float): time for harvest index build-up (calander days)


    Returns:


        NewCond (InitialCondition): InitCond object containing updated model paramaters



    """

    ## Caclulate harvest index adjustment for pollination ##
    # Get fractional flowering
    if HIt == 0:
        # No flowering yet
        FracFlow = 0
    elif HIt > 0:
        # Fractional flowering on previous day
        t1 = HIt - 1
        if t1 == 0:
            F1 = 0
        else:
            t1Pct = 100 * (t1 / Crop_FloweringCD)
            if t1Pct > 100:
                t1Pct = 100

            F1 = 0.00558 * np.exp(0.63 * np.log(t1Pct)) - (0.000969 * t1Pct) - 0.00383

        if F1 < 0:
            F1 = 0

        # Fractional flowering on current day
        t2 = HIt
        if t2 == 0:
            F2 = 0
        else:
            t2Pct = 100 * (t2 / Crop_FloweringCD)
            if t2Pct > 100:
                t2Pct = 100

            F2 = 0.00558 * np.exp(0.63 * np.log(t2Pct)) - (0.000969 * t2Pct) - 0.00383

        if F2 < 0:
            F2 = 0

        # Weight values
        if abs(F1 - F2) < 0.0000001:
            F = 0
        else:
            F = 100 * ((F1 + F2) / 2) / Crop_FloweringCD

        FracFlow = F

    # Calculate pollination adjustment for current day
    if NewCond_CC < Crop_CCmin:
        # No pollination can occur as canopy cover is smaller than minimum
        # threshold
        dFpol = 0
    else:
        Ks = min([Ksw.pol, Kst.PolC, Kst.PolH])
        dFpol = Ks * FracFlow * (1 + (Crop_exc / 100))

    # Calculate pollination adjustment to date
    NewCond_Fpol = NewCond_Fpol + dFpol
    if NewCond_Fpol > 1:
        # Crop has fully pollinated
        NewCond_Fpol = 1

    return NewCond_Fpol

if __name__ == "__main__":
    cc.compile()
