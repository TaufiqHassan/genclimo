import xarray as xr
from cftime import DatetimeNoLeap
from itertools import product
import numpy as np
from pathlib import Path
import multiprocessing as mp

def smean(data):
    month_length = data.time.dt.days_in_month
    weights = (month_length.groupby("time.season") / month_length.groupby("time.season").sum())
    np.testing.assert_allclose(weights.groupby("time.season").sum().values, np.ones(4))
    seasons = (data * weights).groupby("time.season").sum(dim="time")
    return seasons

def amean(data,years):
    month_length = data.time.dt.days_in_month
    weights = (month_length.groupby("time.year") / month_length.groupby("time.year").sum())
    np.testing.assert_allclose(weights.groupby("time.year").sum().values, np.ones(years))
    ann = (data * weights).groupby("time.year").sum(dim="time")
    return ann

def mmean(data):
    month_length = data.time.dt.days_in_month
    weights = (month_length.groupby("time.month") / month_length.groupby("time.month").sum())
    np.testing.assert_allclose(weights.groupby("time.month").sum().values, np.ones(12))
    mon = (data * weights).groupby("time.month").sum(dim="time")
    return mon

class get_climo(object):
    def __init__(self,case, **kwargs):
        self.case = case
        self.start = kwargs.get('start', None)
        self.end = kwargs.get('end', None)
        self.path = kwargs.get('path', None)
        self.path2 = kwargs.get('path2', None)
        self.ts = kwargs.get('ts', None)
        self._var = kwargs.get('variable', None)
        self.mod = kwargs.get('mod', None)
        
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
        if self.path == None:
            self.path = Path('.').absolute()
        fname = self.case+'.'+self.mod+'.h0.*.nc'
        flist = list(self.path.glob(fname))
        print('Considering files:\n', flist)
        data = xr.open_mfdataset(flist, combine='by_coords')
        if len(data.time)%12 != 0:
            data = data.sel(time=slice(str(self.start),str(self.end)))
        ## Fixing the time dimension
        years = np.sort(np.unique(data['time.year'].values))
        print(years)
        if (len(data.time)>=12) and (len(years)>(len(data.time)/12)):
            years=years[:-1]
        months = np.sort(np.unique(data['time.month'].values))
        dates=[DatetimeNoLeap(year,month,1) 
               for year, month in product(years, months)]
        data['time']=dates
        ## Getting the valid variables for climo files
        if self._var == None:
            self._var = []
            vars = list(data.variables.keys())
            for v in vars:
                try:
                    if ('time' in data[v].dims):
                        self._var.append(v)
                    else:
                        print('removing',v)
                except:
                    print('removing',v)
                    pass
            self._var.remove('time')
            self._var.remove('date_written')
            self._var.remove('time_written')
        print('Selected variables: ',self._var)
        ds = data[self._var]
        return ds
    
    def to_nc(self,ind,tag,data,ts):
        if ts=='sea':
            data.isel(season=ind).load().to_netcdf(str(self.path2)+'/'+self.case+'.'+self.mod+'.'+tag+'.'+str(self.start)+'_climo.nc')
        elif ts=='mon':
            data.isel(month=ind).load().to_netcdf(str(self.path2)+'/'+self.case+'.'+self.mod+'.'+tag+'.'+str(self.start)+'_climo.nc')
        else:
            data.isel(year=0).load().to_netcdf(str(self.path2)+'/'+self.case+'.'+self.mod+'.'+tag+'.'+str(self.start)+'_climo.nc')
    
    def get_nc(self):
        data=self.make_climo()
        if self.ts == 'sea':
            ds=smean(data)
            prs=4
            tags = ['DJF','JJA','MAM','SON']
        elif self.ts == 'mon':
            ds=mmean(data)
            prs=12
            tags=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
        else:
            ny = int(self.end) - int(self.start) + 1
            ds=amean(data,years=ny)
            prs=1
            tags=['ANN']

        processes=[]
        for _,i in zip(range(prs),range(prs)):
            p = mp.Process(target=self.to_nc,args=[i,tags[i],ds,self.ts])
            p.start()
            processes.append(p)

        for process in processes:
            process.join()
            

