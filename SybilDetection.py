from GraphAnalysis import *
from Utils import *
import sypy
import pprint
pp = pprint.PrettyPrinter(width=10)

class SybilDetection:
	""" A class that encompasses the data required to perform detection with
	multiple algorithms, and evaluate the results. """
	D_SIMP = "Simple"
	D_ITER = "Iterative"
	D_PRED = "Syb-Predict"
	D_RANK = "Syb-Rank"
	D_SIMP_P = "Simple (pred PDF)"
	D_ITER_P = "Iterative (pred PDF)"
	D_LHCO = "LH Curve Outlier"
	# all_detectors = {D_SIMP, D_ITER, D_PRED, D_RANK, D_LHCO, D_SIMP_P, D_ITER_P}
	# all_detectors = {D_LHCO}
	all_detectors = {D_SIMP, D_ITER, D_PRED, D_RANK}


	@staticmethod
	def __genResultString__(sypy_results):
		""" Returns a formatted string comprising of one precision and two recall
		values (for sybils and malicious nodes) for a given Results object of a
		detector. Used in the GUI as a summary of the detector's results in stdout. """
		res_str = ""
		res_str += "  precision    : {:.3f}\n".format(sypy_results.precision())
		res_str += "  recall (syb) : {:.3f}\n".format(sypy_results.recall())
		res_str += "  recall (mal) : {:.3f}\n".format(sypy_results.recall_mal())
		return res_str
	

	@staticmethod
	def __createSyPyNetwork__(nodes_val, id_to_edges):
		""" Internal. Converts a given simulation into a SyPy-friendly 'network' 
		object that allows utilizing other (GSD-based) detection algorithms.
		Finds the largest connected component, and then creates a graph out of
		the bidirectional edges and corresponding nodes. """
		all_ids = {node.id for node in nodes_val}
		hon_ids = {node.id for node in nodes_val if node.type == "hon"}
		syb_ids = [node.id for node in nodes_val if node.type == "syb"]
		mal_ids = [node.id for node in nodes_val if node.type == "mal"]
		succ_edges = set()
		bidir_edges = []
		for node_id in all_ids:
			for edge in id_to_edges[node_id]:
				if edge.successful:
					src_id = edge.node_src.id
					dst_id = edge.node_dst.id
					if (dst_id,src_id) in succ_edges:
						bidir_edges += [(dst_id,src_id)]
					else:
						succ_edges.add((src_id,dst_id))
		nx_graph = nx.Graph()
		nx_graph.add_nodes_from(all_ids)
		nx_graph.add_edges_from(bidir_edges)
		cc_graph = max(nx.connected_component_subgraphs(nx_graph), key=len)
		cc_nodes = cc_graph.nodes()
		cc_edges = []
		for edge in bidir_edges:
			if edge[0] in cc_nodes and edge[1] in cc_nodes:
				cc_edges += [edge]
		nx_graph = nx.Graph()
		nx_graph.add_nodes_from(cc_nodes)
		nx_graph.add_edges_from(cc_edges)
		initial_sybils = list(set(all_ids)-set(cc_nodes))
		honest_edge_counts = {node_id:0 for node_id in cc_nodes}
		for edge in cc_edges:
			if edge[0] in hon_ids and edge[1] in hon_ids:
				honest_edge_counts[edge[0]] += 1
				honest_edge_counts[edge[1]] += 1
		known_honests = [sorted(honest_edge_counts.items(), key=lambda kv: kv[1], reverse=True)[0][0]]
		network = sypy.Network(None, None, "test", custom_graph=sypy.CustomGraph(nx_graph))
		network.set_data(original_nodes=all_ids, sybils=syb_ids, malicious=mal_ids, known_honests=known_honests, initial_sybils=initial_sybils)
		return network


	@staticmethod
	def runDetectionAlgorithms(nodes_val, id_to_edges, active_detectors=all_detectors):
		""" Takes in the data from a location validation procedure and executes 
		the default detection algorithms on it (unless overridden). Returns three
		dicts, each indexed by the active detector labels. These three dicts are of 
		SyPy.Result objects (confusion matricies), of node_id to predicted node type,
		and of node_id to node p-value (only available for Simple and Iterative). """
		D_SIMP = SybilDetection.D_SIMP
		D_ITER = SybilDetection.D_ITER
		D_PRED = SybilDetection.D_PRED
		D_RANK = SybilDetection.D_RANK
		D_SIMP_P = SybilDetection.D_SIMP_P
		D_ITER_P = SybilDetection.D_ITER_P
		D_LHCO = SybilDetection.D_LHCO
		results = {}

		val_all_ids = {node.id for node in nodes_val}
		val_syb_ids = {node.id for node in nodes_val if node.type == "syb"}
		val_mal_ids = {node.id for node in nodes_val if node.type == "mal"}
		val_syb_fraction = len(val_syb_ids) / len(nodes_val)
		network = SybilDetection.__createSyPyNetwork__(nodes_val, id_to_edges)
		dist_prob_fun = None

		id_to_node = {node.id:node for node in nodes_val}

		if D_SIMP in active_detectors:
			det_results = {}
			pred_syb_ids, pvals = GraphAnalysis.simpleSybilDetection(nodes_val, id_to_edges)
			sypy_results = sypy.Results(val_node_ids=val_all_ids, true_syb_ids=val_syb_ids, true_mal_ids=val_mal_ids, pred_syb_ids=pred_syb_ids)
			det_results["res_sypy"] = sypy_results
			det_results["res_string"] = SybilDetection.__genResultString__(sypy_results)
			det_results["id_to_pval"] = pvals
			det_results["id_to_type"] = {node_id:("sybil" if node_id in sypy_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}
			det_results["init_syb_ids"] = sypy_results.initial_sybils
			results[D_SIMP] = det_results
			
		
		if D_ITER in active_detectors:
			det_results = {}
			pred_syb_ids, pvals = GraphAnalysis.iterativeSybilDetection(nodes_val, id_to_edges)
			sypy_results = sypy.Results(val_node_ids=val_all_ids, true_syb_ids=val_syb_ids, true_mal_ids=val_mal_ids, pred_syb_ids=pred_syb_ids)
			det_results["res_sypy"] = sypy_results
			det_results["res_string"] = SybilDetection.__genResultString__(sypy_results)
			det_results["id_to_pval"] = pvals
			det_results["id_to_type"] = {node_id:("sybil" if node_id in sypy_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}
			det_results["init_syb_ids"] = sypy_results.initial_sybils
			results[D_ITER] = det_results

		if D_PRED in active_detectors:
			det_results = {}
			sypy_results = sypy.SybilPredictDetector(network, pivot=val_syb_fraction).detect()
			det_results["res_sypy"] = sypy_results
			det_results["res_string"] = SybilDetection.__genResultString__(sypy_results)
			det_results["id_to_pval"] = {}
			det_results["id_to_type"] = {node_id:("sybil" if node_id in sypy_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}
			det_results["init_syb_ids"] = sypy_results.initial_sybils
			results[D_PRED] = det_results

		if D_RANK in active_detectors:
			det_results = {}
			sypy_results = sypy.SybilRankDetector(network, pivot=val_syb_fraction).detect()
			det_results["res_sypy"] = sypy_results
			det_results["res_string"] = SybilDetection.__genResultString__(sypy_results)
			det_results["id_to_pval"] = {}
			det_results["id_to_type"] = {node_id:("sybil" if node_id in sypy_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}
			det_results["init_syb_ids"] = sypy_results.initial_sybils
			results[D_RANK] = det_results

		if D_SIMP_P in active_detectors:
			det_results = {}
			if dist_prob_fun == None:
				X, Ys, Y_RANSAC = GraphAnalysis.calcGlobalPDF(id_to_node, id_to_edges)
				dist_prob_fun = lambda dist: np.interp(dist, X, Y_RANSAC, left=0.95, right=0.05)
			pred_syb_ids, pvals = GraphAnalysis.simpleSybilDetection(nodes_val, id_to_edges, dist_prob_fun=dist_prob_fun)
			sypy_results = sypy.Results(val_node_ids=val_all_ids, true_syb_ids=val_syb_ids, true_mal_ids=val_mal_ids, pred_syb_ids=pred_syb_ids)
			det_results["res_sypy"] = sypy_results
			det_results["res_string"] = SybilDetection.__genResultString__(sypy_results)
			det_results["id_to_pval"] = pvals
			det_results["id_to_type"] = {node_id:("sybil" if node_id in sypy_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}
			det_results["init_syb_ids"] = sypy_results.initial_sybils
			results[D_SIMP_P] = det_results
		
		if D_ITER_P in active_detectors:
			det_results = {}
			if dist_prob_fun == None:
				X, Ys, Y_RANSAC = GraphAnalysis.calcGlobalPDF(id_to_node, id_to_edges)
				dist_prob_fun = lambda dist: np.interp(dist, X, Y_RANSAC, left=0.95, right=0.05)
			pred_syb_ids, pvals = GraphAnalysis.iterativeSybilDetection(nodes_val, id_to_edges, dist_prob_fun=dist_prob_fun)
			sypy_results = sypy.Results(val_node_ids=val_all_ids, true_syb_ids=val_syb_ids, true_mal_ids=val_mal_ids, pred_syb_ids=pred_syb_ids)
			det_results["res_sypy"] = sypy_results
			det_results["res_string"] = SybilDetection.__genResultString__(sypy_results)
			det_results["id_to_pval"] = pvals
			det_results["id_to_type"] = {node_id:("sybil" if node_id in sypy_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}
			det_results["init_syb_ids"] = sypy_results.initial_sybils
			results[D_ITER_P] = det_results
		
		if D_LHCO in active_detectors:
			det_results = {}
			pred_syb_ids = GraphAnalysis.likelihoodSybilDetection(nodes_val, id_to_edges)
			sypy_results = sypy.Results(val_node_ids=val_all_ids, true_syb_ids=val_syb_ids, true_mal_ids=val_mal_ids, pred_syb_ids=pred_syb_ids)
			det_results["res_sypy"] = sypy_results
			det_results["res_string"] = SybilDetection.__genResultString__(sypy_results)
			det_results["id_to_pval"] = {}
			det_results["id_to_type"] = {node_id:("sybil" if node_id in sypy_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}
			det_results["init_syb_ids"] = sypy_results.initial_sybils
			results[D_LHCO] = det_results
			
		return results