import cftime
from datetime import datetime
import xarray as xr
import numpy as np
from pathlib import Path

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
    attrs = {
            'comment':'This data was generated using the genclimo tool.',
            'Git repo':'https://github.com/TaufiqHassan/genclimo',
            'contact for genclimo':'Taufiq Hassan (taufiq.hassan@pnnl.gov)',
            'creation_date':datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            }
    global_attrs = attrs
    var_attrs = {var: data_in[var].attrs.copy() for var in data_in.data_vars} if isinstance(data_in, xr.Dataset) else {data_in.name: data_in.attrs.copy()}
    # Restore attributes
    data_out.attrs = global_attrs  # Restore global attributes
    if isinstance(data_out, xr.Dataset):
        for var in data_out.data_vars:
            data_out[var].attrs = var_attrs.get(var, {})
    elif isinstance(data_out, xr.DataArray) and data_in.name:
        data_out.attrs = var_attrs.get(data_in.name, {})
    return data_out

def smean(data):
    month_length = data.time.dt.days_in_month
    weights = (month_length.groupby("time.season") / month_length.groupby("time.season").sum())
    np.testing.assert_allclose(weights.groupby("time.season").sum().values, np.ones(4))
    seasons = (data * weights).groupby("time.season").sum(dim="time")
    seasons = retain_attr(data, seasons)
    return seasons

def amean(data,years):
    month_length = data.time.dt.days_in_month
    weights = (month_length.groupby("time.year") / month_length.groupby("time.year").sum())
    np.testing.assert_allclose(weights.groupby("time.year").sum().values, np.ones(years))
    ann = (data * weights).groupby("time.year").sum(dim="time")
    ann = retain_attr(data, ann)
    return ann

def mmean(data):
    month_length = data.time.dt.days_in_month
    weights = (month_length.groupby("time.month") / month_length.groupby("time.month").sum())
    np.testing.assert_allclose(weights.groupby("time.month").sum().values, np.ones(12))
    mon = (data * weights).groupby("time.month").sum(dim="time")
    mon = retain_attr(data, mon)
    return mon

def get_dir_path(path):
    if (path == ''):
        p=Path('.')
        dir_path = p.absolute()
    else:
        dir_path = Path(path)
    return dir_path