# genclimo
Generate annual/seasonal/monthly climo files for diagnostics

General Usage
-------------


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