import re
import xarray as xr
import numpy as np
import multiprocessing as mp

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from src.utils import shift_time, smean, amean, mmean, get_dir_path


class get_climo(object):
    def __init__(self,case, **kwargs):
        self.case = case
        self.start = kwargs.get('start', None)
        self.end = kwargs.get('end', None)
        self.path = kwargs.get('path', None)
        self.outpath = kwargs.get('outpath', None)
        self.ts = kwargs.get('ts', None)
        self._var = kwargs.get('variable', None)
        self.mod = kwargs.get('mod', None)
        self.prs = kwargs.get('prs', 1)
        self.tags = kwargs.get('tags', ['ANN'])
        self.numTags = kwargs.get('numTags', ['01-12'])
        
    @property
    def variable(self):
        return self._var

    @variable.setter
    def variable(self, val):
        self._var = [0]
        vars = [x.strip() for x in val.split(',')]
        for zz in range(len(vars)):
            self._var.append(vars[zz])
        self._var.remove(0)
        
    def make_climo(self):
        self.path = get_dir_path(self.path)
        print('\nConsidering files in:',str(self.path))
        fname = self.case+'.'+self.mod+'.h0.*.nc'
        print(fname)
        flist = list(self.path.glob(fname))
        print('Considering files:\n', flist)
        data = xr.open_mfdataset(flist, combine='by_coords')

        # Checkout the simulated years from the filenames
        years = []
        for filename in flist:
            filename = str(filename).split('/')[-1]
            syear = re.search(r"h?\.(\d{4}).*\.nc$", str(filename))
            yr = int(syear.group(1))
            years.append(yr)
            
        actual_years = np.sort(list(set(years)))
        dummy_years = np.sort(np.unique(data['time.year'].values))
        print('\nYears read:', dummy_years)
        print('Actual years:', actual_years)

        # Corrected time dimension
        if len(actual_years) < len(dummy_years):
            print('\nCorrecting the time dimension.')
            corrected_time = shift_time(data.time.values)
            data = data.assign_coords(time=corrected_time)
        data = data.sel(time=slice(str(self.start),str(self.end)))

        if self._var == None:
            print('\nSelected all variables.')
            self._var = []
            varList = list(data.variables.keys())
            for v in varList:
                if ('time' in data[v].dims) and ((data[v].dtype == np.float32) or (data[v].dtype == np.float64)):
                    self._var.append(v)
                else:
                    print('removing',v)
        else:
            print('\nSelected variables: ',self._var)
        ds = data[self._var]
        return ds
    
    def to_nc(self,ind,tag,numTag,data,ts):
        self.outpath = get_dir_path(self.outpath)
        im = numTag.split('-')[0]
        fm = numTag.split('-')[1]
        print('\nSaving climo file:\n', str(self.outpath / str(self.case + '_'+ tag + '_' + str(self.start) + im + '_' + str(self.end) + fm + '_climo.nc')))
        data.isel(time=ind).load().to_netcdf(self.outpath / str(self.case + '_' + tag + '_' + str(self.start) + im + '_'+ str(self.end) + fm + '_climo.nc'))
    
    def apply_means(self):
        data = self.make_climo()
        if self.ts == 'sea':
            print('\nCalculating seasonal means.')
            ds=smean(data)
            ds = ds.rename({'season':'time'})
            self.prs=4
            self.tags = ['DJF','JJA','MAM','SON']
            self.numTags = ['01-12','06-08','03-05','09-11']
        elif self.ts == 'mon':
            print('\nCalculating monthly means.')
            ds=mmean(data)
            ds = ds.rename({'month':'time'})
            self.prs=12
            self.tags=['01','02','03','04','05','06','07','08','09','10','11','12']
            self.numTags = ['01-01','02-02','03-03','04-04','05-05','06-06','07-07','08-08','09-09','10-10','11-11','12-12']
        else:
            print('\nCalculating annual means.')
            ny = int(self.end) - int(self.start) + 1
            ds=amean(data,years = ny)
            ds = ds.rename({'year':'time'})
            data = data.sel(time=slice(str(self.start),str(self.end)))
            self.prs=1
            self.tags=['ANN']
            self.numTags = ['01-12']
        return ds
    
    def get_nc(self):
        ds = self.apply_means()

        processes=[]
        for _,i in zip(range(self.prs),range(self.prs)):
            p = mp.Process(target=self.to_nc,args=[i,self.tags[i],self.numTags[i],ds,self.ts])
            p.start()
            processes.append(p)

        for process in processes:
            process.join()
            
