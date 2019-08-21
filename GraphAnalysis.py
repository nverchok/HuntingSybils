import numpy as np
import scipy as sp
from GraphGen import *
from sklearn import linear_model
import pprint

class GraphAnalysis:
	""" A collection of algorithms for Sybil detection that rely on the probabilistic
	model for P2P connection success as a function of pairwise distance. """
	simp_det_thresh = 1/3500000
	iter_det_thresh = 1/100000
	pdf_dist_max = 100
	pdf_dist_inc = 5
	base_dist_prob_fun = lambda dist: np.interp(
		dist, 
		[(25*i - 12.5) for i in range(13)], 
		[1.000, 0.800, 0.650, 0.500, 0.354, 0.258, 0.196, 0.142, 0.092, 0.058, 0.042, 0.021, 0.017], 
		left=0.95, 
		right=0.01)
	curr_dist_prob_fun = base_dist_prob_fun
		
		
	
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
				llh, exp, var = edge.calcStatData(GraphAnalysis.curr_dist_prob_fun)
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
	def calcNodeLHCurve(edges, ignored_ids=set()):
		""" Calculates an observed pdf for a given edge set (presumably from a
		single node) by keeping track of the interval ratio of successful over
		potential connections over increasing distance. Returns lists of x-vals
		and y-vals, ready for plotting. """
		DIST_MAX = GraphAnalysis.pdf_dist_max
		DIST_INC = GraphAnalysis.pdf_dist_inc
		x = np.array([(i+1)*DIST_INC for i in range(DIST_MAX//DIST_INC)])
		y = np.zeros(DIST_MAX//DIST_INC)
		sorted_edges = sorted(edges, key=lambda edge: edge.dist)
		curr_idx = 0
		curr_dist = 0
		while curr_dist < DIST_MAX:
			num_potential = 0
			num_connected = 0
			while curr_idx < len(sorted_edges):
				edge = sorted_edges[curr_idx]
				if curr_dist <= edge.dist and edge.dist < curr_dist + DIST_INC:
					if edge.node_src.id not in ignored_ids:
						num_potential += 1
						if edge.successful:
							num_connected += 1
					curr_idx += 1
				else:
					break
			if num_potential > 0:
				y[curr_dist//DIST_INC] = num_connected/num_potential
			curr_dist += DIST_INC
		return x, y

	
	@staticmethod
	def calcGlobalLHCurves(id_to_node, id_to_edges):
		""" Runs a series of RANSAC computations for every discritized distance.
		Also records the nodes that become outliers in each of these computations. """
		DIST_MAX = GraphAnalysis.pdf_dist_max
		DIST_INC = GraphAnalysis.pdf_dist_inc
		X = np.array([(i+1)*DIST_INC for i in range(DIST_MAX//DIST_INC)])
		Ys = {}
		for node_id, edges in id_to_edges.items():
			x, y = GraphAnalysis.calcNodePDF(edges)
			Ys[node_id] = y
		Ys_t = np.array(list(Ys.values())).transpose()
		outliers = {}
		Y_RANSAC = []

		# run RANSAC on each distance individually
		for i in range(len(Ys_t)):
			outliers[i] = {}
			Y_reg = Ys_t[i]
			X_reg = np.array([0]*len(Y_reg)).reshape(-1,1)
			reg = linear_model.RANSACRegressor()
			try:
				reg.fit(X_reg, Y_reg)
				Y_RANSAC += [reg.predict(np.array([[0]]))[0]]

				# record the outlier nodes for a given input
				for j in range(len(reg.inlier_mask_)):
					if not reg.inlier_mask_[j]:
						node = id_to_node[list(id_to_edges.keys())[j]]
						outliers[i][node.id] = (node.type, "{:.3f}".format(Y_reg[j]))#, reg.inlier_mask_[i])
				print("\n{}:".format((i+1)*DIST_INC))
				pprint.pprint(outliers[i])
			except ValueError:
				print("ransac failed on {}".format((i+1)*DIST_INC))
				sorted_Y_reg = sorted(Y_reg)
				lower_25 = int(len(sorted_Y_reg)*0.25)
				upper_25 = int(len(sorted_Y_reg)*0.75)
				Y_RANSAC += [np.mean(sorted_Y_reg[lower_25:upper_25])]

		# tabulate the number of times a node is an outlier
		is_outlier_count = {}
		for node_id in id_to_edges.keys():
			key = "{}:{}".format(node_id, id_to_node[node_id].type)
			is_outlier_count[key] = 0
			for i in range(len(Ys_t)):
				if node_id in outliers[i].keys():
					is_outlier_count[key] += 1
		pprint.pprint(sorted(is_outlier_count.items(), key=lambda x: x[1]))
		return X, Ys, Y_RANSAC


	@staticmethod
	def simpleSybilDetection(nodes, id_to_edges, dist_prob_fun=None):
		""" Labels Sybil all nodes whose p-values are below the threshold. """
		GraphAnalysis.curr_dist_prob_fun = dist_prob_fun if dist_prob_fun else GraphAnalysis.base_dist_prob_fun
		syb_ids = set()
		pvals = GraphAnalysis.__calcPvals__(nodes, id_to_edges, ignored_ids=[])
		for node_id, pval in pvals.items():
			if pval < GraphAnalysis.simp_det_thresh:
				syb_ids |= {node_id}
		return syb_ids, pvals
	

	@staticmethod
	def iterativeSybilDetection(nodes, id_to_edges, dist_prob_fun=None):
		""" Iteratively computes all p-values, labelling the most unlikely node
		as a Sybil if its LLH is below the threshold. If such a Sybil is found,
		then it is added to the ignored set and the procedure repeats. Procedure
		terminates when the most-unlikely node's LLH is above the threshold. In
		other words, plucks Sybils out one by one while constantly recalculating 
		all LLHs to account for the newfound absense of these Sybils."""
		GraphAnalysis.curr_dist_prob_fun = dist_prob_fun if dist_prob_fun else GraphAnalysis.base_dist_prob_fun
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
	

	@staticmethod
	def __getSusLHCurves__(nodes, id_to_edges, max_runs=10):
		""" Wip stuff. Supposed to be a likelihood-outlier-based detection algorithm 
		that first calculates the observed (discritized) likelihood curve of connection 
		success based on distance for each node, and then find the outlier nodes. """
		DIST_MAX = GraphAnalysis.pdf_dist_max
		DIST_INC = GraphAnalysis.pdf_dist_inc
		id_to_node = {node.id:node for node in nodes}

		run = 0
		syb_ids = set()
		id_to_edges_nonsyb = id_to_edges.copy()
		while run < max_runs:
			run += 1
			for syb_id in syb_ids & set(id_to_edges_nonsyb.keys()):
				id_to_edges_nonsyb.pop(syb_id)

			X = np.array([(i+1)*DIST_INC for i in range(DIST_MAX//DIST_INC)])
			Ys = {}
			is_outlier_count = {}
			for node_id, edges in id_to_edges_nonsyb.items():
				x, y = GraphAnalysis.calcNodeLHCurve(edges, ignored_ids=syb_ids)
				Ys[node_id] = y
				is_outlier_count[node_id] = 0

			idx_to_node_id = list(id_to_edges_nonsyb.keys())
			Ys_t = np.array(list(Ys.values())).transpose()
			outliers = {}
			Y_RANSAC = []

			# run RANSAC on each distance individually
			for i in range(len(Ys_t)):
				Y_reg = Ys_t[i]
				X_reg = np.array([0]*len(Y_reg)).reshape(-1,1)
				reg = linear_model.RANSACRegressor()
				try:
					reg.fit(X_reg, Y_reg)
					Y_RANSAC += [reg.predict(np.array([[0]]))[0]]

					# record the outlier nodes for a given input
					for j in range(len(reg.inlier_mask_)):
						inlier_fraction = sum(reg.inlier_mask_)/len(reg.inlier_mask_)
						if not reg.inlier_mask_[j]:
							is_outlier_count[idx_to_node_id[j]] += 1#2*inlier_fraction

				except ValueError:
					# print("ransac failed on {}".format((i+1)*DIST_INC))
					sorted_Y_reg = sorted(Y_reg)
					lower_25 = int(len(sorted_Y_reg)*0.25)
					upper_25 = int(len(sorted_Y_reg)*0.75)
					Y_RANSAC += [np.mean(sorted_Y_reg[lower_25:upper_25])]

			max_is_outlier_count = max(is_outlier_count.values())
			if max_is_outlier_count > len(X)*0.5:
				syb_ids |= {node_id for node_id in is_outlier_count if is_outlier_count[node_id] == max_is_outlier_count}
				# print({node_id:id_to_node[node_id].type for node_id in syb_ids})
			else:
				break

		return syb_ids
	

	@staticmethod
	def likelihoodSybilDetection(nodes, id_to_edges, N=7):
		""" More wip stuff. """
		syb_ids_counts = {node.id:0 for node in nodes}
		for t in range(N):
			trial_syb_ids = GraphAnalysis.__getSusLHCurves__(nodes, id_to_edges)
			for syb_id in trial_syb_ids:
				syb_ids_counts[syb_id] += 1
		syb_ids = {syb_id for syb_id in syb_ids_counts if syb_ids_counts[syb_id] >= N/2}
		return syb_ids
	

	