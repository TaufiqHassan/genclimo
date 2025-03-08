## genclimo
Generate annual / seasonal / monthly climo files for diagnostics

Usage
------

`python genclimo.py -h`


```bash
usage: genclimo.py [-h] -c CASE -s START [-e END] [-indir INPUT_DIR] [-outdir OUTPUT_DIR] [-m MODEL] [-v VARIABLE] [-t TIME_FREQ]

Process climate data.

options:
  -h, --help            show this help message and exit
  -c CASE, --case CASE  Case name
  -s START, --start START
                        Start year
  -e END, --end END     End year
  -indir INPUT_DIR, --input_dir INPUT_DIR
                        Input directory
  -outdir OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Climo output directory
  -m MODEL, --model MODEL
                        Model name (eam or cam)
  -v VARIABLE, --variable VARIABLE
                        Variable names
  -t TIME_FREQ, --time_freq TIME_FREQ
                        Time frequency (sea=seasonal | mon=monthly)
```

Installation
-------------

Simply clone the repo -
`git clone git@github.com:TaufiqHassan/genclimo.git`

Examples
--------

`genclimo` works with e3sm_unifed environment in Compy and Perlmutter.

Make adjustments in the configuration file `config.ini`:

```
## Config file for running all batch scripts on different nodes
[BATCH]
account = <account>
partition = <partition>

[ENV]
## Latest e3sm unified env for compy: /share/apps/E3SM/conda_envs/load_latest_e3sm_unified_compy.sh
## Latest e3sm unified env for Perlmutter: /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh
source = /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh
## if using a user specific environment, source conda and activate user environment (env = work)
## Otherwise, keep as is.
## For perlmutter use e3sm_unified_latest. For some reason the load_latest_e3sm_unified_pm-cpu.sh doesn't work!
env = e3sm_unified_latest

[CMD]
genclimoDir = /path/to/genclimo
case = <caseName>
start = <startYear>
end = <endYear>
inDirectory = /path/to/input/data

## Model options are cam / eam / scream (for EAMxx)
model = <model>
## Walltime is usually 10-15 mins
walltime = 00:10:00

variables
#= bc_a1,bc_a3,bc_a4,so4_a1,so4_a2,so4_a3,pom_a1,pom_a3,pom_a4,soa_a1,soa_a2,soa_a3,SO2,ncl_a1,ncl_a2,ncl_a3,T,PS,AODVIS,AODABS,lat,lon,ncol
## No values indicate all variables
## For selected variables put comma separated values (ex: variables = bc_a1_SRF, bc_a4_SRF, etc)

outDirectory = /path/to/output/data
## No values indicate inDirectory as outDirectory
## or put full directory path (ex: outDirectory = some/output/dir)

## Run this config by: python submit_batch_jobs.py
```

Submit the batch jobs with:
`python submit_batch_jobs.py`
