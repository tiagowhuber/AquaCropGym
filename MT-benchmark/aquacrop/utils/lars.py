
import sys

_ = [sys.path.append(i) for i in [".", ".."]]


import numpy as np
import pandas as pd
from ..core import *


def prepare_lars_weather(
    file,
    year,
    generated=True,
    order=["year", "jday", "minTemp", "maxTemp", "precip", "rad"],
    wind_speed=3.4,
):
    """
    Uses FAO-PM to calculate reference evapotranspiration for LARS generated and baseline input data.

    """

    def vap_pres(t):
        return 0.6108 * np.exp((17.27 * t) / (t + 237.3))

    df = pd.read_csv(file, delim_whitespace=True, header=None)

    if generated:
        df.columns = order
        df["tdelta"] = pd.to_timedelta(df.jday, unit="D")
        df["date"] = pd.to_datetime(f"{year-1}/12/31") + df["tdelta"]

        psyc = 0.054  # sychometric constant
        tmean = (df.maxTemp + df.minTemp) / 2
        e_s = (vap_pres(df.maxTemp) + vap_pres(df.minTemp)) / 2
        e_a = vap_pres(df.minTemp)
        slope = 4098 * vap_pres(tmean) / (tmean + 237.3) ** 2
        R_ns = (1 - 0.23) * df.rad
        sb_const = 4.903e-9
        R_nl = (
            sb_const
            * 0.5
            * ((df.maxTemp + 273.15) ** 4 + (df.minTemp + 273.15) ** 4)
            * (0.34 - 0.14 * (e_a) ** 0.5)
            * (1.35 * 0.77 - 0.35)
        )
        Rn = R_ns - R_nl
        u2 = wind_speed

        eto = 0.408 * slope * Rn + (psyc * 900 * u2 * (e_s - e_a) / (tmean + 273)) / (
            slope + psyc * (1 + 0.34 * u2)
        )
        df["eto"] = eto

        # df["eto"] = df.rad*(0.0023)*(((df.maxTemp+df.minTemp)/2)+17.8)*(df.maxTemp-df.minTemp)**0.5
        df.eto = df.eto.clip(0.1)
        df = df[["simyear", "minTemp", "maxTemp", "precip", "eto", "date"]]
        df.columns = ["simyear", "MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]

    else:
        df.columns = order
        df["date"] = pd.to_datetime(df.year, format="%Y") + pd.to_timedelta(df.jday - 1, unit="d")

        psyc = 0.054  # sychometric constant
        tmean = (df.maxTemp + df.minTemp) / 2
        e_s = (vap_pres(df.maxTemp) + vap_pres(df.minTemp)) / 2
        e_a = vap_pres(df.minTemp)
        slope = 4098 * vap_pres(tmean) / (tmean + 237.3) ** 2
        R_ns = (1 - 0.23) * df.rad
        sb_const = 4.903e-9
        R_nl = (
            sb_const
            * 0.5
            * ((df.maxTemp + 273.15) ** 4 + (df.minTemp + 273.15) ** 4)
            * (0.34 - 0.14 * (e_a) ** 0.5)
            * (1.35 * 0.77 - 0.35)
        )
        Rn = R_ns - R_nl
        u2 = wind_speed

        eto = 0.408 * slope * Rn + (psyc * 900 * u2 * (e_s - e_a) / (tmean + 273)) / (
            slope + psyc * (1 + 0.34 * u2)
        )
        df["eto"] = eto

        # df["eto"] = df.rad*(0.0023)*(((df.maxTemp+df.minTemp)/2)+17.8)*(df.maxTemp-df.minTemp)**0.5
        df.eto = df.eto.clip(0.1)
        df = df[["minTemp", "maxTemp", "precip", "eto", "date"]]
        df.columns = ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]

    return df



def select_lars_wdf(df, simyear):
    temp = df[df.simyear == simyear][["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]]
    return temp.reset_index(drop=True)
