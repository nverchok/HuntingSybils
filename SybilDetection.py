from GraphAnalysis import *
from Utils import *
import sypy





class SybilDetection:
	D_SIMP = "simple"
	D_ITER = "iterative"
	D_PRED = "sybil predict"
	D_RANK = "sybil rank"
	all_detectors = {D_SIMP, D_ITER, D_PRED, D_RANK}


	def __init__(self, nodes_all):
		self.nodes = nodes_all
		self.num_nodes = len(self.nodes)
		self.true_syb_idxs = {i for i in range(self.num_nodes) if self.nodes[i].type == "syb"}
		self.true_mal_idxs = {i for i in range(self.num_nodes) if self.nodes[i].type == "mal"}


	def runDetectionAlgorithms(self, nodes_val, id_to_idx, edge_lists, active_detectors=all_detectors):
		D_SIMP = SybilDetection.D_SIMP
		D_ITER = SybilDetection.D_ITER
		D_PRED = SybilDetection.D_PRED
		D_RANK = SybilDetection.D_RANK
		results = {}
		id_to_pred_type = {}
		id_to_pred_pval = {}

		graph_analysis = GraphAnalysis(nodes_val, edge_lists)
		num_val_nodes = len(nodes_val)
		val_node_idxs = set(range(num_val_nodes))
		val_true_syb_idxs = {i for i in range(num_val_nodes) if nodes_val[i].type == "syb"}
		val_true_mal_idxs = {i for i in range(num_val_nodes) if nodes_val[i].type == "mal"}
		val_syb_fraction = len(val_true_syb_idxs) / len(nodes_val)
		network = Utils.createSyPyNetwork(nodes_val, id_to_idx, edge_lists)

		print("1")
		if D_SIMP in active_detectors:
			simp_syb_idxs, simp_pvals = graph_analysis.simpleSybilDetection()
			simp_results = sypy.Results(
				val_node_idxs=val_node_idxs, 
				true_syb_idxs=val_true_syb_idxs, 
				true_mal_idxs=val_true_mal_idxs, 
				pred_syb_idxs=simp_syb_idxs)
			results[D_SIMP] = simp_results
			id_to_pred_type[D_SIMP] = {}
			id_to_pred_pval[D_SIMP] = {}
			for i in range(num_val_nodes):
				node_id = nodes_val[i].id
				id_to_pred_type[D_SIMP][node_id] = "sybil" if i in simp_syb_idxs else "non-sybil"
				id_to_pred_pval[D_SIMP][node_id] = simp_pvals[i]
		
		print("2")
		if D_ITER in active_detectors:
			iter_syb_idxs, iter_pvals = graph_analysis.iterativeSybilDetection()
			iter_results = sypy.Results(
				val_node_idxs=val_node_idxs, 
				true_syb_idxs=val_true_syb_idxs, 
				true_mal_idxs=val_true_mal_idxs, 
				pred_syb_idxs=iter_syb_idxs)
			results[D_ITER] = simp_results
			id_to_pred_type[D_ITER] = {}
			id_to_pred_pval[D_ITER] = {}
			for i in range(num_val_nodes):
				node_id = nodes_val[i].id
				id_to_pred_type[D_ITER][node_id] = "sybil" if i in iter_syb_idxs else "non-sybil"
				id_to_pred_pval[D_ITER][node_id] = iter_pvals[i]

		# print("3")
		# if D_PRED in active_detectors:
		# 	pred_results = sypy.SybilPredictDetector(network, pivot=val_syb_fraction).detect()
		# 	results[D_PRED] = pred_results
		# 	id_to_pred_type[D_PRED] = {}
		# 	for i in range(num_val_nodes):
		# 		node_id = nodes_val[i].id
		# 		id_to_pred_type[D_PRED][node_id] = "sybil" if i in pred_results.pred_syb_idxs else "non-sybil"

		# print("4")
		# if D_RANK in active_detectors:
		# 	rank_results = sypy.SybilPredictDetector(network, pivot=val_syb_fraction).detect()
		# 	results[D_RANK] = rank_results
		# 	id_to_pred_type[D_RANK] = {}
		# 	for i in range(num_val_nodes):
		# 		node_id = nodes_val[i].id
		# 		id_to_pred_type[D_RANK][node_id] = "sybil" if i in rank_results.pred_syb_idxs else "non-sybil"
		
		return results, id_to_pred_type, id_to_pred_pval

		
	#Draw the grid
	def drawGrid(self):
		if not self.detectionResultsStored:
			self.detectSybils(store_results=True)
		self.grid = grid(self)
		self.grid.draw()

	#Evaluation
	def evaluateResults(self):
		results = {}
		# print(str(self))
		for detector in self.detectors:
			results[detector] = (self.detection_results[detector].precision(), self.detection_results[detector].recall())
			# print(detector + ": " + str(len(self.detection_results[detector].nodes)/len(self.nodes)))
		return results