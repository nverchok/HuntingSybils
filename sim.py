from GUI import *
from Utils import *
from NodeSim import *
from GraphGen import *
from Adversary import *
from SybilDetection import *
import sys
import time
import pprint

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
	val_time = 4
	val_pos = (35,22)
	val_rad = 50
	terrain = Terrain(140,70)
	terrain.addRestriction((0, 0, 140, 16.1), color="#636363")
	terrain.addRestriction((0, 16.1+10.67, 140, 16.46), color="#AAAAAA")
	terrain.addRestriction((0, 70-16.1, 1540, 70), color="#636363")
	p("terrain created")

	# nodes_all, id2idx_all = Utils.importNodes("input_files/10Nodes.txt", node_type="hon")

	# nodes_hon, id_to_idx_hon = Utils.importNodes2("input_files/honest.txt", node_type="hon", id_offset=0)
	# nodes_syb, id_to_idx_syb = Utils.importNodes2("input_files/sybil.txt", node_type="syb", id_offset=len(nodes_hon))
	# nodes_mal, id_to_idx_mal = Utils.importNodes2("input_files/malicious.txt", node_type="mal", id_offset=len(nodes_hon)+len(nodes_syb))
	
	Node.setMaxTime(50)
	node_sim = NodeSim(terrain, Node.max_time)
	nodes_hon = node_sim.genNodeGroup(150, (0,0,terrain.width,terrain.height), lambda x: (x[0],0), "hon")
	nodes_syb = node_sim.genNodeGroup(25, (34,22,14,8), lambda x: (np.random.normal(2.6,0.35),0), "syb")
	nodes_mal = node_sim.genNodeGroup(10, (34,22,8,6), lambda x: (np.random.normal(2.6,0.35),0), "mal")

	nodes_all = np.concatenate([nodes_hon, nodes_syb, nodes_mal])
	id2idx_all = {nodes_all[i].id: i for i in range(len(nodes_all))}

	p("input loaded")
	graph = GraphGen(nodes_all, val_time, val_pos, val_rad)
	p("graph made")
	nodes_val = graph.nodes
	id2idx_val = graph.id_to_idx
	comm_plan_original, key2idx, potential_conns = graph.genCommPlan()
	p("comm plan made")

	comm_plan_modified = Adversary.impersonation(nodes_val, comm_plan_original)
	p("impersonation done")
	sim_conns_original = graph.genSimuConns(comm_plan_modified)
	p("connections simulated")
	sim_conns_modified = Adversary.dissemination(nodes_val, comm_plan_original, sim_conns_original)
	p("dissemination done")
	edge_lists = graph.formEdges(sim_conns_modified, potential_conns, key2idx)
	p("edges formed")

	sybil_detection = SybilDetection(nodes_all)
	p("sybil detection initialized")
	results, id2type, id2pval = sybil_detection.runDetectionAlgorithms(nodes_val, id2idx_val, edge_lists)
	p("detection run")
	gui = GUI(terrain, nodes_all, id2idx_all)
	p("gui initialized")
	gui.addLocVal("val1", graph, edge_lists, results, id2type, id2pval)
	p("gui populated with locval data")
	gui.draw()