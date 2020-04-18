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

	NUM_SCENARIOS = 3
	NUM_COMM_SIMS = 3
	
#-------------------------------- Run Tests --------------------------------#

	Node.setMaxTime(50)
	terrain = Terrain(100, 8.00+10.67+16.46+10.67+8.00)
	terrain.addRestriction((0, 0, 100, 8.00), color="#636363")
	terrain.addRestriction((0, 8.00+10.67, 100, 16.46), color="#AAAAAA")
	terrain.addRestriction((0, 8.00+10.67+16.46+10.67, 100, 8.00), color="#636363")

	val_time = 4
	val_pos = (32,14)
	val_rad = 32.5

	# detectors = {"Simple", "Iterative", "Syb-Predict", "Syb-Rank"}
	detectors = {"LH Curve Outlier"}

	precision_data = {det:[] for det in detectors}
	recall_syb_data = {det:[] for det in detectors}
	recall_mal_data = {det:[] for det in detectors}

	for i in range(NUM_SCENARIOS):
		p("outer: {}".format(i))

		node_sim = NodeSim(terrain, Node.max_time)
		nodes_hon = node_sim.genNodeGroup(180, (0,0,terrain.width,terrain.height), lambda x: (x[0],0), "hon", collision=False)
		nodes_syb = node_sim.genNodeGroup(14, (34,11,12,8), lambda x: (np.random.normal(2.6,0.35),0), "syb", collision=False)
		nodes_mal = []#node_sim.genNodeGroup(6, (34,11,14,8), lambda x: (np.random.normal(2.6,0.35),0), "mal", collision=False)
		nodes_all = np.concatenate([nodes_hon, nodes_syb, nodes_mal])

		for j in range(NUM_COMM_SIMS):
			p("inner: {}".format(j))

			graph_gen = GraphGen(nodes_all, val_time, val_pos, val_rad)
			nodes_val = graph_gen.nodes_val
			comm_plan_original, key2idx, potential_conns = graph_gen.genCommPlan()
			comm_plan_modified = Adversary.impersonation(nodes_val, comm_plan_original)
			sim_conns_original = graph_gen.genSimuConns(comm_plan_modified)
			sim_conns_modified = Adversary.dissemination(nodes_val, comm_plan_original, sim_conns_original)
			id2edges = graph_gen.formEdges(sim_conns_modified, potential_conns, key2idx)
			results = SybilDetection.runDetectionAlgorithms(nodes_val, id2edges)
			
			for det in detectors:
				precision_data[det] += [results[det]["res_sypy"].precision()]
				recall_syb_data[det] += [results[det]["res_sypy"].recall()]
				recall_mal_data[det] += [results[det]["res_sypy"].recall_mal()]
	
	precision = {det:(np.mean(precision_data[det]),np.var(precision_data[det])) for det in detectors}
	recall_syb = {det:(np.mean(recall_syb_data[det]),np.var(recall_syb_data[det])**0.5) for det in detectors}
	recall_mal = {det:(np.mean(recall_mal_data[det]),np.var(recall_mal_data[det])**0.5) for det in detectors}
	for det in detectors:
		res_str = "Detector: {}\n".format(det)
		res_str += "  precision    : {:.3f} \u00B1 {:.3f}\n".format(*precision[det])
		res_str += "  recall (syb) : {:.3f} \u00B1 {:.3f}\n".format(*recall_syb[det])
		res_str += "  recall (mal) : {:.3f} \u00B1 {:.3f}\n".format(*recall_mal[det])
		print(res_str)
