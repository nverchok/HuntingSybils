from Utils import *
import math
import numpy as np

class NodeSim:
	""" A class for generating simple simulations of moving nodes. """
	node_id = -1


	@staticmethod
	def __genNodeID__():
		""" Internal. Generates a unique node id. """
		NodeSim.node_id += 1
		return NodeSim.node_id


	def __init__(self, terrain, max_time):
		""" Initialized a NodeSim object capable of generating clusters of nodes
		of a given node type and velocity function. """
		self.terrain = terrain
		self.max_time = max_time
		self.nodes_all = []


	def genNodeGroup(self, num_nodes, cluster_dims, vel_lim_fn=lambda x: x, node_type="hon", collision=True):
		""" Creates an array of Node objects that have been randomly generated within
		a specified cluster, with random velocities that have been constrained by a
		provided velocity function. The nodes assume the specified type, and are spawned
		at a minimum distance away from each other unless specified otherwise). """
		nodes = []
		num_left = num_nodes
		while(num_left > 0):
			x = cluster_dims[0] + np.random.random()*cluster_dims[2]
			y = cluster_dims[1] + np.random.random()*cluster_dims[3]
			valid = True
			for rstr in self.terrain.restrictions:
				r = rstr[0]
				if x >= r[0] and y >= r[1] and x <= r[0]+r[2] and y <= r[1]+r[3]:
					valid = False
					break
			if collision:
				for z in self.nodes_all:
					pos = z.getPos(0)
					dx = x - pos[0]
					dy = y - pos[1]
					if (dx**2 + dy**2) < 0.8:
						valid = False
						break
			if valid:
				vx = np.random.choice([-1,1]) * np.random.normal(1.3, 0.22)
				vy = np.random.choice([-1,1]) * np.random.normal(1.3, 0.22)
				vx,vy = vel_lim_fn((vx,vy))
				pos_data = {i: (x+i*vx,y+i*vy) for i in range(self.max_time)}
				new_node = Node(NodeSim.__genNodeID__(), pos_data, node_type)
				nodes += [new_node]
				num_left -= 1
			self.nodes_all += nodes
		return np.array(nodes)



