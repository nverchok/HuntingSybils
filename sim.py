from Adversary import *
from Utils import *
from GUI import *
from GraphGen import *
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
	val_time = 4
	val_pos = (35,35)
	val_rad = 32.5
	terrain = Terrain(70,70)

	# nodes_all, id2idx_all = Utils.importNodes("input_files/10Nodes.txt", node_type="hon")
	p("start")
	nodes_hon, id_to_idx_hon = Utils.importNodes2("input_files/honest.txt", node_type="hon", id_offset=0)
	nodes_syb, id_to_idx_syb = Utils.importNodes2("input_files/sybil.txt", node_type="syb", id_offset=len(nodes_hon))
	nodes_mal, id_to_idx_mal = Utils.importNodes2("input_files/malicious.txt", node_type="mal", id_offset=len(nodes_hon)+len(nodes_syb))
	nodes_all = np.concatenate([nodes_hon, nodes_syb, nodes_mal])
	id2idx_all = {}
	id2idx_all.update(id_to_idx_hon)
	id2idx_all.update(id_to_idx_syb)
	id2idx_all.update(id_to_idx_mal)

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
	# gui = GUI(terrain, nodes_all, id2idx_all)
	# p()
	# gui.addLocVal("val1", graph, edge_lists, results, id2type, id2pval)
	# p()
	# gui.draw()