import numpy as np

    
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    # Important: classes are only imported when types are checked, not in production.
    from aquacrop.entities.soilProfile import SoilProfileNT
    from aquacrop.entities.crop import CropStructNT
    from aquacrop.entities.initParamVariables import InitialCondition
    from aquacrop.entities.irrigationManagement import IrrMngtStruct


def pre_irrigation(
    prof: "SoilProfileNT",
    Crop: "CropStructNT",
    InitCond: "InitialCondition",
    growing_season: bool,
    IrrMngt: "IrrMngtStruct",
    ) -> Tuple["InitialCondition", float]:
    """
    Function to calculate pre-irrigation when in net irrigation mode

    <a href="https://www.fao.org/3/BR246E/br246e.pdf#page=40" target="_blank">Reference Manual: Net irrigation description</a> (pg. 31)


    Arguments:

        prof (SoilProfile): Soil object containing soil paramaters

        Crop (CropStruct): Crop object containing Crop paramaters

        InitCond (InitialCondition): InitCond object containing model paramaters

        growing_season (bool): is growing season (True or Flase)

        IrrMngt (IrrMngtStruct): object containing irrigation management paramaters



    Returns:

        NewCond (InitialCondition): InitCond object containing updated model paramaters

        PreIrr (float): Pre-Irrigaiton applied on current day mm




    """
    # Store initial conditions for updating ##
    NewCond = InitCond

    ## Calculate pre-irrigation needs ##
    if growing_season == True:
        if (IrrMngt.irrigation_method != 4) or (NewCond.dap != 1):
            # No pre-irrigation as not in net irrigation mode or not on first day
            # of the growing season
            PreIrr = 0
        else:
            # Determine compartments covered by the root zone
            rootdepth = round(max(NewCond.z_root, Crop.Zmin), 2)

            compRz = np.argwhere(prof.dzsum >= rootdepth).flatten()[0]

            PreIrr = 0
            for ii in range(int(compRz)):

                # Determine critical water content threshold
                thCrit = prof.th_wp[ii] + (
                    (IrrMngt.NetIrrSMT / 100) * (prof.th_fc[ii] - prof.th_wp[ii])
                )

                # Check if pre-irrigation is required
                if NewCond.th[ii] < thCrit:
                    PreIrr = PreIrr + ((thCrit - NewCond.th[ii]) * 1000 * prof.dz[ii])
                    NewCond.th[ii] = thCrit

    else:
        PreIrr = 0

    return NewCond, PreIrr

