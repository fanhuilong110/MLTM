for prop in ['0.01','0.05','0.1','0.3','0.6','0.8','0.9','1']:
	for j in range(5):
		fname = 'p_del_%s_%d' %(prop,j+1)
		fp = open(fname,'w')
		fp.write('#PBS -l nodes=1:ppn=1\n#PBS -l walltime=24:00:00\ncd $PBS_O_WORKDIR\n')
		fp.write('module load gsl\nmodule load python/3.3.2\n')
		fp.write('cd %s/%d\n' %(prop,j+1))
		fp.write('python3 PyRun.py')
		fp.close()
