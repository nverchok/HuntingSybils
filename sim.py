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
	val_time_1 = 4
	val_time_2 = 19
	val_pos_1 = (35,22)
	val_pos_2 = (52,24)
	val_rad = 40
	terrain = Terrain(140,70)
	terrain.addRestriction((0, 0, 140, 16.1), color="#636363")
	terrain.addRestriction((0, 16.1+10.67, 140, 16.46), color="#AAAAAA")
	terrain.addRestriction((0, 70-16.1, 140, 16.1), color="#636363")
	p("terrain created")

	# nodes_all, id2idx_all = Utils.importNodes("input_files/10Nodes.txt", node_type="hon")

	# nodes_hon, id_to_idx_hon = Utils.importNodes2("input_files/honest.txt", node_type="hon", id_offset=0)
	# nodes_syb, id_to_idx_syb = Utils.importNodes2("input_files/sybil.txt", node_type="syb", id_offset=len(nodes_hon))
	# nodes_mal, id_to_idx_mal = Utils.importNodes2("input_files/malicious.txt", node_type="mal", id_offset=len(nodes_hon)+len(nodes_syb))
	
	Node.setMaxTime(50)
	node_sim = NodeSim(terrain, Node.max_time)
	nodes_hon = node_sim.genNodeGroup(100, (0,0,terrain.width,terrain.height), lambda x: (x[0],0), "hon")
	nodes_syb = node_sim.genNodeGroup(15, (34,22,12,8), lambda x: (np.random.normal(2.6,0.35),0), "syb")
	nodes_mal = node_sim.genNodeGroup(8, (34,22,14,8), lambda x: (np.random.normal(2.6,0.35),0), "mal")

	nodes_all = np.concatenate([nodes_hon, nodes_syb, nodes_mal])
	id2node = {node.id:node for node in nodes_all}

	p("input loaded")
	graph = GraphGen(nodes_all, val_time_1, val_pos_1, val_rad)
	p("graph made")
	nodes_val = graph.nodes
	comm_plan_original, key2idx, potential_conns = graph.genCommPlan()
	p("comm plan made")
	comm_plan_modified = Adversary.impersonation(nodes_val, comm_plan_original)
	p("impersonation done")
	sim_conns_original = graph.genSimuConns(comm_plan_modified)
	p("connections simulated")
	sim_conns_modified = Adversary.dissemination(nodes_val, comm_plan_original, sim_conns_original)
	p("dissemination done")
	id2edges = graph.formEdges(sim_conns_modified, potential_conns, key2idx)
	p("edges formed")
	results = SybilDetection.runDetectionAlgorithms(nodes_val, id2edges)
	p("detection run")

	g1 = graph
	i2e1 = id2edges
	r1 = results

	graph = GraphGen(nodes_all, val_time_2, val_pos_2, val_rad)
	p("graph made")
	nodes_val = graph.nodes
	comm_plan_original, key2idx, potential_conns = graph.genCommPlan()
	p("comm plan made")
	comm_plan_modified = Adversary.impersonation(nodes_val, comm_plan_original)
	p("impersonation done")
	sim_conns_original = graph.genSimuConns(comm_plan_modified)
	p("connections simulated")
	sim_conns_modified = Adversary.dissemination(nodes_val, comm_plan_original, sim_conns_original)
	p("dissemination done")
	id2edges = graph.formEdges(sim_conns_modified, potential_conns, key2idx)
	p("edges formed")
	results = SybilDetection.runDetectionAlgorithms(nodes_val, id2edges, active_detectors={SybilDetection.D_SIMP, SybilDetection.D_RANK})
	p("detection run")

	g2 = graph
	i2e2 = id2edges
	r2 = results

	gui = GUI(terrain, id2node)
	p("gui initialized")
	gui.addLocVal("val1", g1, i2e1, r1)
	gui.addLocVal("val2", g2, i2e2, r2)
	p("gui populated with locval data")
	gui.draw()