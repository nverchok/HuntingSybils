import math
import numpy as np
import networkx as nx
import sypy





class Node:
	""" A node class containing an id and position data. """
	max_time = 0
	loc_rate = 2


	@staticmethod
	def setMaxTime(max_time):
		""" Sets the length of the position np.array. """
		Node.max_time = max_time


	@staticmethod
	def setLocRate(loc_rate):
		""" Sets the frequency of transmitted location updates (seconds). """
		Node.loc_rate = loc_rate


	@staticmethod
	def getDist(node1, node2, time, reported_pos=False):
		""" Gives the distance (metres) between two nodes at a given time. The
		optional reported_pos argument gives the last reported location instead
		of the true location (governed by Node.loc_rate). """
		pos1 = node1.getPos(time, reported_pos=reported_pos)
		pos2 = node2.getPos(time, reported_pos=reported_pos)
		dist = ((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)**0.5
		return dist


	def __init__(self, node_id, pos_data, node_type="hon"):
		""" Creates a Node object using an integer id, a dictionary of time-
		indexed location data, and a node type ("hon", "mal", or "syb"). """
		self.id = node_id
		self.pos = np.zeros((Node.max_time+1,2))
		self.type = node_type
		for i in range(Node.max_time+1):
			if i in pos_data:
				self.pos[i] = pos_data[i]
			elif i != 0:
				self.pos[i] = self.pos[i-1]


	def getPos(self, time, reported_pos=False):
		""" Gives the (x,y) tuple location of a Node at a given time. The
		reported_pos flag indicates whether to return the true location or
		the last reported location derived from Node.loc_rate. """
		if reported_pos:
			return self.pos[int(Node.loc_rate*(time//Node.loc_rate))]
		elif time == int(time):
			return self.pos[time]
		else:
			time_lower = int(time)
			time_upper = int(time + 1)
			a = time_upper - time
			xl = self.pos[time_lower][0]
			yl = self.pos[time_lower][1]
			xu = self.pos[time_upper][0]
			yu = self.pos[time_upper][1]
			x_intp = a*x_lower + (1-a)*x_upper
			y_intp = a*y_lower + (1-a)*y_upper
			return (x_intp, y_intp)





class Edge:
	""" An edge class containing the source and destination Nodes, the time
	of the edge, and whether it was successful or not. """


	def __init__(self, node_src, node_dst, time, successful):
		""" Creates an Edge object with the source and destination Nodes, 
		the time of formation, and whether it succeeded. """
		self.node_src = node_src
		self.node_dst = node_dst
		self.time = time
		self.successful = successful
	

	def calcStatData(self, dist_prob_function):
		""" Treats the edge as a binary random variable with a success chance
		derived using the argument function. Then, calculates both the observed
		llog-likelihood (llh), and the expectation (exp1) and variance (var) of
		the edge. Used in the 'Sybilness' evaluation. """
		dist = Node.getDist(self.node_src, self.node_dst, self.time, reported_pos=True)
		p = dist_prob_function(dist)
		q = 1-p
		ln_p = math.log(p)
		ln_q = math.log(q)
		exp1 = p*ln_p + q*ln_q
		exp2 = p*(ln_p**2) + q*(ln_q**2)
		var = exp2 - (exp1**2)
		llh = ln_p if self.successful else ln_q
		return llh, exp1, var
		




class KeyGen:
	""" A class for generating unique (ideally unguessable) fixed-length strings. """
	

	def __init__(self):
		""" Initializes the object. """
		self.unique_key = 0
		self.key_length = 6
	

	def reset(self):
		""" Resets the keyspace. """
		self.unique_key = 0
	

	def genKey(self):
		""" Generates a unique fixed-length string. """
		unique_str = str(self.unique_key)
		pad_length = self.key_length - len(unique_str) - 1
		key = "k" + "0"*pad_length + unique_str
		self.unique_key += 1
		return key





class Terrain:
	""" A class that represents the geographical 2D layout for a scenario. 
	Contains information about the x,y dimensions of the scenario, as well
	rectangular obstructions such as buildings or roads. """

	
	def __init__(self, width, height, restrictions=[]):
		self.width = width
		self.height = height
		self.restrictions = restrictions





class Utils:
	""" A collection of functions: for importing nodes from a text file, for 
	obtaining a set of location validation participants, for processing tuples
	(used in evaluating detection results), and for forming a SyPy-friendly 
	'network' object used by other detection algorithms. """
	

	@staticmethod
	def importNodes(file_name, node_type="hon"):
		f = open(file_name, "r")
		node_data = {}
		time = 0
		max_time = 0
		for l in f.readlines():
			if l[0:2] == "T=":
				time = int(l[3:])
				if time > max_time:
					max_time = time
			elif l[0:2] == "ID":
				entry = l.split(":")
				node_id = int(entry[1][1:-2])
				node_x = int(entry[2][1:-2])
				node_y = int(entry[3][1:-5])
				if node_id not in node_data:
					node_data[node_id] = {}
				node_data[node_id][time] = (node_x,node_y)
		f.close()
		Node.setMaxTime(max_time)
		nodes_temp = []
		id_to_idx = {}
		for node_id in node_data.keys():
			new_node = Node(node_id, node_data[node_id], node_type=node_type)
			id_to_idx[node_id] = len(nodes_temp)
			nodes_temp += [new_node]
		nodes = np.array(nodes_temp)
		return nodes, id_to_idx
	

	@staticmethod
	def importNodes2(file_name, node_type="hon", id_offset=0):
		f = open(file_name, "r")
		node_data = {}
		max_time = 0
		for l in f.readlines():
			line = l.split(",")
			time = int(line[0])
			node_id = int(line[1]) + id_offset
			node_x = float(line[2])
			node_y = float(line[3])
			if node_id not in node_data:
				node_data[node_id] = {}
			node_data[node_id][time] = (node_x,node_y)
			if time > max_time:
				max_time = time
		f.close()
		Node.setMaxTime(max_time)
		nodes_temp = []
		id_to_idx = {}
		for node_id in node_data.keys():
			new_node = Node(node_id, node_data[node_id], node_type=node_type)
			id_to_idx[node_id] = len(nodes_temp)
			nodes_temp += [new_node]
		nodes = np.array(nodes_temp)
		return nodes, id_to_idx


	@staticmethod
	def getLocValSet(original_nodes, time, center, radius):
		""" Returns an array of nodes to be involved in a location validation 
		procedure, and a mapping from node.id to the index in this list (or -1 
		indicating absence). Membership is determined by euclidean proximity
		from the center at start time, based on *last reported* location. """
		nodes_temp = []
		id_to_idx = {}
		cx, cy = center
		for node in original_nodes:
			id_to_idx[node.id] = -1
			nx, ny = node.getPos(time, reported_pos=True)
			if (nx-cx)**2 + (ny-cy)**2 <= radius**2:
				id_to_idx[node.id] = len(nodes_temp)
				nodes_temp += [node]
		nodes = np.array(nodes_temp)
		return nodes, id_to_idx


	@staticmethod
	def addTuples(t1, t2):
		""" Adds elementwise two tuples of arbitray length. """
		res = []
		for i in range(min(len(t1), len(t2))):
			res += [t1[i] + t2[i]]
		return tuple(res)
	

	@staticmethod
	def divTuple(t, v):
		""" Divides elementwise a tuple of arbitray length by a number. """
		res = []
		for i in t:
			res += [round(i/v,3)]
		return tuple(res)
	

	@staticmethod
	def normTuples(L, N):
		""" Stuff. """
		NN = max(N-1,1)
		L = list(zip(*L))
		m1 = sum(L[0])/N
		m2 = sum(L[1])/N
		sd1 = (sum(list(map(lambda x: (x-m1)**2, L[0])))/NN)**0.5
		sd2 = (sum(list(map(lambda x: (x-m2)**2, L[1])))/NN)**0.5
		return "%1.3f,%1.3f,%1.3f,%1.3f" % (m1, sd1, m2, sd2)


	@staticmethod
	def createSyPyNetwork(nodes, id_to_idx, edge_lists):
		""" Converts a given simulation into a SyPy-friendly 'network' object 
		that allows utilizing other (GSD-based) detection algorithms. First,
		finds the largest connected component. Then, creates a graph out of the
		bidirectional edges and corresponding nodes  """
		num_nodes = len(nodes)
		succ_edges = {}
		bidir_edges = []
		for i in range(num_nodes):
			for edge in edge_lists[i]:
				if edge.successful:
					if (edge.node_dst.id,edge.node_src.id) in succ_edges:
						bidir_edges += [(edge.node_dst.id,edge.node_src.id)]
					else:
						succ_edges[(edge.node_src.id,edge.node_dst.id)] = True
		nx_graph = nx.Graph()
		nx_graph.add_nodes_from([i for i in range(num_nodes)])
		nx_graph.add_edges_from(bidir_edges)
		cc_graph = max(nx.connected_component_subgraphs(nx_graph), key=len)
		cc_nodes = cc_graph.nodes()
		cc_edges = []
		for edge in bidir_edges:
			if id_to_idx[edge[0]] in cc_nodes and id_to_idx[edge[1]] in cc_nodes:
				cc_edges += [edge]
		nx_graph = nx.Graph()
		nx_graph.add_nodes_from(cc_nodes)
		nx_graph.add_edges_from(cc_edges)
		initial_sybils = list(set(range(len(nodes)))-set(cc_nodes))
		honest_edge_counts = {}
		for i in cc_nodes:
			honest_edge_counts[i] = 0
		for edge in cc_edges:
			if nodes[id_to_idx[edge[0]]].type == "hon" and nodes[id_to_idx[edge[1]]].type == "hon":
				honest_edge_counts[id_to_idx[edge[0]]] += 1
				honest_edge_counts[id_to_idx[edge[1]]] += 1
		known_honests = [sorted(honest_edge_counts.items(), key=lambda kv: kv[1], reverse=True)[0][0]]
		original_nodes = [i for i in range(num_nodes)]
		true_syb_idxs = [i for i in range(num_nodes) if nodes[i].type == "syb"]
		true_mal_idxs = [i for i in range(num_nodes) if nodes[i].type == "mal"]
		network = sypy.Network(None, None, "test", custom_graph=sypy.CustomGraph(nx_graph))
		network.set_data(original_nodes=original_nodes, sybils=true_syb_idxs, malicious=true_mal_idxs, known_honests=known_honests, initial_sybils=initial_sybils)
		return network


