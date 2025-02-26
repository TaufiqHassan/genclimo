import configparser
from subprocess import Popen, PIPE, STDOUT

config = configparser.ConfigParser(allow_no_value=True)
config.read('config.ini')

account = config.get('BATCH','account')
partition = config.get('BATCH','partition')
env = config.get('ENV','env')
case = config.get('CMD','case')
start = config.get('CMD','start')
end = config.get('CMD','end')
inDirectory = config.get('CMD','inDirectory')
outDirectory = config.get('CMD','outDirectory')
model = config.get('CMD','model')
variables = config.get('CMD','variables')
genclimoDir = config.get('CMD','genclimoDir')
walltime = config.get('CMD','walltime')

def exec_shell(cmd):
    cmd_split = cmd.split(' ')
    p = Popen(cmd_split, stdout=PIPE, stdin=PIPE, stderr=STDOUT, universal_newlines=True)
    op, _ = p.communicate()
    
if outDirectory==None:
    outDirectory = inDirectory   
for time in ['ann','sea','mon']:
    exec_shell(f'cp {genclimoDir}/src/batch_script/get_climoPy_batch.sh {outDirectory}/get_climoPy_{time}.sh')
    with open(outDirectory+'/get_climoPy_'+time+'.sh','r') as file:
        filedata = file.read()
        filedata = filedata.replace('<account>',account)
        filedata = filedata.replace('<partition>',partition)
        filedata = filedata.replace('<env>',env)
        filedata = filedata.replace('<genclimoDir>',genclimoDir)
        filedata = filedata.replace('<case>',case)
        filedata = filedata.replace('<start>',start)
        filedata = filedata.replace('<end>',end)
        filedata = filedata.replace('<directory>',inDirectory)
        filedata = filedata.replace('<outDir>',outDirectory)
        filedata = filedata.replace('<model>',model)
        filedata = filedata.replace('<wallMin>',walltime)
        if variables!=None:
            filedata = filedata.replace('<vars>',variables)
        else:
            filedata = filedata.replace('-v <vars>','')
        if time=='ann':
            filedata = filedata.replace('-t <time>','')
        else:
            filedata = filedata.replace('<time>',time)
    with open(outDirectory+'/get_climoPy_'+time+'.sh','w') as file:
        file.write(filedata)
    exec_shell(f'sbatch {outDirectory}/get_climoPy_'+time+'.sh')
    
