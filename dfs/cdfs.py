# create a cluster
# assign mission to master
# master will direct slaves to do the jobs

def simulate(self):
	while Time < 100: # until condition is true ... 
		time = time + 1
		
		master.step()
		for slave in slaves:
			slave.step()
