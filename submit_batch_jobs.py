import configparser

from src.utils import exec_shell

# Load configuration file
config = configparser.ConfigParser(allow_no_value=True)
config.read("config.ini")

# Read configurations
account = config.get("BATCH", "account")
partition = config.get("BATCH", "partition")
env = config.get("ENV", "env")
source = config.get("ENV", "source")
case = config.get("CMD", "case")
start = config.get("CMD", "start")
end = config.get("CMD", "end")
in_directory = config.get("CMD", "inDirectory")
out_directory = config.get("CMD", "outDirectory")
model = config.get("CMD", "model")
variables = config.get("CMD", "variables")
genclimo_dir = config.get("CMD", "genclimoDir")
walltime = config.get("CMD", "walltime")


# Default output directory to input directory if not specified
if out_directory is None:
    out_directory = in_directory

# Loop through different time periods
for time_period in ["ann", "sea", "mon"]:
    script_path = f"{out_directory}/get_climoPy_{time_period}.sh"
    exec_shell(f"cp {genclimo_dir}/src/batch_script/get_climoPy_batch.sh {script_path}")

    # Read and modify the script template
    with open(script_path, "r") as file:
        file_data = file.read()

    file_data = file_data.replace("<account>", account)
    file_data = file_data.replace("<partition>", partition)
    file_data = file_data.replace("<source>", source)

    if env:
        file_data = file_data.replace("# user-defined environment", f"conda activate {env}")

    file_data = file_data.replace("<genclimoDir>", genclimo_dir)
    file_data = file_data.replace("<case>", case)
    file_data = file_data.replace("<start>", start)
    file_data = file_data.replace("<end>", end)
    file_data = file_data.replace("<directory>", in_directory)
    file_data = file_data.replace("<outDir>", out_directory)
    file_data = file_data.replace("<model>", model)
    file_data = file_data.replace("<wallMin>", walltime)

    if variables:
        file_data = file_data.replace("<vars>", variables)
    else:
        file_data = file_data.replace("-v <vars>", "")

    if time_period == "ann":
        file_data = file_data.replace("-t <time>", "")
    else:
        file_data = file_data.replace("<time>", time_period)

    # Write modified script back
    with open(script_path, "w") as file:
        file.write(file_data)

    # Submit the batch script
    exec_shell(f"sbatch {script_path}")