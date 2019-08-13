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
	D_PRED = "Sybil-Predict"
	D_RANK = "Sybil-Rank"
	all_detectors = {D_SIMP, D_ITER, D_PRED, D_RANK}


	@staticmethod
	def __genResultString__(results):
		res_str = ""
		res_str += "  precision    : {:.3f}\n".format(results.precision())
		res_str += "  recall (syb) : {:.3f}\n".format(results.recall())
		res_str += "  recall (mal) : {:.3f}\n".format(results.recall_mal())
		return res_str


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
		results = {}

		graph_analysis = GraphAnalysis(nodes_val, id_to_edges)
		val_all_ids = {node.id for node in nodes_val}
		val_syb_ids = {node.id for node in nodes_val if node.type == "syb"}
		val_mal_ids = {node.id for node in nodes_val if node.type == "mal"}
		val_syb_fraction = len(val_syb_ids) / len(nodes_val)
		network = Utils.createSyPyNetwork(nodes_val, id_to_edges)

		if D_SIMP in active_detectors:
			results[D_SIMP] = {}
			simp_syb_ids, simp_pvals = graph_analysis.simpleSybilDetection()
			simp_results = sypy.Results(val_node_ids=val_all_ids, true_syb_ids=val_syb_ids, true_mal_ids=val_mal_ids, pred_syb_ids=simp_syb_ids)
			results[D_SIMP]["matrix"] = SybilDetection.__genResultString__(simp_results)
			results[D_SIMP]["id_to_pval"] = simp_pvals
			results[D_SIMP]["id_to_type"] = {node_id:("sybil" if node_id in simp_syb_ids else "non-sybil") for node_id in val_all_ids}
		
		if D_ITER in active_detectors:
			results[D_ITER] = {}
			iter_syb_ids, iter_pvals = graph_analysis.iterativeSybilDetection()
			iter_results = sypy.Results(val_node_ids=val_all_ids, true_syb_ids=val_syb_ids, true_mal_ids=val_mal_ids, pred_syb_ids=iter_syb_ids)
			results[D_ITER]["matrix"] = SybilDetection.__genResultString__(iter_results)
			results[D_ITER]["id_to_pval"] = iter_pvals
			results[D_ITER]["id_to_type"] = {node_id:("sybil" if node_id in iter_syb_ids else "non-sybil") for node_id in val_all_ids}

		if D_PRED in active_detectors:
			results[D_PRED] = {}
			pred_results = sypy.SybilPredictDetector(network, pivot=val_syb_fraction).detect()
			results[D_PRED]["matrix"] = SybilDetection.__genResultString__(pred_results)
			results[D_PRED]["id_to_type"] = {node_id:("sybil" if node_id in pred_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}

		if D_RANK in active_detectors:
			results[D_RANK] = {}
			rank_results = sypy.SybilPredictDetector(network, pivot=val_syb_fraction).detect()
			results[D_RANK]["matrix"] = SybilDetection.__genResultString__(rank_results)
			results[D_RANK]["id_to_type"] = {node_id:("sybil" if node_id in rank_results.pred_syb_ids else "non-sybil") for node_id in val_all_ids}

		# comp = {
		# 	node.id: (
		# 	node.type,
		# 	round(results[D_ITER]["id_to_pval"][node.id]-results[D_SIMP]["id_to_pval"][node.id],4),
		# 	round(results[D_SIMP]["id_to_pval"][node.id],4),
		# 	round(results[D_ITER]["id_to_pval"][node.id],4)
		# 	) for node in nodes_val}
		# pp.pprint(comp)
		return results