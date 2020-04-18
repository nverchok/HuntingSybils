import random
import numpy as np

class Adversary:
	""" A container for actions available to an Adversary to thwart detection. """


	@staticmethod
	def impersonation(nodes, comm_plan, min_mal_listeners=1):
		""" Alters a communication plan. In every round, only a minimum number of
		malicious nodes remain as listeners, while the others broadcast the keys of
		Sybil nodes, thereby impersonating the Sybils' presence. """
		new_comm_plan = np.copy(comm_plan)
		num_nodes = comm_plan.shape[0]
		num_rounds = comm_plan.shape[1]
		syb_idxs = [i for i in range(num_nodes) if nodes[i].type == "syb"]
		mal_idxs = [i for i in range(num_nodes) if nodes[i].type == "mal"]
		for rnd in range(num_rounds):
			bdcaster_syb_idxs = [i for i in syb_idxs if comm_plan[i,rnd] != "listen"]
			listener_mal_idxs = [i for i in mal_idxs if comm_plan[i,rnd] == "listen"]
			subset_size = max(min(len(bdcaster_syb_idxs), len(listener_mal_idxs)) - min_mal_listeners, 0)
			subset_syb_idxs = random.sample(bdcaster_syb_idxs, subset_size)
			subset_mal_idxs = random.sample(listener_mal_idxs, subset_size)
			for i in range(subset_size):
				syb_key = comm_plan[subset_syb_idxs[i],rnd]
				new_comm_plan[subset_mal_idxs[i],rnd] = syb_key
		return new_comm_plan

	
	@staticmethod
	def dissemination(nodes, comm_plan, simulated_conns, rate=1.0):
		""" Alters a set of connection results. Listening malicious nodes pool
		their sets of seen keys. These sets are subsequently subsampled (excluding
		adversarial indices) by all other adversarial nodes that were supposed
		to be listening according to the server's original communication plan. """
		num_nodes = simulated_conns.shape[0]
		num_rounds = simulated_conns.shape[1]
		if rate == 0:
			return simulated_conns
		advsry_idxs = [i for i in range(num_nodes) if nodes[i].type == "syb" or nodes[i].type == "mal"]
		for rnd in range(num_rounds):
			listener_advsry_idxs = [i for i in advsry_idxs if comm_plan[i,rnd] == "listen"]
			bdcaster_advsry_keys = [comm_plan[i,rnd] for i in advsry_idxs if comm_plan[i,rnd] != "listen"]
			combined_keys_seen = []
			for i in listener_advsry_idxs:
				combined_keys_seen += simulated_conns[i,rnd]
			nonsybil_keys_seen = list(set(combined_keys_seen) - set(bdcaster_advsry_keys))
			for i in listener_advsry_idxs:
				new_keys_seen = random.sample(nonsybil_keys_seen, int(rate*len(nonsybil_keys_seen)))
				simulated_conns[i,rnd] += new_keys_seen
		return simulated_conns