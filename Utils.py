import math
import numpy as np
import networkx as nx
import sypy
from threading import Lock

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
		for i in range(Node.max_time+1):
			if len(self.pos[i]) != 2:
				print("{} {} {}".format(self.id, i, self.pos[i]))


	def getPos(self, time, reported_pos=False):
		""" Gives the (x,y) tuple location of a Node at a given time. The
		reported_pos flag indicates whether to return the true location or
		the last reported location derived from Node.loc_rate. """
		if reported_pos:
			return self.pos[int(Node.loc_rate*(time//Node.loc_rate))]
		elif time == int(time):
			return self.pos[int(time)]
		else:
			time_lower = int(time)
			time_upper = int(time + 1)
			a = time - time_lower
			x_lower = self.pos[time_lower][0]
			y_lower = self.pos[time_lower][1]
			x_upper = self.pos[time_upper][0]
			y_upper = self.pos[time_upper][1]
			x_intp = x_lower + a*(x_upper-x_lower)
			y_intp = y_lower + a*(y_upper-y_lower)
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
		self.dist = Node.getDist(self.node_src, self.node_dst, self.time, reported_pos=True)
	

	def calcStatData(self, dist_prob_function):
		""" Treats the edge as a binary random variable with a success chance
		derived using the argument function. Then, calculates both the observed
		llog-likelihood (llh), and the expectation (exp1) and variance (var) of
		the edge. Used in the 'Sybilness' evaluation. Memoized. """
		p = dist_prob_function(self.dist)
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
		self.lock = Lock()
		self.unique_key = 10
		self.key_length = 6
	

	def genKeys(self, num_keys):
		""" Generates a unique fixed-length string). Synchronyzed. """
		self.lock.acquire()
		keys = []
		for i in range(num_keys):
			unique_str = str(self.unique_key)
			pad_length = self.key_length - len(unique_str) - 1
			key = "k" + "0"*pad_length + unique_str
			self.unique_key += 1
			keys += [key]
		self.lock.release()
		return keys





class Terrain:
	""" A class that represents the geographical 2D layout for a scenario. 
	Contains information about the x,y dimensions of the scenario, as well
	rectangular obstructions such as buildings or roads. """

	
	def __init__(self, width, height, restrictions=[]):
		self.width = width
		self.height = height
		self.restrictions = restrictions

	
	def addRestriction(self, rstr_data, color="#AAAAAA"):
		self.restrictions += [(rstr_data, color)]





class Utils:
	""" A collection of functions: for importing nodes from a text file, for 
	obtaining a set of location validation participants, for processing tuples
	(used in evaluating detection results), and for forming a SyPy-friendly 
	'network' object used by other detection algorithms. """
	

	@staticmethod
	def importNodes_PatrickSim(file_name, node_type="hon"):
		f = open(file_name, "r")
		node_data = {}
		time = 0
		max_time = 0
		dim = {"xmin":0,"xmax":0,"ymin":0,"ymax":0}
		for l in f.readlines():
			if l[0:2] == "T=":
				time = int(l[3:])//2
				if time > max_time:
					max_time = time
			elif l[0:2] == "ID":
				entry = l.split(":")
				node_id = int(entry[1][1:-2])
				node_x = float(entry[2][1:-2])/2
				node_y = float(entry[3][1:-5])/2
				dim["xmin"] = min(dim["xmin"], node_x)
				dim["xmax"] = max(dim["xmax"], node_x)
				dim["ymin"] = min(dim["ymin"], node_y)
				dim["ymax"] = max(dim["ymax"], node_y)
				if node_id not in node_data:
					node_data[node_id] = {}
				node_data[node_id][time] = (node_x,node_y)
		f.close()
		Node.setMaxTime(max_time)
		nodes_temp = []
		for node_id in node_data.keys():
			new_node = Node(node_id, node_data[node_id], node_type=node_type)
			nodes_temp += [new_node]
		nodes = np.array(nodes_temp)
		return nodes, dim
	

	@staticmethod
	def importNodes(file_name):
		f = open(file_name, "r")
		node_data = {}
		max_time = 0
		lines = f.readlines()
		node_summary = [entry.split(":") for entry in lines[0].split(",")[:-1]]
		node_types = {int(entry[0]):entry[1] for entry in node_summary}
		for l in lines[1:]:
			line = l.split(",")
			time = int(line[0])
			node_id = int(line[1])
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
		for node_id in node_data.keys():
			new_node = Node(node_id, node_data[node_id], node_type=node_types[node_id])
			nodes_temp += [new_node]
		nodes = np.array(nodes_temp)
		return nodes
	

	@staticmethod
	def exportNodes(nodes, file_name):
		f = open(file_name, "w+")
		node_summary = ""
		for node in nodes:
			node_summary += "{}:{},".format(node.id,node.type)
		node_summary += "\n"
		f.write(node_summary)
		for t in range(Node.max_time):
			for node in nodes:
				pos = node.getPos(t)
				f.write("{},{},{},{}\n".format(t, node.id, pos[0], pos[1]))
		f.close()


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