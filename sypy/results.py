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

class Results:

    def __init__(self, detector=None, val_node_idxs=None, true_syb_idxs=None, true_mal_idxs=None, pred_syb_idxs=None):
        if detector != None:
            self.val_node_idxs = set(detector.network.original_nodes)
            self.true_syb_idxs = set(detector.network.sybils)
            self.true_mal_idxs = set(detector.network.malicious)
            self.pred_hon_idxs = set(detector.honests_predicted)
            self.pred_syb_idxs = self.val_node_idxs - self.pred_hon_idxs
            self.initial_sybils = set(detector.network.initial_sybils)
        else:
            self.val_node_idxs = val_node_idxs
            self.true_syb_idxs = true_syb_idxs
            self.true_mal_idxs = true_mal_idxs
            self.pred_syb_idxs = pred_syb_idxs
            self.pred_hon_idxs = self.val_node_idxs - self.pred_syb_idxs
            self.initial_sybils = set()
        self.confusion_matrix = self.__compute_confusion_matrix__()

    def __compute_confusion_matrix__(self):
        P = len(self.true_syb_idxs)
        N = len(self.val_node_idxs) - len(self.true_syb_idxs) - len(self.true_mal_idxs)
        true_syb = self.true_syb_idxs
        true_hon = (self.val_node_idxs - self.true_syb_idxs) - self.true_mal_idxs
        pred_syb = self.pred_syb_idxs - self.true_mal_idxs
        pred_hon = self.pred_hon_idxs - self.true_mal_idxs

        TN = len(set.intersection(pred_hon,true_hon))
        FN = len(set.intersection(pred_hon,true_syb))
        TP = len(set.intersection(pred_syb,true_syb))
        FP = len(set.intersection(pred_syb,true_hon))
        
        confusion_matrix = {
            "N": N,
            "P": P,
            "TN": TN,
            "FN": FN,
            "TP": TP,
            "FP": FP
        }
        return confusion_matrix

    def precision(self):
        cm = self.confusion_matrix
        return round((cm["TP"]/max((float)(cm["TP"]+cm["FP"]),1)),3)
    
    def recall(self):
        cm = self.confusion_matrix
        return round((cm["TP"]/max((float)(cm["TP"]+cm["FN"]),1)),3)

    def accuracy(self):
        cm = self.confusion_matrix
        return (cm["TP"] + cm["TN"])/(float)(cm["P"] + cm["N"])

    def sensitivity(self):
        cm = self.confusion_matrix
        return cm["TP"]/(float)(cm["TP"]+cm["FN"])

    def specificity(self):
        cm = self.confusion_matrix
        return cm["TN"]/(float)(cm["FP"]+cm["TN"])

