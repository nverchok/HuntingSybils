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

delta = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
print("delta is: {} (metres)".format(delta))



# generate syb node
# generate mal node with delta offset
# generate N hon nodes uniformly around Sybil, all with delta offsets

TRIALS = 40
GLOBAL_DIST_DIFF = []
FIG_IDX = 0

NUM_MAL = 1

SYB_Ys = {}
MAL_Ys = {}

COMBINED_EDGES = {
	"syb":[], "mal":[],
	"up": {"syb":[], "mal":[]},
	"down": {"syb":[], "mal":[]},
	"left": {"syb":[], "mal":[]},
	"right": {"syb":[], "mal":[]}
}




for t in range(TRIALS):

	Node.setMaxTime(50)
	w = 70
	h = 70
	terrain = Terrain(2*w, 2*h)

	node_sim = NodeSim(terrain, Node.max_time)
	nodes_syb = node_sim.genNodeGroup(1, (w,h,0,0), lambda x: (0,0), "mal", collision=True, collision_delta=delta)
	nodes_mal = []
	for i in range(NUM_MAL):
		dw = (delta+0.1)*(math.sin(2*math.pi*i/NUM_MAL))
		dh = (delta+0.1)*(math.cos(2*math.pi*i/NUM_MAL))
		nodes_mal = np.array(list(nodes_mal) + list(node_sim.genNodeGroup(1, (w+dw,h+dh,0,0), lambda x: (0,0), "mal", collision=True, collision_delta=delta)))
	nodes_hon = node_sim.genNodeGroup_gridAlg(1000, (0,0,terrain.width,terrain.height), lambda x: x, "hon", collision=True, collision_delta=delta)
	nodes_all = np.concatenate([nodes_syb, nodes_mal, nodes_hon])

	val_time = 0
	val_pos = (w,h)
	val_rad = 60

	id_to_node = {node.id:node for node in nodes_all}
	gui = GUI(terrain, id_to_node)

	syb_node = nodes_syb[0]
	mal_node = nodes_mal[0]
	syb_pos = syb_node.getPos(0)
	mal_poss = [mal_node.getPos(0) for mal_node in nodes_mal]

	graph_gen = GraphGen(nodes_all, val_time, val_pos, val_rad)
	nodes_val = graph_gen.nodes_val


	#------ TEST 1: AVERAGE DIFFERENCE IN DISTANCES TO SYB VS MAL ------#
	for i in range(len(nodes_hon)):
		hon_pos = nodes_hon[i].getPos(0)
		syb_dist = ((syb_pos[0]-hon_pos[0])**2 + (syb_pos[1]-hon_pos[1])**2)**0.5
		mal_pos = mal_poss[i % NUM_MAL]
		mal_dist = ((mal_pos[0]-hon_pos[0])**2 + (mal_pos[1]-hon_pos[1])**2)**0.5
		GLOBAL_DIST_DIFF += [abs(syb_dist - mal_dist)]
	#-------------------------------------------------------------------#




	#------------ TEST 2: FLIPPING COINS BASED ON DISTANCES ------------#
# 	id_to_edges = {syb_node.id:[], mal_node.id:[]}
# 	for n in nodes_val:
# 		hon_pos = n.getPos(0)

# 		mal_dist = ((mal_pos[0]-hon_pos[0])**2 + (mal_pos[1]-hon_pos[1])**2)**0.5
# 		mal_success = np.random.random() <= GraphGen.simu_dist_prob_fun(mal_dist)
# 		id_to_edges[mal_node.id] += [Edge(n, mal_node, 0, mal_success)]

# 		syb_dist = ((syb_pos[0]-hon_pos[0])**2 + (syb_pos[1]-hon_pos[1])**2)**0.5
# 		syb_success = np.random.random() <= GraphGen.simu_dist_prob_fun(syb_dist)
# 		id_to_edges[syb_node.id] += [Edge(n, syb_node, 0, mal_success)]
	
# 	graph_gen = GraphGen(nodes_all, val_time, val_pos, val_rad)
# 	results = SybilDetection.createDummyResults(nodes_all)
# 	gui.addLocVal("val1", graph_gen, id_to_edges, results)

# 	syb_x, syb_y = GraphAnalysis.calcNodeLHCurve(id_to_edges[syb_node.id])
# 	mal_x, mal_y = GraphAnalysis.calcNodeLHCurve(id_to_edges[mal_node.id])
# 	SYB_Ys[syb_node.id] = syb_y
# 	MAL_Ys[mal_node.id] = mal_y

# gui.plotLHCurves(syb_x, SYB_Ys, fig_idx=FIG_IDX, n_type="syb")
# gui.plotLHCurves(mal_x, MAL_Ys, fig_idx=FIG_IDX, n_type="mal")
# gui.drawSim()
	#-------------------------------------------------------------------#
	



	#----------------- TEST 3: FLIPPING COINS COMBINED -----------------#
# 	for n in nodes_val:
# 		hon_pos = n.getPos(0)

# 		mal_dist = ((mal_pos[0]-hon_pos[0])**2 + (mal_pos[1]-hon_pos[1])**2)**0.5
# 		mal_success = np.random.random() <= GraphGen.simu_dist_prob_fun(mal_dist)
# 		COMBINED_EDGES["mal"] += [Edge(n, mal_node, 0, mal_success)]

# 		syb_dist = ((syb_pos[0]-hon_pos[0])**2 + (syb_pos[1]-hon_pos[1])**2)**0.5
# 		syb_success = np.random.random() <= GraphGen.simu_dist_prob_fun(syb_dist)
# 		COMBINED_EDGES["syb"] += [Edge(n, syb_node, 0, mal_success)]
# 		# print(COMBINED_EDGES["mal"][-1].dist, COMBINED_EDGES["syb"][-1].dist)
	
# 	graph_gen = GraphGen(nodes_all, val_time, val_pos, val_rad)
# 	results = SybilDetection.createDummyResults(nodes_all)
# 	gui.addLocVal("val1", graph_gen, COMBINED_EDGES, results)

# syb_x, syb_y = GraphAnalysis.calcNodeLHCurve(COMBINED_EDGES["syb"])
# mal_x, mal_y = GraphAnalysis.calcNodeLHCurve(COMBINED_EDGES["mal"])
# gui.plotLHCurves(syb_x, {"syb":syb_y}, fig_idx=FIG_IDX, n_type="syb")
# gui.plotLHCurves(mal_x, {"mal":mal_y}, fig_idx=FIG_IDX, n_type="mal")
# gui.drawSim()
	#-------------------------------------------------------------------#
	



	#----------- TEST 4: FLIPPING COINS COMBINED W MOVEMEMNT -----------#
# 	adv_keys = {(i+1):("mal"+str(i)) for i in range(NUM_MAL)}
# 	adv_keys.update({0:"syb"})
# 	comm_plan, key2idx, potential_conns = graph_gen.genCommPlan_customBroadcasters(adv_keys)
# 	sim_conns = graph_gen.genSimuConns(comm_plan)
# 	id_to_edges = graph_gen.formEdges(sim_conns, potential_conns, key2idx)
# 	i = -1
# 	j = -1
# 	for syb_edge in id_to_edges[syb_node.id]:
# 		i += 1
# 		mal_node = nodes_mal[i % NUM_MAL]
# 		for mal_edge in id_to_edges[mal_node.id]:
# 			if mal_edge.node_src == syb_edge.node_src and mal_edge.time == syb_edge.time:
# 				syb_edge.successful = mal_edge.successful
# 				COMBINED_EDGES["syb"] += [syb_edge]
# 				COMBINED_EDGES["mal"] += [mal_edge]
# 				j += 1
# 				break
# 	print(i,j)

# results = SybilDetection.createDummyResults(nodes_all)
# gui.addLocVal("val1", graph_gen, COMBINED_EDGES, results)
# syb_x, syb_y = GraphAnalysis.calcNodeLHCurve(COMBINED_EDGES["syb"])
# mal_x, mal_y = GraphAnalysis.calcNodeLHCurve(COMBINED_EDGES["mal"])
# gui.plotLHCurves(syb_x, {"syb":syb_y}, fig_idx=FIG_IDX, n_type="syb")
# gui.plotLHCurves(mal_x, {"mal":mal_y}, fig_idx=FIG_IDX, n_type="mal")
# gui.drawSim()
	#-------------------------------------------------------------------#
	



	#----------- TEST 4: FLIPPING COINS COMBINED W MOVEMEMNT -----------#
	adv_keys = {(i+1):("mal"+str(i)) for i in range(NUM_MAL)}
	adv_keys.update({0:"syb"})
	comm_plan, key2idx, potential_conns = graph_gen.genCommPlan_customBroadcasters(adv_keys)
	sim_conns = graph_gen.genSimuConns(comm_plan)
	id_to_edges = graph_gen.formEdges(sim_conns, potential_conns, key2idx)
	i = -1
	j = -1
	for syb_edge in id_to_edges[syb_node.id]:
		i += 1
		mal_node = nodes_mal[i % NUM_MAL]
		for mal_edge in id_to_edges[mal_node.id]:
			if mal_edge.node_src == syb_edge.node_src and mal_edge.time == syb_edge.time:
				syb_edge.successful = mal_edge.successful

				(xH,yH) = syb_edge.node_src.getPos(syb_edge.time)
				(xS,yS) = syb_edge.node_dst.getPos(syb_edge.time)
				(xM,yM) = mal_edge.node_dst.getPos(mal_edge.time)

				syb_dir = max([(yS-yH,"up"),(yH-yS,"down"),(xH-xS,"left"),(xS-xH,"right")])[1]
				mal_dir = max([(yM-yH,"up"),(yH-yM,"down"),(xH-xM,"left"),(xM-xH,"right")])[1]

				COMBINED_EDGES[syb_dir]["syb"] += [syb_edge]
				COMBINED_EDGES[mal_dir]["mal"] += [mal_edge]
				j += 1
				break
	print(i,j)

results = SybilDetection.createDummyResults(nodes_all)
gui.addLocVal("val1", graph_gen, COMBINED_EDGES, results)
for edge_dir in ["up","down","left","right"]:
	syb_x, syb_y = GraphAnalysis.calcNodeLHCurve(COMBINED_EDGES[edge_dir]["syb"])
	mal_x, mal_y = GraphAnalysis.calcNodeLHCurve(COMBINED_EDGES[edge_dir]["mal"])
	gui.plotLHCurves(syb_x, {"syb":syb_y}, fig_idx=FIG_IDX, n_type="syb", title=edge_dir)
	gui.plotLHCurves(mal_x, {"mal":mal_y}, fig_idx=FIG_IDX, n_type="mal", title=edge_dir)
	FIG_IDX += 1
gui.drawSim()
	#-------------------------------------------------------------------#





print("average distance difference from honests to syb vs mal is: {:.3f} ({:.3f}) (delta={})".format(np.mean(GLOBAL_DIST_DIFF), np.var(GLOBAL_DIST_DIFF)**0.5, delta))
	





