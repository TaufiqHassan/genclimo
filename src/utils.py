import cftime
from datetime import datetime
import xarray as xr
import numpy as np
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT


def shift_time(time_array):
    """
    Shift each timestamp in the given time array one month earlier.
    """
    return [
        cftime.DatetimeNoLeap(
            t.year - (t.month == 1),
            12 if t.month == 1 else t.month - 1,
            t.day,
            t.hour,
            t.minute,
            t.second
        )
        for t in time_array
    ]


def retain_attr(data_in, data_out):
    """
    Retain the attributes of the input dataset or data array in the output dataset.
    """
    attrs = {
        "comment": "This data was generated using the genclimo tool.",
        "Git repo": "https://github.com/TaufiqHassan/genclimo",
        "contact for genclimo": "Taufiq Hassan (taufiq.hassan@pnnl.gov)",
        "creation_date": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
    }

    global_attrs = attrs
    var_attrs = (
        {var: data_in[var].attrs.copy() for var in data_in.data_vars}
        if isinstance(data_in, xr.Dataset)
        else {data_in.name: data_in.attrs.copy()}
    )

    # Restore attributes
    data_out.attrs = global_attrs

    if isinstance(data_out, xr.Dataset):
        for var in data_out.data_vars:
            data_out[var].attrs = var_attrs.get(var, {})
    elif isinstance(data_out, xr.DataArray) and data_in.name:
        data_out.attrs = var_attrs.get(data_in.name, {})

    return data_out


def smean(data):
    """
    Compute seasonal mean weighted by the number of days in each month.
    """
    month_length = data.time.dt.days_in_month
    weights = month_length.groupby("time.season") / month_length.groupby("time.season").sum()

    np.testing.assert_allclose(weights.groupby("time.season").sum().values, np.ones(4))

    seasons = (data * weights).groupby("time.season").sum(dim="time")
    return retain_attr(data, seasons)


def amean(data, years):
    """
    Compute annual mean weighted by the number of days in each month.
    """
    month_length = data.time.dt.days_in_month
    weights = month_length.groupby("time.year") / month_length.groupby("time.year").sum()

    np.testing.assert_allclose(weights.groupby("time.year").sum().values, np.ones(years))

    ann = (data * weights).groupby("time.year").sum(dim="time")
    return retain_attr(data, ann)


def mmean(data):
    """
    Compute monthly mean weighted by the number of days in each month.
    """
    month_length = data.time.dt.days_in_month
    weights = month_length.groupby("time.month") / month_length.groupby("time.month").sum()

    np.testing.assert_allclose(weights.groupby("time.month").sum().values, np.ones(12))

    mon = (data * weights).groupby("time.month").sum(dim="time")
    return retain_attr(data, mon)


def get_dir_path(path):
    """
    Get the absolute directory path.
    """
    return Path(".").absolute() if path == "" else Path(path)

def exec_shell(cmd):
    """
    Execute a shell command and return the output.
    """
    cmd_split = cmd.split(" ")
    process = Popen(cmd_split, stdout=PIPE, stdin=PIPE, stderr=STDOUT, universal_newlines=True)
    output, _ = process.communicate()
    return output