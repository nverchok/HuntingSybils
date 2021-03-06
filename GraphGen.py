from Utils import *
import math
import numpy as np
import random
import pprint

class GraphGen:
	""" A class encompassing a single instance of a location validation process.
	Contains the process parameters (time (seconds), center (x,y), and radius 
	(metres). The genCommPlan() function that generates a communication plan for 
	the participatory nodes indicating the actions that they are to take in every 
	given round. The genSimuConns() function that executes a provided communications 
	plan and simulated establishing connections based on the distance-probabilistic
	model and node types. The formEdges() function creates a list of Edge objects
	created per node by a particular simulation of a communication plan. """
	simu_dist_prob_fun = lambda dist: np.interp(
		dist, 
		[(25*i - 12.5) for i in range(13)], 
		[1.000, 0.800, 0.650, 0.500, 0.354, 0.258, 0.196, 0.142, 0.092, 0.058, 0.042, 0.021, 0.017], 
		left=0.95, 
		right=0.01)


	def __init__(self, nodes_all, val_time, val_pos, val_rad, round_duration=2, syb_mal_mult=0.6, syb_syb_mult=0.6):
		""" Initialized a GraphGen object, storing the input parameters and also
		immediately computing variables needed for subsequent algorithms. """
		self.nodes_all = nodes_all
		self.val_time = val_time
		self.val_pos = val_pos
		self.val_rad = val_rad
		self.nodes_val = self.__getLocValSet__()
		self.time_start = val_time
		self.round_duration = round_duration
		self.num_nodes = len(self.nodes_val)
		self.num_rounds = int(2*math.ceil(math.log(self.num_nodes,2))) if self.num_nodes >= 2 else 0
		self.time_end = self.time_start + self.num_rounds*self.round_duration
		self.conn_prob_mult = {
			("hon","hon"): 1,
			("hon","mal"): 1,
			("hon","syb"): 0,
			("mal","hon"): 1,
			("mal","mal"): 1,
			("mal","syb"): syb_mal_mult,
			("syb","hon"): 0,
			("syb","mal"): syb_mal_mult,
			("syb","syb"): syb_syb_mult
		}
	

	def __getLocValSet__(self):
		""" Internal. Returns an array of nodes that will be involved in a 
		location validation procedure. Membership is determined by euclidean 
		proximity from the center at start time, based on their *last reported* 
		(not always true) location. """
		nodes_temp = []
		cx, cy = self.val_pos
		for node in self.nodes_all:
			nx, ny = node.getPos(self.val_time, reported_pos=True)
			if (nx-cx)**2 + (ny-cy)**2 <= self.val_rad**2:
				nodes_temp += [node]
		nodes = np.array(nodes_temp)
		return nodes
	

	def __recGenStates__(self, incomplete_comm_plan, depth, bgn, end):
		""" Internal. Recursively fills out an incomplete communication plan by 
		replacing default "listen" values with randomly generated unique key strings. 
		Algorithm ensures full bidirectional connectivity in logarithmic time. """
		if bgn==end:
			return
		mid = (bgn+end)//2
		incomplete_comm_plan[bgn:mid,depth] = self.keygen.genKeys(mid-bgn)
		incomplete_comm_plan[mid:end,depth] = "listen"
		incomplete_comm_plan[bgn:mid,depth+1] = "listen"
		incomplete_comm_plan[mid:end,depth+1] = self.keygen.genKeys(end-mid)
		if depth+2 < self.num_rounds:
			if(mid-bgn > 1):
				self.__recGenStates__(incomplete_comm_plan, depth+2, bgn, mid)
			if(end-mid > 1):
				self.__recGenStates__(incomplete_comm_plan, depth+2, mid, end)
	

	def __getRoundTime__(self, rnd):
		""" Internal. Returns the time of the start of a round. """
		time = self.time_start + rnd*self.round_duration
		return time
	

	def __attemptConn__(self, node1, node2, time):
		""" Internal. Attempts to establish a connection by flipping a coin biased
		according to the node types and separating distance at the *true* time. """
		dist = Node.getDist(node1, node2, time, reported_pos=False)
		prob = GraphGen.simu_dist_prob_fun(dist)
		success = np.random.random() <= prob * self.conn_prob_mult[(node1.type,node2.type)]
		return success
	

	def genCommPlan(self):
		""" Generate a communication plan, returning a 2D array of #nodes*#rounds. 
		Each entry is either "listen" or a unique key, created by a KeyGen object
		In every round, a node either listens or broadcasts its key. """
		if self.num_nodes < 2:
			return None, None, None
		comm_plan = np.full((self.num_nodes, self.num_rounds), "_done_")
		key_to_idx = {}
		self.keygen = KeyGen()
		self.__recGenStates__(comm_plan, 0, 0, self.num_nodes)
		np.random.shuffle(comm_plan)
		potential_conns = np.ndarray((self.num_nodes, self.num_rounds), dtype=object)		
		for rnd in range(self.num_rounds):
			listener_set = []
			bdcaster_set = []
			for i in range(self.num_nodes):
				potential_conns[i,rnd] = []
				if comm_plan[i,rnd] != "_done_":
					if comm_plan[i,rnd] == "listen":
						listener_set += [i]
					else:
						bdcaster_set += [i]
			for i in listener_set:
				for j in bdcaster_set:
					bdcaster_key = comm_plan[j,rnd]
					potential_conns[i,rnd] += [bdcaster_key]
					key_to_idx[bdcaster_key] = j
		return comm_plan, key_to_idx, potential_conns


	def genSimuConns(self, comm_plan):
		""" Simulate an execution of the communication plan. For every round, for
		every (listener, broadcaster) tuple, attempt to establish a connection by
		flipping a biased coin based on distance, and the two node types. Returns
		a 2D array of #nodes*#rounds, with each entry being a list of seen keys. """
		if self.num_nodes < 2:
			return None
		simulated_conns = np.ndarray((self.num_nodes, self.num_rounds), dtype=object)
		for rnd in range(self.num_rounds):
			time = self.__getRoundTime__(rnd)
			listener_set = []
			bdcaster_set = []
			for i in range(self.num_nodes):
				simulated_conns[i,rnd] = []
				if comm_plan[i,rnd] != "_done_":
					if comm_plan[i,rnd] == "listen":
						listener_set += [i]
					else:
						bdcaster_set += [i]
			for i in listener_set:
				for j in bdcaster_set:
					listen_node = self.nodes_val[i]
					bdcast_node = self.nodes_val[j]
					conn_successful = self.__attemptConn__(listen_node, bdcast_node, time)
					if conn_successful:
						simulated_conns[i,rnd] += [comm_plan[j,rnd]]
		return simulated_conns
	
	
	def formEdges(self, simulated_conns, potential_conns, key_to_idx, max_attempts=999):
		""" Constructs a list of Edge objects, each of which captures the source 
		and destination nodes, time, and success/failure of th edge. The ith entry
		in this list corresponds to all edges going TO node i in self.nodes. """
		if self.num_nodes < 2 or max_attempts < 1:
			return None
		id_to_edges = {}
		num_attempts = {}
		for node in self.nodes_val:
			id_to_edges[node.id] = []
		for rnd in range(self.num_rounds):
			time = self.__getRoundTime__(rnd)
			for i in range(self.num_nodes):
				node_src = self.nodes_val[i]
				node_potl_conns = {key_to_idx[key] for key in potential_conns[i,rnd]}
				node_simu_conns = {key_to_idx[key] for key in simulated_conns[i,rnd]}
				for j in node_potl_conns:
					if (i,j) not in num_attempts:
						num_attempts[(i,j)] = 1
					else:
						num_attempts[(i,j)] += 1
					
					if num_attempts[(i,j)] <= max_attempts:
						node_dst = self.nodes_val[j]
						successful = j in node_simu_conns
						id_to_edges[node_dst.id] += [Edge(node_src, node_dst, time, successful)]
		return id_to_edges
	

	def genCommPlan_customBroadcasters(self, broadcasters):
		""" Generate a communication plan, returning a 2D array of #nodes*#rounds. 
		Each entry is either "listen" or a unique key, created by a KeyGen object
		In every round, a node either listens or broadcasts its key. """
		if self.num_nodes < 2:
			return None, None, None
		comm_plan = np.full((self.num_nodes, self.num_rounds), "_done_")
		key_to_idx = {}
		self.keygen = KeyGen()
		self.__recGenStates__(comm_plan, 0, 0, self.num_nodes)
		np.random.shuffle(comm_plan)
		potential_conns = np.ndarray((self.num_nodes, self.num_rounds), dtype=object)
		for rnd in range(self.num_rounds):
			for (node_idx,key) in broadcasters.items():
				comm_plan[node_idx,rnd] = key
		for rnd in range(self.num_rounds):
			listener_set = []
			bdcaster_set = []
			for i in range(self.num_nodes):
				potential_conns[i,rnd] = []
				if comm_plan[i,rnd] != "_done_":
					if comm_plan[i,rnd] == "listen":
						listener_set += [i]
					else:
						bdcaster_set += [i]
			for i in listener_set:
				for j in bdcaster_set:
					bdcaster_key = comm_plan[j,rnd]
					potential_conns[i,rnd] += [bdcaster_key]
					key_to_idx[bdcaster_key] = j
		return comm_plan, key_to_idx, potential_conns