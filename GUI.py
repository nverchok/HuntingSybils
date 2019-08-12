import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle
from matplotlib.widgets import Slider
from matplotlib.widgets import RadioButtons
from Utils import *
from CurveAnalysis import *

class GUI:
	""" Encompasses the entire graphical interface, as well as managing its
	interactive elements such as buttons, sliders, and stdout output. """
	figsize = (13.0, 8.0)
	edges_display_reported_pos = False
	arrow_alpha_duration = 1.5
	CLICK_STATUS_IDLE = 0
	CLICK_STATUS_ARROWS = 1
	CLICK_STATUS_DISABLE = 2
	axcolor = "lightgoldenrodyellow"
	col_terrain_normal = "#DDDDDD"
	col_terrain_blocked = "#AAAAAA"
	col_terrain_edge = "#888888"
	col_loc_val_radius = "#A6BC95"
	col_node_fill = {
		"hon": "green",
		"mal": "yellow",
		"syb": "red"
	}
	col_node_edge = {
		"non-sybil": "darkgreen",
		"sybil": "darkred",
		"unknown": "darkgrey"
	}


	def __init__(self, terrain, nodes, id_to_idx):
		""" Stores the relevant data, and initialized a set of gfx lookup tables
		to store the references to the drawn graphical objects. """
		self.terrain = terrain
		self.nodes = nodes
		self.num_nodes = len(self.nodes)
		self.id_to_idx = id_to_idx
		self.loc_val_data = {}
		self.max_time = Node.max_time

		self.gfx = {}
		self.gfx["loc_val_radius"] = None
		self.gfx["radio_detector"] = None
		self.gfx["ax_radio_detector"] = None
		self.gfx["node_gfx"] = {}
		self.gfx["node_click_status"] = {node.id: GUI.CLICK_STATUS_IDLE for node in self.nodes}
		self.gfx["nodewise_arrow_gfx"] = {}

		self.curr_val_label = None
		self.curr_detector = None
		self.curr_time = 0
	

	def __getNodeFillColor__(self, node_id):
		""" Returns the fill color of a node (true node type). """
		true_type = self.nodes[self.id_to_idx[node_id]].type
		return GUI.col_node_fill.get(true_type, "black")
	

	def __getNodeEdgeColor__(self, node_id):
		""" Returns the edge color of a node (predicted node type). """
		if self.curr_val_label == None or self.curr_detector == None:
			return self.__getNodeFillColor__(node_id)
		else:
			curr_loc_val_data = self.loc_val_data[self.curr_val_label]
			curr_detector_pred_types = curr_loc_val_data["id_to_type"][self.curr_detector]
			pred_type = curr_detector_pred_types.get(node_id, "unknown")
			return GUI.col_node_edge.get(pred_type, "black")

	
	def __getArrowColor__(self, edge):
		""" Returns the color of an arrow (i.e. edge; connection success). """
		return "green" if edge.successful else "red"
	

	def __getNodePval__(self, node_id):
		""" Returns the pval of a node if available. """
		if self.curr_val_label == None or self.curr_detector == None:
			return "N/A"
		else:
			curr_loc_val_data = self.loc_val_data[self.curr_val_label]
			curr_detector_pvals = curr_loc_val_data["id_to_pval"].get(self.curr_detector, {})
			node_pval = curr_detector_pvals.get(node_id, "unknown")
			return str(node_pval)


	def addLocVal(self, val_label, graph_gen, edge_lists, results, id_to_type, id_to_pval):
		""" Stores the data associated with a location validation procedure. Thus
		multiple location validation procedures may be plotted at once, viewed one
		at a time (but swapped-between dynamically). """
		self.loc_val_data[val_label] = {
			"detectors": list(results.keys()),
			"graph": graph_gen,
			"edges": edge_lists,
			"results": results,
			"id_to_type": id_to_type,
			"id_to_pval": id_to_pval
		}
		self.curr_val_label = val_label
		detectors = self.loc_val_data[val_label]["detectors"]
		initial_det_label = detectors[0]
		self.curr_detector = initial_det_label


	def draw(self):
		""" Executes the drawing. """
		self.fig = plt.figure(figsize=GUI.figsize)
		self.ax = self.fig.add_axes(
			(0.15, 0.10, 0.85, 0.85),
			aspect="equal", 
			frameon=False,
			xlim=(-0.05, self.terrain.width + 0.05),
			ylim=(-0.05, self.terrain.height + 0.05))
		self.ax.add_patch(Rectangle(
			(0,0),
			self.terrain.width,
			self.terrain.height,
			ec=GUI.col_terrain_edge,
			fc=GUI.col_terrain_normal))

		ax_time_slider = plt.axes([0.20, 0.03, 0.75, 0.03], facecolor=GUI.axcolor, frameon=True)
		axfig_time_slider = self.fig.add_axes(
			ax_time_slider, 
			frameon=False,
			xlim=(-0.05, self.terrain.width + 0.05), 
			ylim=(-0.02,-0.01))
		ax_time_slider.xaxis.set_visible(True)
		ax_time_slider.set_xticks(list(range(Node.max_time)), minor=False)
		time_slider = Slider(ax_time_slider, "Time", 0, self.max_time, valinit=0, closedmin=True, closedmax=True)
		time_slider.valstep = 0.2


		ax_radio_loc_val = plt.axes([0.02, 0.70, 0.08, 0.25], facecolor=GUI.axcolor, frameon=True)
		radio_loc_val = RadioButtons(ax_radio_loc_val, tuple(self.loc_val_data.keys()))

		
		ax_radio_detector = plt.axes([0.02, 0.40, 0.08, 0.25], facecolor=GUI.axcolor, frameon=True)
		radio_detector = RadioButtons(ax_radio_detector, tuple())
		self.gfx["radio_detector"] = radio_detector
		self.gfx["ax_radio_detector"] = ax_radio_detector

		for rstr in self.terrain.restrictions:
			data = rstr[0]
			color = rstr[1]
			self.ax.add_patch(Rectangle( (data[0],data[1]), data[2], data[3], ec=GUI.col_terrain_edge, fc=color))


		def __drawNodes__():
			""" Creates graphical objects for all nodes. """
			for i in range(self.num_nodes):
				node = self.nodes[i]
				node_gfx = Circle(
					node.getPos(0), 
					radius=0.38, 
					linewidth=1.5,
					ec=self.__getNodeEdgeColor__(node.id), 
					fc=self.__getNodeFillColor__(node.id), 
					zorder=3)
				node_gfx.set_picker(True)
				node_gfx.set_url(node.id)
				self.ax.add_patch(node_gfx)
				self.gfx["node_gfx"][node.id] = node_gfx
			self.fig.canvas.draw_idle()
			return

		
		def __drawNodewiseArrows__(node_id):
			""" Creates the set of arrow objects for a given broadcasting node. """
			if node_id not in self.gfx["nodewise_arrow_gfx"]:
				edge_lists = self.loc_val_data[self.curr_val_label]["edges"]
				id2idx_val = self.loc_val_data[self.curr_val_label]["graph"].id_to_idx
				temp_arrow_list = []
				for edge in edge_lists[id2idx_val[node_id]]:
					pos1 = edge.node_src.getPos(edge.time, reported_pos=GUI.edges_display_reported_pos)
					pos2 = edge.node_dst.getPos(edge.time, reported_pos=GUI.edges_display_reported_pos)
					x, y, dx, dy = (pos2[0], pos2[1], pos1[0]-pos2[0], pos1[1]-pos2[1])
					col = self.__getArrowColor__(edge)
					arrow_gfx = self.ax.arrow(
						x, y, dx, dy, 
						color=col, 
						visible=False, 
						zorder=2, 
						linewidth=0.2, 
						head_width=0, 
						length_includes_head=True)
					arrow_gfx.set_url(edge.time)
					temp_arrow_list += [arrow_gfx]
				self.gfx["nodewise_arrow_gfx"][node_id] = np.array(temp_arrow_list)
			return
		

		def __drawNodeCDF__(node_id):
			edge_lists = self.loc_val_data[self.curr_val_label]["edges"]
			id2idx_val = self.loc_val_data[self.curr_val_label]["graph"].id_to_idx
			edges = edge_lists[id2idx_val[node_id]]
			xvals, cdf = CurveAnalysis.calcNodeConnCDF(edges)
			CurveAnalysis.plotCDF(xvals, cdf)
			return
		

		def __updateValRadiusAlpha__():
			""" Updates the visual representation of the location validation are
			(i.e. a large circle), showing it only while the procedure is in progress
			and hiding it before and after the procedure. """
			rad_gfx = self.gfx["loc_val_radius"]
			graph = self.loc_val_data[self.curr_val_label]["graph"]
			time_start = graph.time_start
			time_end = graph.time_end
			if self.curr_time < time_start:
				rad_gfx.set_visible(False)
			elif self.curr_time < time_end:
				rad_gfx.set_alpha(1)
				rad_gfx.set_visible(True)
			elif self.curr_time < time_end + GUI.arrow_alpha_duration:
				new_alpha = 1-((self.curr_time - time_end)/GUI.arrow_alpha_duration)**0.5
				rad_gfx.set_visible(True)
				rad_gfx.set_alpha(new_alpha)
			else:
				rad_gfx.set_visible(False)
			return
		

		def __updateArrowAlpha__(arrow_gfx, node_id):
			""" Updates the visual representation of a single arrow (edge) depending
			on the current time selected and the broadcasting node's click status (i.e.
			whether arrows for this node should be shown at all). """
			arrow_time = float(arrow_gfx.get_url())
			node_click_status = self.gfx["node_click_status"][node_id]
			if node_click_status != GUI.CLICK_STATUS_ARROWS:
				arrow_gfx.set_visible(False)
			elif arrow_time > self.curr_time:
				arrow_gfx.set_visible(False)
			elif arrow_time + GUI.arrow_alpha_duration < self.curr_time:
				arrow_gfx.set_visible(False)
			else:
				new_alpha = 1-((self.curr_time - arrow_time)/GUI.arrow_alpha_duration)**0.5
				arrow_gfx.set_visible(True)
				arrow_gfx.set_alpha(new_alpha)
			return
		

		def __updateArrows__(node_id):
			__drawNodewiseArrows__(node_id)
			for arrow_gfx in self.gfx["nodewise_arrow_gfx"][node_id]:
				__updateArrowAlpha__(arrow_gfx, node_id)
			return

		
		def __updateCurrTime__(val):
			""" Updates the current time to the one selected on the time slider. Then
			triggers further updates of the location validation radius and all existing
			arrow objects. """
			self.curr_time = float(val)
			__updateValRadiusAlpha__()
			for node in self.nodes:
				node_gfx = self.gfx["node_gfx"][node.id]
				node_gfx.center = node.getPos(self.curr_time)
			edge_lists = self.loc_val_data[self.curr_val_label]["edges"]
			id2idx_val = self.loc_val_data[self.curr_val_label]["graph"].id_to_idx
			for i in range(self.num_nodes):
				click_status = self.gfx["node_click_status"][i]
				node_id = self.nodes[i].id
				if click_status == GUI.CLICK_STATUS_ARROWS:
					edge_list = edge_lists[id2idx_val[node_id]]
					for arrow_gfx in self.gfx["nodewise_arrow_gfx"][node_id]:
						__updateArrowAlpha__(arrow_gfx, node_id)
			self.fig.canvas.draw()
			return
		

		def __updateDetector__(det_label):
			""" Updates the current detector chosen from the list of current detectors.
			Recolors relevant node edges according to the predictions made by the new 
			detector. Additionally, prints the precision and recall figures for the new 
			detector to stdout. """
			self.curr_detector = det_label
			for node in self.nodes:
				node_gfx = self.gfx["node_gfx"][node.id]
				node_gfx.set_ec(self.__getNodeEdgeColor__(node.id))
			results = self.loc_val_data[self.curr_val_label]["results"]
			print("Mode now: {}  ({}, {})".format(det_label, results[det_label].precision(), results[det_label].recall()))
			self.fig.canvas.draw()
			return


		def __updateDetectorList__(det_list):
			""" Updates the current detector list according to the current location
			validation procedure, correspondingly updating the RadioButtons UI element. 
			Triggers a UI update indirectly through __updateDetector__()."""
			detectors = self.loc_val_data[self.curr_val_label]["detectors"]
			ax_radio_detector = self.gfx["ax_radio_detector"]
			self.gfx["radio_detector"] = RadioButtons(ax_radio_detector, detectors)
			self.gfx["radio_detector"].on_clicked(__updateDetector__)
			__updateDetector__(detectors[0])
			return


		def __updateLocValProcedure__(val_label):
			""" Updates the current location validation procedure. Erases all arrow
			objects, updates the old radius object, and updates the detector list.
			Triggers a UI update indirectly through __updateDetectorList__(). """
			self.curr_val_label = val_label
			if self.gfx["loc_val_radius"] != None:
				self.gfx["loc_val_radius"].remove()
			graph = self.loc_val_data[val_label]["graph"]
			new_val_rad = Circle(
				graph.val_pos, 
				radius=graph.val_rad, 
				linewidth=1, 
				ec=GUI.col_loc_val_radius, 
				zorder=4, 
				visible=True, 
				fill=False)
			self.gfx["loc_val_radius"] = new_val_rad
			self.ax.add_patch(new_val_rad)
			__updateValRadiusAlpha__()
			for arrow_gfx in self.gfx["nodewise_arrow_gfx"].values():
				arrow_gfx.remove()
			self.gfx["nodewise_arrow_gfx"] = {}
			new_det_list = self.loc_val_data[val_label]["detectors"]
			__updateDetectorList__(new_det_list)
			return
		
		
		def __updateNodeStatus__(event):
			""" Creates a click-listener for the nodes to allow showing/hiding the
			set of a node's arrows. """
			if self.curr_val_label == None:
				return
			node_id = int(str(event.artist.get_url()))
			old_click_status = self.gfx["node_click_status"][node_id]
			if old_click_status == GUI.CLICK_STATUS_IDLE:
				self.gfx["node_click_status"][node_id] = GUI.CLICK_STATUS_DISABLE
				# __updateArrows__(node_id)
				__drawNodeCDF__(node_id)
				print("Node: {}, pval={}".format(node_id, self.__getNodePval__(node_id)))
			elif old_click_status == GUI.CLICK_STATUS_ARROWS:
				self.gfx["node_click_status"][node_id] = GUI.CLICK_STATUS_DISABLE
				__updateArrows__(node_id)
			elif old_click_status == GUI.CLICK_STATUS_DISABLE:
				self.gfx["node_click_status"][node_id] = GUI.CLICK_STATUS_IDLE
			else:
				print("# erroneous click status {} on node_id {}".format(old_click_status, node_id))
			self.fig.canvas.draw()
			return
		

		__drawNodes__()
		time_slider.on_changed(__updateCurrTime__)
		radio_detector.on_clicked(__updateDetector__)
		radio_loc_val.on_clicked(__updateLocValProcedure__)
		if self.loc_val_data != {}:
			__updateLocValProcedure__(list(self.loc_val_data.keys())[0])
		self.fig.canvas.mpl_connect("pick_event", __updateNodeStatus__)
		plt.show()