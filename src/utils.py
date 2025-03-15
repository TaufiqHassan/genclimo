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
    seasons['lev'] = data.lev[0].values
    return retain_attr(data, seasons)


def amean(data, years):
    """
    Compute annual mean weighted by the number of days in each month.
    """
    month_length = data.time.dt.days_in_month
    weights = month_length.groupby("time.year") / month_length.groupby("time.year").sum()

    np.testing.assert_allclose(weights.groupby("time.year").sum().values, np.ones(years))

    ann = (data * weights).groupby("time.year").sum(dim="time")
    ann['lev'] = data.lev[0].values
    return retain_attr(data, ann)


def mmean(data):
    """
    Compute monthly mean weighted by the number of days in each month.
    """
    month_length = data.time.dt.days_in_month
    weights = month_length.groupby("time.month") / month_length.groupby("time.month").sum()

    np.testing.assert_allclose(weights.groupby("time.month").sum().values, np.ones(12))

    mon = (data * weights).groupby("time.month").sum(dim="time")
    mon['lev'] = data.lev[0].values
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

def prep_mamxx(data):
    """
    Pre-process EAMxx outputs to EAM: active when using SCREAM.
    """
    tracers = [
        "Q", "CLDLIQ", "CLDICE", "NUMLIQ", "NUMICE", "RAINQM", "SNOWQM",
        "NUMRAI", "NUMSNO", "O3", "H2O2", "H2SO4", "SO2", "DMS", "SOAG",
        "so4_a1", "pom_a1", "soa_a1", "bc_a1", "dst_a1", "ncl_a1", "mom_a1", "num_a1",
        "so4_a2", "soa_a2", "ncl_a2", "mom_a2", "num_a2",
        "dst_a3", "ncl_a3", "so4_a3", "bc_a3", "pom_a3", "soa_a3", "mom_a3", "num_a3",
        "pom_a4", "bc_a4", "mom_a4", "num_a4"
    ]

    # Define default chunk sizes (adjustable based on dataset size)
    default_chunks = {
        "lev": -1,
        "ncol": -1,
        "lat": -1,
        "lon": -1,
    }

    # Only apply chunking to existing dimensions
    chunk_dims = {dim: default_chunks[dim] for dim in default_chunks if dim in data.dims}
    data = data.chunk(chunk_dims)

    # Get available spatial dimensions
    spatial_dims = [dim for dim in ["ncol", "lat", "lon"] if dim in data.dims]

    # Transpose only existing dimensions
    if "lev" in data.dims:
        data = data.transpose(..., "lev", *spatial_dims)

    # Rename variables
    rename_dict = {var: var.replace("nacl", "ncl") for var in data.variables if "nacl" in var}
    if 'ps' in data.variables:
        rename_dict.update({'ps': 'PS'})
    if 'landfrac' in data.variables:
        rename_dict.update({'landfrac':'LANDFRAC'})
    data = data.rename(rename_dict)

    aer_list = ['bc', 'so4', 'dst', 'mom', 'pom', 'ncl', 'soa', 'num', 'DMS', 'SO2', 'H2SO4']
    new_vars = {}

    # Aerosol processing
    for aer in aer_list:
        for aval, vname in zip(['a', 'c'], ['aerdepwetis', 'aerdepwetcw']):
            for mode in ['1', '2', '3', '4']:
                var_name = f"{aer}_{aval}{mode}SFWET"
                if vname in data and f"{aer}_a{mode}" in tracers:
                    new_vars[var_name] = data[vname].isel(
                        num_phys_constants=tracers.index(f"{aer}_a{mode}")
                    )

        for aval, vname in zip(['a', 'c'], [
            'deposition_flux_of_interstitial_aerosols',
            'deposition_flux_of_cloud_borne_aerosols'
        ]):
            for mode in ['1', '2', '3', '4']:
                var_name = f"{aer}_{aval}{mode}DDF"
                if vname in data and f"{aer}_a{mode}" in tracers:
                    new_vars[var_name] = data[vname].isel(
                        num_phys_constants=tracers.index(f"{aer}_a{mode}")
                    )

        for aval, vname in zip(['a'], ['constituent_fluxes']):
            for mode in ['1', '2', '3', '4']:
                var_name = f"SF{aer}_{aval}{mode}"
                if vname in data and f"{aer}_a{mode}" in tracers:
                    new_vars[var_name] = data[vname].isel(
                        num_phys_constituents=tracers.index(f"{aer}_a{mode}")
                    )

    # Dry and wet size, aerosol water
    size_vars = {'dgnum': 'dgnd_a0', 'dgnumwet': 'dgnw_a0', 'qaerwat': 'wat_a'}
    for vname, item in size_vars.items():
        if vname in data:
            for mode in ['1', '2', '3', '4']:
                var_name = f"{item}{mode}"
                new_vars[var_name] = data[vname].isel(nmodes=int(mode) - 1)

    # ACI diagnostics
    ccn_vars = ["ccn_0p02", "ccn_0p05", "ccn_0p1", "ccn_0p2", "ccn_0p5", "ccn_1p0"]
    for i, vname in enumerate(ccn_vars):
        if vname in data:
            new_vars[f'CCN{i+1}'] = data[vname]

    # Optical properties
    if {'aero_tau_sw', 'aero_ssa_sw'}.issubset(data.variables):
        new_vars.update({
            "AODVIS": data['aero_tau_sw'].isel(swband=10).sum(dim='lev'),
            "SSAVIS": data['aero_ssa_sw'].isel(swband=10).sum(dim='lev'),
            "AODABS": (
                data['aero_tau_sw'].isel(swband=10) * (1 - data['aero_ssa_sw'].isel(swband=10))
            ).sum(dim='lev'),
        })

    # Assigning all converted variables
    data.update(new_vars)

    # Rename PG2 variables
    rename_pg2 = {var: var.replace("_PG2", "") for var in data.variables if "_PG2" in var}
    data = data.rename(rename_pg2)

    return data