import numpy as np
import scipy as sp





class GraphAnalysis:
	""" A collection of algorithms for Sybil detection that rely on the probabilistic
	model for P2P connection success as a function of pairwise distance. """
	simp_det_thresh = 1/3500000
	iter_det_thresh = 1/3500000


	@staticmethod
	def setSimpDetThresh(simp_det_thresh):
		""" Sets the p-value threshold used in the Simple detection algorithm. """
		GraphAnalysis.simp_det_thresh = simp_det_thresh


	@staticmethod
	def setIterDetThresh(iter_det_thresh):
		""" Sets the p-value threshold used in the Iterative detection algorithm. """
		GraphAnalysis.iter_det_thresh = iter_det_thresh


	def __init__(self, nodes, edge_lists):
		""" Internal. Stores the array of nodes and edge-lists (similarly indexed). """
		self.nodes = nodes
		self.edge_lists = edge_lists
		self.num_nodes = len(self.nodes)

	
	def __getEvalDistProb__(self, dist):
		""" Internal. Gives the probability of a connection succeeding given a 
		specific distance (based on exact experimental evidence). """
		raw_exp_x = [(25*i - 12.5) for i in range(13)]
		raw_exp_y = [1.000, 0.800, 0.650, 0.500, 0.354, 0.258, 0.196, 0.142, 0.092, 0.058, 0.042, 0.021, 0.017]
		return np.interp(dist, raw_exp_x, raw_exp_y, left=1.0, right=0.0)

	
	def __calcNodePval__(self, edges, ignored_node_idxs=set()):
		""" Internal. Calculates the distribution of the sum of Edges (treated
		as binary random variables), and finds the left p-value of the observed
		log-likelihood sum. Ignores edges originating at ignored nodes. """
		obs_llh = 0
		exp_sum = 0
		var_sum = 0
		for edge in edges:
			if edge.node_src not in ignored_node_idxs:
				llh, exp, var = edge.calcStatData(self.__getEvalDistProb__)
				obs_llh += llh
				exp_sum += exp
				var_sum += var
		sd_sum = var_sum**0.5
		pval = sp.stats.norm(exp_sum, sd_sum).cdf(obs_llh)
		return pval, obs_llh
	

	def __calcPvals__(self, ignored_node_idxs=set()):
		""" Internal. Returns an array of left tail p-values for the nodes. """
		pvals = np.zeros(self.num_nodes)
		for i in range(self.num_nodes):
			if i not in ignored_node_idxs:
				pval, llh = self.__calcNodePval__(self.edge_lists[i], ignored_node_idxs)
				pvals[i] = pval
		return pvals


	def simpleSybilDetection(self):
		""" Labels Sybil all nodes whose p-values are below the threshold. """
		syb_idxs = set()
		pvals = self.__calcPvals__()
		for i in range(self.num_nodes):
			if pvals[i] < self.simp_det_thresh:
				syb_idxs |= {i}
		return syb_idxs, pvals
	

	def iterativeSybilDetection(self):
		""" Iteratively computes all p-values, labelling the most unlikely node
		as a Sybil if its LLH is below the threshold. If such a Sybil is found,
		then it is added to the ignored set and the procedure repeats. Procedure
		terminates when the most-unlikely node's LLH is above the threshold. In
		other words, plucks Sybils out one by one while constantly recalculating 
		all LLHs to account for the newfound absense of these Sybils."""
		syb_idxs = set()
		final_pvals = np.zeros(self.num_nodes)
		while len(syb_idxs) < 1*self.num_nodes:
			temp_pvals = self.__calcPvals__(ignored_node_idxs=syb_idxs)
			min_pval = 1
			min_idx = 0
			for i in range(self.num_nodes):
				if i not in syb_idxs and temp_pvals[i] < min_pval:
					min_pval = temp_pvals[i]
					min_idx = i
			if temp_pvals[min_idx] < self.iter_det_thresh:
				syb_idxs |= {min_idx}
				final_pvals[min_idx] = min_pval
			else:
				for i in set(range(self.num_nodes)) - syb_idxs:
					final_pvals[i] = temp_pvals[i]
				break
		return syb_idxs, final_pvals