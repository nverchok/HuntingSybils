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

    def __init__(self, detector=None, val_node_ids=None, true_syb_ids=None, true_mal_ids=None, pred_syb_ids=None):
        if detector != None:
            self.val_node_ids = set(detector.network.original_nodes)
            self.true_syb_ids = set(detector.network.sybils)
            self.true_mal_ids = set(detector.network.malicious)
            self.pred_hon_ids = set(detector.honests_predicted)
            self.pred_syb_ids = self.val_node_ids - self.pred_hon_ids
            self.initial_sybils = set(detector.network.initial_sybils)
        else:
            self.val_node_ids = val_node_ids
            self.true_syb_ids = true_syb_ids
            self.true_mal_ids = true_mal_ids
            self.pred_syb_ids = pred_syb_ids
            self.pred_hon_ids = self.val_node_ids - self.pred_syb_ids
            self.initial_sybils = set()
        self.confusion_matrix = self.__compute_confusion_matrix__()

    def __compute_confusion_matrix__(self):
        P = len(self.true_syb_ids)
        N = len(self.val_node_ids) - len(self.true_syb_ids) - len(self.true_mal_ids)
        true_syb = self.true_syb_ids
        true_hon = (self.val_node_ids - self.true_syb_ids) - self.true_mal_ids
        pred_syb = self.pred_syb_ids - self.true_mal_ids
        pred_hon = self.pred_hon_ids - self.true_mal_ids

        TN = len(set.intersection(pred_hon,true_hon))
        FN = len(set.intersection(pred_hon,true_syb))
        TP = len(set.intersection(pred_syb,true_syb))
        FP = len(set.intersection(pred_syb,true_hon))
        TPR_mal = len(set.intersection(self.pred_syb_ids,self.true_mal_ids))/len(self.true_mal_ids) if len(self.true_mal_ids) != 0 else 0
        
        confusion_matrix = {
            "N": N,
            "P": P,
            "TN": TN,
            "FN": FN,
            "TP": TP,
            "FP": FP,
            "TPR_mal": TPR_mal
        }
        return confusion_matrix

    def precision(self):
        cm = self.confusion_matrix
        return round((cm["TP"]/max((float)(cm["TP"]+cm["FP"]),1)),3)
    
    def recall(self):
        cm = self.confusion_matrix
        return round((cm["TP"]/max((float)(cm["TP"]+cm["FN"]),1)),3)
    
    def recall_mal(self):
        cm = self.confusion_matrix
        return round(cm["TPR_mal"],3)

    def accuracy(self):
        cm = self.confusion_matrix
        return (cm["TP"] + cm["TN"])/(float)(cm["P"]+cm["N"])

    def sensitivity(self):
        cm = self.confusion_matrix
        return cm["TP"]/(float)(cm["TP"]+cm["FN"])

    def specificity(self):
        cm = self.confusion_matrix
        return cm["TN"]/(float)(cm["FP"]+cm["TN"])

