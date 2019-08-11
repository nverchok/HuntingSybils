#    SyPy: A Python framework for evaluating graph-based Sybil detection
#    algorithms in social and information networks.
#
#    Copyright (C) 2013  Yazan Boshmaf
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import matplotlib.pyplot as plt
import networkx as nx
import random
import sypy

class Network:

    def __init__(self, left_region, right_region, name, seed=None, custom_graph=None):
        self.left_region = left_region
        self.right_region = right_region
        self.custom_graph = custom_graph
        self.honest_truth = []
        # self.__check_integrity()

        self.name = name
        self.seed = seed
        if self.seed:
            random.seed(self.seed)

        self.known_honests = []
        self.is_stitched = False
        self.attack_edges = []
        self.__setup_network_graph()

    def reset(self, num_edges):
        if self.custom_graph != None:
            self.graph = self.custom_graph
            self.known_honests = []
            self.is_stitched = True
            return
        self.graph = self.__setup_network_graph()
        self.known_honests = []
        self.is_stitched = False
        self.attack_edges = []
        self.random_pair_stitch(num_edges)

    def get_network_stats(self):
        return sypy.Stats(self.graph)

    def __check_integrity(self):
        if self.left_region.is_sybil == self.right_region.is_sybil:
            raise Exception("Invalid region labels")

        if self.left_region.is_sybil:
            raise Exception("Left region must be honest")

        if nx.number_connected_components(
            self.left_region.graph.structure
        ) != 1:
            raise Exception("Left region has more than one component")

        if nx.number_connected_components(
            self.right_region.graph.structure
        ) != 1:
            raise Exception("Right region has more than one component")

        if not self.left_region.known_honests:
            raise Exception("Known honests not set")

    def __setup_network_graph(self):
        if self.custom_graph != None:
            self.graph = self.custom_graph
            self.known_honests = []
            self.is_stitched = True
            return
        structure = nx.disjoint_union(
            self.left_region.graph.structure,
            self.right_region.graph.structure
        )

        return sypy.CustomGraph(structure)

    def random_pair_stitch(self, num_edges):
        left_nodes = self.left_region.graph.nodes()
        right_nodes = self.right_region.graph.nodes()

        if num_edges > len(left_nodes) * len(right_nodes):
            raise Exception("Too many edges to stitch")

        stitch = []
        while len(stitch) != num_edges:
            edge = (
                random.choice(list(left_nodes)),
                random.choice(list(right_nodes))
            )
            if edge in stitch:
                continue
            stitch.append(edge)

        self.graph.structure = nx.disjoint_union(
            self.left_region.graph.structure,
            self.right_region.graph.structure
        )

        for (left_node, right_node) in stitch:
            edge = (left_node,right_node)
            self.graph.structure.add_edges_from([edge])
            self.attack_edges.append(edge)

        self.known_honests = self.left_region.known_honests
        self.is_stitched = True

    def visualize(self, file_name=None, file_format="pdf"):
        layout = nx.spring_layout(self.graph.structure)

        handles = []
        honest_handle = nx.draw_networkx_nodes(
            self.left_region.graph.structure,
            layout,
            node_size=150,
            node_color="green"
        )
        honest_handle.set_label("Honest")
        handles.append(honest_handle)

        sybil_nodes = range(
            self.left_region.graph.structure.order(),
            self.graph.order()
        )

        sybil_handle = nx.draw_networkx_nodes(
            self.right_region.graph.structure,
            layout,
            nodelist=sybil_nodes,
            node_size=150,
            node_color="red"
        )
        sybil_handle.set_label("Sybil")
        handles.append(sybil_handle)

        known_handle = nx.draw_networkx_nodes(
            self.left_region.graph.structure,
            layout,
            nodelist=self.known_honests,
            node_color="orange",
            node_size=150
        )
        known_handle.set_label("Known")
        handles.append(known_handle)

        nx.draw_networkx_edges(
            self.graph.structure,
            layout,
            edge_color="black",
            alpha=0.5
        )

        nx.draw_networkx_edges(
            self.graph.structure,
            layout,
            edgelist = self.attack_edges,
            edge_color="red",
            alpha=0.5,
            width=5
        )

        labels = [handle.get_label() for handle in handles]
        plt.legend(
            handles,
            labels,
            scatterpoints=1
        )
        plt.title("{0}".format(self.name))
        plt.axis('off')

        if file_name:
            plt.savefig(
                "{0}.{1}".format(file_name, file_format),
                format=file_format
            )
            plt.clf()
        else:
            plt.show()
    
    def set_data(self, original_nodes=None, sybils=None, malicious=None, known_honests=None, initial_sybils=None):
        self.honest_truth = set(self.graph.nodes()) - set(sybils)
        self.known_honests = known_honests
        self.sybils = sybils
        self.malicious = malicious
        self.original_nodes = original_nodes
        self.initial_sybils = initial_sybils
        self.graph = self.custom_graph
        self.is_stitched = True

