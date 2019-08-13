import numpy as np
import scipy as sp
import random
import matplotlib
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline

class CurveAnalysis:
	""" A collection of algorithms for Sybil detection that rely on the probabilistic
	model for P2P connection success as a function of pairwise distance. """
	dist_max = 100
	dist_inc = 1
	num_ticks = 20
	fig = None
	ax = None
	col_int = 0
	plotted_cdfs = {}


	@staticmethod
	def calcNodeConnCDF(edges):
		""" Calculates an observed cdf for a given edge set (presumably from a
		single node) by keeping track of the cumulative ratio of successful over
		potential connections over increasing distance. Returns lists of x-vals
		and y-vals, ready for plotting. """
		DIST_MAX = CurveAnalysis.dist_max
		DIST_INC = CurveAnalysis.dist_inc
		xvals = np.array([(i+1)*DIST_INC for i in range(DIST_MAX//DIST_INC)])
		sorted_edges = sorted(edges, key=lambda edge: edge.dist)
		num_potential = 0
		num_connected = 0
		cdf = np.zeros(DIST_MAX//DIST_INC)
		cdf_start_idx = 0
		curr_idx = 0
		curr_dist = DIST_INC
		while curr_dist < DIST_MAX:
			while curr_idx < len(sorted_edges):
				edge = sorted_edges[curr_idx]
				if edge.dist < curr_dist:
					num_potential += 1
					if edge.successful:
						num_connected += 1
					curr_idx += 1
				else:
					break
			if num_potential > 0:
				cdf[curr_dist//DIST_INC] = num_connected/num_potential
			else:
				cdf_start_idx += 1
			curr_dist += DIST_INC
		return xvals[cdf_start_idx:], cdf[cdf_start_idx:]
	

	@staticmethod
	def plotCDF(node, xvals, cdf):
		""" Plots the provided cdf on a globally-shared plot. Uses warm colors for
		sybils and cool colors for honest and malicious (physical) nodes. If a cdf
		with an indentical node.id is already plotted, removes it instead. """
		DIST_MAX = CurveAnalysis.dist_max
		NUM_TICKS = CurveAnalysis.num_ticks
		if CurveAnalysis.fig == None:
			CurveAnalysis.fig = plt.figure(figsize=(6,3))
			CurveAnalysis.ax = CurveAnalysis.fig.add_axes(
				(0.1, 0.2, 0.75, 0.75),
				frameon=False,
				xlim=(0, CurveAnalysis.dist_max),
				ylim=(0.0, 1.0),
				xlabel="distance (m)",
				ylabel="P(conn success)")	
			CurveAnalysis.ax.set_xticks([i*(DIST_MAX//NUM_TICKS) for i in range(NUM_TICKS+1)], minor=False)
			CurveAnalysis.ax.xaxis.set_visible(True)
		if node.id not in CurveAnalysis.plotted_cdfs:
			cool_color = matplotlib.cm.winter(CurveAnalysis.col_int) 
			warm_color = matplotlib.cm.autumn(CurveAnalysis.col_int)
			color = warm_color if node.type == "syb" else cool_color
			CurveAnalysis.col_int = (CurveAnalysis.col_int + 71) % 256
			CurveAnalysis.plotted_cdfs[node.id] = CurveAnalysis.ax.plot(xvals, cdf, label=node.id, color=color)
		else:
			for artist in CurveAnalysis.plotted_cdfs[node.id]:
				artist.remove()
			CurveAnalysis.plotted_cdfs.pop(node.id)
		CurveAnalysis.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
		CurveAnalysis.fig.show()
		
