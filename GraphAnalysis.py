import numpy as np
import scipy as sp

class GraphAnalysis:
	""" A collection of algorithms for Sybil detection that rely on the probabilistic
	model for P2P connection success as a function of pairwise distance. """
	simp_det_thresh = 1/3500000
	iter_det_thresh = 1/100000

	
	@staticmethod
	def __getEvalDistProb__(dist):
		""" Internal. Gives the probability of a connection succeeding given a 
		specific distance (based on exact experimental evidence). """
		raw_exp_x = [(25*i - 12.5) for i in range(13)]
		raw_exp_y = [1.000, 0.800, 0.650, 0.500, 0.354, 0.258, 0.196, 0.142, 0.092, 0.058, 0.042, 0.021, 0.017]
		return np.interp(dist, raw_exp_x, raw_exp_y, left=1.0, right=0.0)

	
	@staticmethod
	def __calcNodePval__(edges, ignored_ids=set()):
		""" Internal. Calculates the distribution of the sum of Edges (treated
		as binary random variables), and finds the left p-value of the observed
		log-likelihood sum. Ignores edges originating at ignored nodes. """
		obs_llh = 0
		exp_sum = 0
		var_sum = 0
		for edge in edges:
			if edge.node_src.id not in ignored_ids:
				llh, exp, var = edge.calcStatData(GraphAnalysis.__getEvalDistProb__)
				obs_llh += llh
				exp_sum += exp
				var_sum += var
		sd_sum = var_sum**0.5
		pval = sp.stats.norm(exp_sum, sd_sum).cdf(obs_llh)
		return pval, obs_llh
	

	@staticmethod
	def __calcPvals__(nodes, id_to_edges, ignored_ids=set()):
		""" Internal. Returns an array of left tail p-values for the nodes. """
		pvals = {}
		for node in nodes:
			if node.id not in ignored_ids:
				pval, llh = GraphAnalysis.__calcNodePval__(id_to_edges[node.id], ignored_ids=ignored_ids)
				pvals[node.id] = pval
		return pvals


	@staticmethod
	def simpleSybilDetection(nodes, id_to_edges):
		""" Labels Sybil all nodes whose p-values are below the threshold. """
		syb_ids = set()
		pvals = GraphAnalysis.__calcPvals__(nodes, id_to_edges)
		for node_id, pval in pvals.items():
			if pval < GraphAnalysis.simp_det_thresh:
				syb_ids |= {node_id}
		return syb_ids, pvals
	

	@staticmethod
	def iterativeSybilDetection(nodes, id_to_edges):
		""" Iteratively computes all p-values, labelling the most unlikely node
		as a Sybil if its LLH is below the threshold. If such a Sybil is found,
		then it is added to the ignored set and the procedure repeats. Procedure
		terminates when the most-unlikely node's LLH is above the threshold. In
		other words, plucks Sybils out one by one while constantly recalculating 
		all LLHs to account for the newfound absense of these Sybils."""
		syb_ids = set()
		pvals = {}
		while len(syb_ids) < 0.5*len(nodes):
			temp_pvals = GraphAnalysis.__calcPvals__(nodes, id_to_edges, ignored_ids=syb_ids)
			min_id = min(temp_pvals.items(), key=lambda x:x[1])[0]
			if temp_pvals[min_id] < GraphAnalysis.iter_det_thresh:
				syb_ids |= {min_id}
				pvals[min_id] = temp_pvals[min_id]
			else:
				pvals.update(temp_pvals)
				break
		return syb_ids, pvals