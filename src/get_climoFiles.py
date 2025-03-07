import re
import xarray as xr
import numpy as np
import multiprocessing as mp
import warnings

from pathlib import Path
from src.utils import shift_time, smean, amean, mmean, get_dir_path, prep_mamxx

warnings.simplefilter(action="ignore", category=FutureWarning)


class GetClimo:
    def __init__(self, case, **kwargs):
        self.case = case
        self.start = kwargs.get("start", None)
        self.end = kwargs.get("end", None)
        self.path = kwargs.get("path", None)
        self.outpath = kwargs.get("outpath", None)
        self.ts = kwargs.get("ts", None)
        self._var = kwargs.get("variable", None)
        self.mod = kwargs.get("mod", None)
        self.prs = kwargs.get("prs", 1)
        self.tags = kwargs.get("tags", ["ANN"])
        self.numTags = kwargs.get("numTags", ["01-12"])

    @property
    def variable(self):
        return self._var

    @variable.setter
    def variable(self, val):
        self._var = []
        vars_list = [x.strip() for x in val.split(",")]
        self._var.extend(vars_list)

    def make_climo(self):
        self.path = get_dir_path(self.path)
        print("\nConsidering files in:", str(self.path))

        fname = f"{self.case}.{self.mod}.h0.*.nc"
        print(fname)

        flist = sorted(list(Path(self.path).glob(fname)))
        print("Considering files:\n", flist)

        data = xr.open_mfdataset(flist, combine="by_coords")
        
        if self.mod == 'scream':
            data = prep_mamxx(data)

        # Extract the simulated years from filenames
        years = []
        for filename in flist:
            filename = str(filename).split("/")[-1]
            match = re.search(r"h?\.(\d{4}).*\.nc$", filename)
            if match:
                years.append(int(match.group(1)))

        actual_years = np.sort(list(set(years)))
        dummy_years = np.sort(np.unique(data["time.year"].values))

        print("\nYears read:", dummy_years)
        print("Actual years:", actual_years)

        # Correct the time dimension if needed
        if len(actual_years) < len(dummy_years):
            print("\nCorrecting the time dimension.")
            corrected_time = shift_time(data.time.values)
            data = data.assign_coords(time=corrected_time)

        data = data.sel(time=slice(str(self.start), str(self.end)))

        if self._var is None:
            print("\nSelected all variables.")
            self._var = []
            var_list = list(data.variables.keys())

            for var in var_list:
                if "time" in data[var].dims and data[var].dtype in [np.float32, np.float64]:
                    self._var.append(var)
                else:
                    print("Removing", var)
        else:
            print("\nSelected variables: ", self._var)

        return data[self._var]

    def to_nc(self, ind, tag, num_tag, data, ts):
        self.outpath = get_dir_path(self.outpath)

        im, fm = num_tag.split("-")
        filename = f"{self.case}_{tag}_{self.start}{im}_{self.end}{fm}_climo.nc"
        filepath = self.outpath / filename

        print("\nSaving climo file:\n", str(filepath))
        data.isel(time=ind).load().to_netcdf(filepath)

    def apply_means(self):
        data = self.make_climo()

        if self.ts == "sea":
            print("\nCalculating seasonal means.")
            ds = smean(data)
            ds = ds.rename({"season": "time"})
            self.prs = 4
            self.tags = ["DJF", "JJA", "MAM", "SON"]
            self.numTags = ["01-12", "06-08", "03-05", "09-11"]

        elif self.ts == "mon":
            print("\nCalculating monthly means.")
            ds = mmean(data)
            ds = ds.rename({"month": "time"})
            self.prs = 12
            self.tags = [f"{i:02d}" for i in range(1, 13)]
            self.numTags = [f"{i:02d}-{i:02d}" for i in range(1, 13)]

        else:
            print("\nCalculating annual means.")
            ny = int(self.end) - int(self.start) + 1
            ds = amean(data, years=ny)
            ds = ds.rename({"year": "time"})
            self.prs = 1
            self.tags = ["ANN"]
            self.numTags = ["01-12"]

        return ds

    def get_nc(self):
        ds = self.apply_means()
        processes = []

        for i in range(self.prs):
            p = mp.Process(target=self.to_nc, args=(i, self.tags[i], self.numTags[i], ds, self.ts))
            p.start()
            processes.append(p)

        for process in processes:
            process.join()
