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
    Pre-process EAMxx outputs to EAM: active when using scream.
    """
    tracers = ["Q", "CLDLIQ", "CLDICE", "NUMLIQ", "NUMICE", "RAINQM", "SNOWQM", "NUMRAI", "NUMSNO",
                "O3", "H2O2", "H2SO4", "SO2", "DMS", "SOAG",
                "so4_a1", "pom_a1", "soa_a1", "bc_a1", "dst_a1", "ncl_a1", "mom_a1", "num_a1",
                "so4_a2", "soa_a2", "ncl_a2", "mom_a2", "num_a2",
                "dst_a3", "ncl_a3", "so4_a3", "bc_a3", "pom_a3", "soa_a3", "mom_a3", "num_a3",
                "pom_a4", "bc_a4", "mom_a4", "num_a4"
                ]
    # Handle dims: add time dim and transpose lev dim
    for var in data.data_vars:
        if "lev" in data[var].dims and "ncol" in data[var].dims:
            data[var] = data[var].transpose(..., "lev", "ncol")

    if 'ps' in data.variables:
        data = data.rename({'ps':'PS'})
    if 'landfrac' in data.variables:
        data = data.rename({'landfrac':'LANDFRAC'})
        
    data = data.rename({var: var.replace("nacl", "ncl") for var in data.variables if "nacl" in var})
    
    aer_list = ['bc','so4','dst','mom','pom','ncl','soa','num','DMS','SO2','H2SO4']
    for aer in aer_list:
        for aval, vname in zip(['a','c'],['aerdepwetis','aerdepwetcw']):
            for mode in ['1','2','3','4']:
                try:
                    var_name = aer + '_' + aval + mode + 'SFWET'
                    new_var = data[vname][..., tracers.index(aer+'_a' + mode)]
                    data = data.assign({var_name: new_var})
                except:
                    pass
        
        for aval, vname in zip(['a','c'],['deposition_flux_of_interstitial_aerosols','deposition_flux_of_cloud_borne_aerosols']):
            for mode in ['1','2','3','4']:
                try:
                    var_name = aer + '_' + aval + mode + 'DDF'
                    new_var = data[vname][..., tracers.index(aer+'_a' + mode)]
                    data = data.assign({var_name: new_var})
                except:
                    pass
        
        for aval, vname in zip(['a'],['constituent_fluxes']):
            for mode in ['1','2','3','4']:
                try:
                    var_name = 'SF' + aer + '_' + aval + mode
                    new_var = data[vname][..., tracers.index(aer+'_a' + mode)]
                    data = data.assign({var_name: new_var})
                except:
                    pass
        
    # dry and wet size, aerosol water
    for vname, item in zip(['dgnum','dgnumwet','qaerwat'],['dgnd_a0','dgnw_a0','wat_a']):
        if vname not in data:
            print(f"Warning: Variable '{vname}' not found in dataset. Skipping...")
            continue
    
        for mode in ['1','2','3','4']:
            var_name = item + mode
            new_var = data[vname].isel({ "nmodes": int(mode)-1 })
            data = data.assign({var_name: new_var})
            
    # aci diagnostics
    ccn_vars = ["ccn_0p02", "ccn_0p05", "ccn_0p1", "ccn_0p2", "ccn_0p5", "ccn_1p0"]
    for i, vname in enumerate(ccn_vars):
        if vname not in data:
            print(f"Warning: Variable '{vname}' not found in dataset. Skipping...")
            continue
        
        var_name = 'CCN' + str(i+1)
        new_var = data[vname]
        data = data.assign({var_name: new_var})
    
    # optical properties
    optics_vars = ['aero_tau_sw', 'aero_ssa_sw']
    missing_vars = [var for var in optics_vars if var not in data]
    
    if missing_vars:
        print(f"Warning: Missing variables {missing_vars}. Skipping assignment.")
    else:
        data = data.assign(
        AODVIS=data['aero_tau_sw'].isel(swband=10).sum(dim='lev'),
        SSAVIS=data['aero_ssa_sw'].isel(swband=10).sum(dim='lev'),
        AODABS=lambda ds: (ds['aero_tau_sw'].isel(swband=10) - 
                            (ds['aero_tau_sw'].isel(swband=10) * ds['aero_ssa_sw'].isel(swband=10))
                          ).sum(dim='lev')
        )
            
    data = data.rename(
            {var: var.replace("_PG2", "") for var in data.variables if "_PG2" in var}
        )

    return data
