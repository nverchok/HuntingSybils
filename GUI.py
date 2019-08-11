import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle
from matplotlib.widgets import Slider

class GUI:
	edges_display_reported_pos = False
	arrow_alpha_duration = 1.5
	CLICK_STATUS_IDLE = 0
	CLICK_STATUS_ARROWS = 1
	CLICK_STATUS_DISABLE = 2
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
		self.terrain = terrain
		self.nodes = nodes
		self.num_nodes = len(self.nodes)
		self.id_to_idx = id_to_idx
		self.loc_val_data = {}
		self.max_time = Node.max_time

		self.gfx = {}
		self.gfx["loc_val_radius"] = None
		self.gfx["node_gfx"] = {}
		self.gfx["node_click_status"] = {}
		self.gfx["nodewise_arrow_gfx"] = {}

		self.curr_val_label = None
		self.curr_detector = None
	

	def __getNodeFillColor__(self, node_id):
		true_type = self.nodes[self.id_to_idx[node_id]].type
		return GUI.col_node_fill.get(true_type, "black")
	

	def __getNodeEdgeColor__(self, node_id):
		if self.curr_val_label == None or self.curr_detector == None:
			return self.__getNodeFillColor__(node_id)
		else:
			pred_type = self.loc_val_data[val_label]["id_to_type"][self.curr_detector].get(node_id, "unknown")
			return GUI.col_node_edge.get(pred_type, "black")

	
	def __getArrowColor__(self, edge):
		return "green" if edge.successful else "red"
	

	def __getNodePval__(self, node_id):
		if self.curr_val_label == None or self.curr_detector == None:
			return "N/A"
		else:
			curr_loc_val_data = self.loc_val_data[self.curr_val_label]
			curr_detector_pval = curr_loc_val_data["id_to_pval"]
			node_pval = curr_detector_pval[self.curr_detector].get(node_id, "unknown")
			return str(node_pval)


	def addLocVal(val_label, graph_gen, edge_lists, results, id_to_type, id_to_pval):
		self.loc_val_data[val_label] = {
			"detectors": list(results.keys()),
			"graph": graph_gen,
			"edges": edge_lists,
			"results": results,
			"id_to_type": id_to_type,
			"id_to_pval": id_to_pval
		}


	def draw(self):
		self.fig = plt.figure(figsize=(9.0, 9.0))
		self.ax = self.fig.add_axes(
			(0.05, 0.08, 0.88, 0.9),
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

		#Add slider for round number
		axcolor = "lightgoldenrodyellow"
		ax_time_slider = plt.axes([0.40, 0.01, 0.55, 0.03], facecolor=axcolor, frameon=True)
		axfig_time_slider = self.fig.add_axes(
			ax_time_slider, 
			frameon=False,
			xlim=(-0.05, self.terrain.width + 0.05), 
			ylim=(-0.02,-0.01))
		ax_time_slider.xaxis.set_visible(True)
		ax_time_slider.set_xticks(list(range(self.total_rounds)), minor=False)
		time_slider = Slider(ax_time_slider, "Time", 0, self.max_time-0.99, valinit=0, closedmin=True, closedmax=True)
		time_slider.valstep = 0.5

		#Add radio buttons for all the location validation procedures
		axcolor = "lightgoldenrodyellow"
		ax_radio_loc_val = plt.axes([0.01, 0.01, 0.05, 0.10], facecolor=axcolor, frameon=True)
		radio_loc_val = RadioButtons(ax_radio_loc_val, tuple(self.loc_val_data.keys()))

		#Add radio buttons for all detectors used in a given location validation procedure
		axcolor = "lightgoldenrodyellow"
		ax_radio_detector = plt.axes([0.01, 0.11, 0.05, 0.10], facecolor=axcolor, frameon=True)
		radio_detector = RadioButtons(ax_radio_detector, tuple())


		#Draw restrictions
		# for rstr in self.restrictions:
		# 	r = rstr[0]
		# 	col = rstr[1]
		# 	self.ax.add_patch(Rectangle((r[0],r[1]), r[2], r[3], ec=self.edge_color, fc=col))
		

		def __drawNodes__():
			for i in self.num_nodes:
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
		

		def __updateArrowAlpha__(arrow_gfx, arrow_time):
			if arrow_time < self.curr_time or arrow_time > self.curr_time + GUI.arrow_alpha_duration:
				arrow_gfx.set_visible(False)
			else:
				new_alpha = arrow_alpha_duration**0.5 - (self.curr_time - arrow_time)**0.5
				arrow_gfx.set_visible(True)
				arrow_gfx.set_alpha(new_alpha)
			return

		
		def __updateNodewiseArrows__(node_id):
			if node_id not in self.gfx["nodewise_arrow_gfx"]:
				temp_arrow_list = []
				for edge in self.edge_lists[self.id_to_idx[node_id]]:
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
					__updateArrowAlpha__(arrow_gfx, edge.time)
					temp_arrow_list += [arrow_gfx]
				self.gfx["nodewise_arrow_gfx"][node_id] = np.array(temp_arrow_list)
			return

		
		def __updateTime__(val):
			self.curr_time = time_slider.val
			for drawn_node in self.drawn_nodes:
				node_id = int(str(drawn_node.get_url()))
				drawn_node.center = self.nodes[self.id_to_idx[node_id]].getPos(self.curr_time)
			for i in range(self.num_nodes):
				click_status = self.node_click_status[i]
				if click_status == GUI.CLICK_STATUS_ARROWS:
					edge_list = self.edge_lists[i]
					arrow_gfx_list = self.gfx["nodewise_arrow_gfx"][self.nodes[i].id]
					for j in range(len(arrow_data_list)):
						arrow_gfx = arrow_gfx_list[j]
						arrow_time = edge_list[j]
						__updateArrowAlpha__(arrow_gfx, arrow_time)
			self.fig.canvas.draw()
			return
		

		def __updateDetector__(det_label):
			self.curr_detector = det_label
			for drawn_node in self.gfx["node_gfx"]:
				node_id = int(str(drawn_node.get_url()))
				drawn_node.set_ec(self.__getNodeEdgeColor__(node_id))
			print("Mode now: {}  ({}, {})".format(det_label, self.results[det_label].precision(), self.results[det_label].recall()))
			self.fig.canvas.draw()
			return


		def __updateLocValProcedure__(val_label):
			self.curr_val_label = val_label
			if self.gfx["loc_val_radius"] != None:
				self.gfx["loc_val_radius"].remove()
			graph = self.loc_val_data[val_label]["graph"]
			new_val_rad = Circle(
				graph.val_pos, 
				radius=graph.val_rad, 
				linewidth=1, 
				ec=col_loc_val_radius, 
				zorder=4, 
				visible=True, 
				fill=False)
			self.gfx["loc_val_radius"] = new_val_rad
			self.ax.add_patch(new_val_rad)
			initial_det_label = self.loc_val_data[val_label]["detectors"][0]
			__updateDetector__(initial_det_label)
			return
		

		
		def on_pick(event):
			node_id = int(str(event.artist.get_url()))
			__predrawNodewiseArrows__(self, node_id)
			old_click_status = self.gfx["node_click_status"][node_id]
			if old_click_status == GUI.CLICK_STATUS_IDLE:
				self.gfx["node_click_status"][node_id] = GUI.CLICK_STATUS_ARROWS
				for arrow_gfx in self.gfx["nodewise_arrow_gfx"][node_id]:
					arrow_gfx.set_visible(True)
				pval_str = self.__getNodePval__(node_id)
				print("Node: {}, pval={}".format(node_id, pval_str))
			elif old_click_status == GUI.CLICK_STATUS_ARROWS:
				self.gfx["node_click_status"][node_id] = GUI.CLICK_STATUS_IDLE
				for arrow_gfx in self.gfx["nodewise_arrow_gfx"][node_id]:
					arrow_gfx.set_visible(False)
			else:
				print("# erroneous click status {} on node_id {}".format(old_click_status, node_id))
			self.fig.canvas.draw()
			return
		

		__drawNodes__()
		time_slider.on_changed(__updateTime__)
		radio_detector.on_clicked(__updateDetector__)
		radio_loc_val.on_clicked(__updateLocValProcedure__)
				
		self.fig.canvas.mpl_connect("pick_event", on_pick)
		plt.show()