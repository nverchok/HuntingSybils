import numpy as np
import scipy as sp
import matplotlib
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline

class CurveAnalysis:
	""" A collection of algorithms for Sybil detection that rely on the probabilistic
	model for P2P connection success as a function of pairwise distance. """
	dist_max = 100
	dist_inc = 5


	@staticmethod
	def calcNodeConnCDF(edges):
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
	def plotCDF(xvals, cdf):
		fig = plt.figure(figsize=(5,3))
		ax = fig.add_axes(
			(0.1, 0.1, 0.85, 0.85),
			frameon=False,
			xlim=(0, CurveAnalysis.dist_max),
			ylim=(0.0, 1.0))	
		ax.set_xticks(xvals, minor=False)
		ax.xaxis.set_visible(True)
		# xnew = np.linspace(0, CurveAnalysis.dist_max, CurveAnalysis.dist_max)
		# spl = make_interp_spline(xvals, cdf, k=3)
		# cdf_smooth = spl(xnew)
		# plt.plot(xnew, cdf_smooth)
		plt.plot(xvals, cdf)
		plt.show()
		