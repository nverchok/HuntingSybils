from GUI import *
from Utils import *
from NodeSim import *
from GraphGen import *
from Adversary import *
from SybilDetection import *
import sys
import time
import pprint
import matplotlib.pyplot as plt


pp = pprint.PrettyPrinter(indent=4)
sys.stdout.flush()
tick = 0
prev_time = time.time()
def p(s=""):
	global tick
	global prev_time
	new_time = time.time()
	time_diff = new_time - prev_time
	prev_time = new_time
	extra = "" if s=="" else " ("+str(s)+")"
	print("{0:}: {1:0.3f}s{2}".format(tick, time_diff, extra), flush=True)
	tick += 1


if __name__ == "__main__":
	p("start")
	
	
	# fig = plt.figure(figsize=(6,4))
	# ax = fig.add_axes(
	# 	(0.1,0.1,0.8,0.8),
	# 	xlim=(0,300),
	# 	ylim=(-0.02,1.02))
	# ax.set_xticks(list(range(0,301,25)))
	# ax.set_yticks([0,0.2,0.4,0.6,0.8,1.0])
	# ax.xaxis.set_visible(True)
	# ax.yaxis.set_visible(True)
	# ax.plot(
	# 	list(range(0,301,20)), 
	# 	list(map(GraphGen.simu_dist_prob_fun, list(range(0,301,20)))),
	# 	color="#7030A0",
	# 	marker=".")
	# plt.show()
	# exit(1)

#---------------------------------- Others ----------------------------------#

	# Node.setMaxTime(50)
	# terrain = Terrain(50, 50)

	# node_sim = NodeSim(terrain, Node.max_time)
	# nodes_all = node_sim.genNodeGroup(140, (0,0,50,50), lambda x: (x[0],0), "hon")

	# val_time_1 = 0
	# val_pos_1 = (25,25)
	# val_rad = 32.5

#-------------------------- Generate Nodes Locally --------------------------#

	Node.setMaxTime(50)
	terrain = Terrain(100, 8.00+10.67+16.46+10.67+8.00)
	terrain.addRestriction((0, 0, 100, 8.00), color="#636363")
	terrain.addRestriction((0, 8.00+10.67, 100, 16.46), color="#AAAAAA")
	terrain.addRestriction((0, 8.00+10.67+16.46+10.67, 100, 8.00), color="#636363")
	p("terrain created")

	node_sim = NodeSim(terrain, Node.max_time)
	nodes_hon = node_sim.genNodeGroup(100, (0,0,terrain.width,terrain.height), lambda x: (x[0],0), "hon")
	nodes_syb = node_sim.genNodeGroup(20, (34,11,12,8), lambda x: (np.random.normal(2.6,0.35),0), "syb")
	nodes_mal = node_sim.genNodeGroup(6, (34,11,14,8), lambda x: (np.random.normal(2.6,0.35),0), "mal")
	nodes_all = np.concatenate([nodes_hon, nodes_syb, nodes_mal])
	# Utils.exportNodes(nodes_all, "input_files/node_data.txt")

	val_time_1 = 4
	val_time_2 = 19
	val_pos_1 = (32,14)
	val_pos_2 = (49,16)
	val_rad = 32.5
	
#---------------------- Import Locally-Generated Nodes ----------------------#

	# terrain = Terrain(100, 8.00+10.67+16.46+10.67+8.00)
	# terrain.addRestriction((0, 0, 100, 8.00), color="#636363")
	# terrain.addRestriction((0, 8.00+10.67, 100, 16.46), color="#AAAAAA")
	# terrain.addRestriction((0, 8.00+10.67+16.46+10.67, 100, 8.00), color="#636363")
	# p("terrain created")

	# nodes_all = Utils.importNodes("../inputs/node_data.txt")

	# val_time_1 = 4
	# val_time_2 = 19
	# val_pos_1 = (32,14)
	# val_pos_2 = (49,16)
	# val_rad = 32.5

#---------------------- Import Patrick-Generated Nodes ----------------------#

	# terrain = Terrain(800, 150)
	# p("terrain created")
	
	# nodes_all, dim = Utils.importNodes_PatrickSim("../inputs/marathon2_2000_2.scb", node_type="hon")

	# val_time_1 = 243
	# val_pos_1 = (700,125)
	# val_rad = 40

#--------------------------------- Analysis ---------------------------------#

	p("input loaded")
	graph_gen = GraphGen(nodes_all, val_time_1, val_pos_1, val_rad)
	p("graph made")
	nodes_val = graph_gen.nodes_val
	comm_plan_original, key2idx, potential_conns = graph_gen.genCommPlan()
	p("comm plan made")
	comm_plan_modified = Adversary.impersonation(nodes_val, comm_plan_original)
	p("impersonation done")
	sim_conns_original = graph_gen.genSimuConns(comm_plan_modified)
	p("connections simulated")
	sim_conns_modified = Adversary.dissemination(nodes_val, comm_plan_original, sim_conns_original)
	p("dissemination done")
	id2edges = graph_gen.formEdges(sim_conns_modified, potential_conns, key2idx)
	p("edges formed")
	results = SybilDetection.runDetectionAlgorithms(nodes_val, id2edges)
	p("detection run")

	# Utils.printEdges("edges.csv", id2edges)

	g1 = graph_gen
	i2e1 = id2edges
	r1 = results

	# graph_gen = GraphGen(nodes_all, val_time_2, val_pos_2, val_rad)
	# p("graph made")
	# nodes_val = graph_gen.nodes_val
	# comm_plan_original, key2idx, potential_conns = graph_gen.genCommPlan()
	# p("comm plan made")
	# comm_plan_modified = Adversary.impersonation(nodes_val, comm_plan_original)
	# p("impersonation done")
	# sim_conns_original = graph_gen.genSimuConns(comm_plan_modified)
	# p("connections simulated")
	# sim_conns_modified = Adversary.dissemination(nodes_val, comm_plan_original, sim_conns_original)
	# p("dissemination done")
	# id2edges = graph_gen.formEdges(sim_conns_modified, potential_conns, key2idx)
	# p("edges formed")
	# results = SybilDetection.runDetectionAlgorithms(nodes_val, id2edges)
	# p("detection run")

	# g2 = graph_gen
	# i2e2 = id2edges
	# r2 = results

	id2node = {node.id:node for node in nodes_all}
	gui = GUI(terrain, id2node)
	p("gui initialized")
	gui.addLocVal("val1", g1, i2e1, r1)
	# gui.addLocVal("val2", g2, i2e2, r2)
	p("gui populated with locval data")
	gui.drawSim()
	