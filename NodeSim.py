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


	def genNodeGroup(self, num_nodes, cluster_dims, vel_lim_fn=lambda x: x, node_type="hon", collision=True, collision_delta=0.8):
		""" Creates an array of Node objects that have been randomly generated within
		a specified cluster, with random velocities that have been constrained by a
		provided velocity function. The nodes assume the specified type, and are spawned
		at a minimum distance away from each other unless specified otherwise). """
		collision_delta_sq = collision_delta**2
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
			if collision and valid:
				for z in self.nodes_all:
					pos = z.getPos(0)
					dx = x - pos[0]
					dy = y - pos[1]
					if (dx**2 + dy**2) < collision_delta_sq:
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


	def genNodeGroup_gridAlg(self, num_nodes, cluster_dims, vel_lim_fn=lambda x: x, node_type="hon", collision=True, collision_delta=0.8):
		""" Creates an array of Node objects that have been randomly generated within
		a specified cluster, with random velocities that have been constrained by a
		provided velocity function. The nodes assume the specified type, and are spawned
		at a minimum distance away from each other unless specified otherwise). """
		d = int(math.ceil(collision_delta))
		nodes = []
		num_left = num_nodes
		grid = [(i,j) for i in range(cluster_dims[0]+cluster_dims[2]+1) for j in range(cluster_dims[1]+cluster_dims[3]+1)]
		for rstr in self.terrain.restrictions:
			r = rstr[0]
			for x in range(r[0]+1, r[0]+r[2]):
				for y in range(r[1]+1, r[1]+r[3]-1):
					try: grid.remove((x,y))
					except: pass
		for node in self.nodes_all:
			x = int(node.getPos(0)[0])
			y = int(node.getPos(0)[1])
			for i in range(-d+1,d):
				for j in range(-d+1,d):
					try: grid.remove((x+i,y+j))
					except: pass
		while(num_left > 0 and grid != []):
			x,y = grid[np.random.choice(range(len(grid)))]
			for i in range(-d+1,d):
				for j in range(-d+1,d):
					try: grid.remove((x+i,y+j))
					except: pass
			vx = np.random.choice([-1,1]) * np.random.normal(1.3, 0.22)
			vy = np.random.choice([-1,1]) * np.random.normal(1.3, 0.22)
			vx,vy = vel_lim_fn((vx,vy))
			pos_data = {i: (x+i*vx,y+i*vy) for i in range(self.max_time)}
			new_node = Node(NodeSim.__genNodeID__(), pos_data, node_type)
			nodes += [new_node]
			num_left -= 1
			self.nodes_all += nodes
		return np.array(nodes)



