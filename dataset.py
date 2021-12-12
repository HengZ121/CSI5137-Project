import csv
import torch
import numpy as np
import pandas as pd
import torch.utils.data as data
from transformers import BertTokenizer, BertModel, BertForMaskedLM

class Dataset(data.Dataset):

    # A dictionary that stores the descriptions of labels, order of entires is used to create bitmaps
    labels = {

        "A"  : "Description of shoftware's accessibility for a user at a given point in time. Expressed as a probability percentage"
        "FT" : "Property that enables software to continue operating properly in the event of the failure of faults within its components",
        "L"  : "Requirement that limits the risk for legal disputes between a software provider and their users, and the compliance with laws",
        "LF" : "Aspects of software's design, including elements, the behavior of elements, a non-graphical user interface, and API not related to functional properties",
        "MN" : "Ease with which a software can be maintained for learning from the past in order to improve the ability or reliability of software",
        "O"  : "Ability to keep the software in a safe and reliable functioning condition, according to pre-defined operational requirements.",
        "PE" : "Amount of useful work accomplished by a software, estimated in terms of accuracy, efficiency and speed of executing",
        "PO" : "Usability of the same software in different environments, also the key issue for development cost reduction",
        "SC" : "Property of software to handle increasing (or decreasing)c amount of workload by adding resources to the software",
        "SE" : "Protection of software from information disclosure, theft of or damage to their data, also from the disruption or misdirection of its services",
        "US" : "Degree to which a software can achieve quantified objectives with effectiveness, efficiency, and satisfaction in a quantified context of use",
        "F"  : "Description of the service that the software must offer. It describes a software or its component."
    }

    def __init__(self, opt):
        '''
        attributes:
        opt            :   parser specified in train.py
        text_corpus    :   text corpus, string array
        text_vectors   :   ***vectors that represent text in corpus, 长度为num_hidden_layers的(batch_size， sequence_length，hidden_size)的Tensor.列表
        p_labels       :   ***parent labels text in corpus, array of bitmaps (2d array)    [NFR, F]
        c_labels       :   ***child labels text in corpus, array of bitmaps (2d array)     [F, A, FT, L, LF, MN, O, PE, PO, SC, SE, US]
        input_ids      :   arraies of words' (in text) ids in dictionary, array of tensors

        sequence_classification_tokenizer is used internally only for tokenization
        '''
        self.opt = opt
        self.text_corpus = []
        self.input_ids = []
        self.token_type_ids = []
        self.p_labels = []
        self.c_labels = []
        self.sequence_classification_tokenizer = torch.hub.load('huggingface/pytorch-transformers', 'tokenizer',
                                                           'bert-base-cased-finetuned-mrpc')

        df = pd.read_csv(self.opt.dataset, delimiter=';', header=0, encoding='utf8',
                         names=['number', 'ProjectID', 'RequirementText', 'class', 'NFR', 'F', 'A', 'FT', 'L', 'LF',
                                'MN', 'O', 'PE', 'PO', 'SC', 'SE', 'US'])
        df = df.dropna()
        df = df.sample(frac=1, axis=0, random_state=904727489)
        self.text_corpus = df.RequirementText.tolist()
        labels = ['NFR', 'F', 'A', 'FT', 'L', 'LF',
                                'MN', 'O', 'PE', 'PO', 'SC', 'SE', 'US']
        for index, row in df.iterrows():
            temp_p = []
            temp_c = []
            for i in labels[0:2]:
                temp_p.append(float(row[i]))
            for i in labels[2:]:
                temp_c.append(float(row[i]))
            self.p_labels.append(temp_p)
            flag = 0.
            if temp_p[1] == 1:
                flag = 1.
            temp_c.append(flag)
            self.c_labels.append(temp_c)

        for text in self.text_corpus:
            # Get encoding info for each text in corpus along with every labels
            encodes = self.sequence_classification_tokenizer.encode_plus(text)

            tokens_tensor = encodes['input_ids']
            self.input_ids.append(tokens_tensor)
            self.token_type_ids.append(encodes['token_type_ids'])



    def __getitem__(self, index):
        '''
        @param: index: int, location of data instance
        @return: input_ids, parent_label, child_label, and BERT vector of a data instance at specified location
                   ^ this is the array of words' id in dictionary
        '''
        #Get quantity of children labels are desired in classification
        clabel_nb = self.opt.clabel_nb

        input_ids = self.input_ids[index]
        parent_label = self.p_labels[index]
        child_label = self.c_labels[index][0:clabel_nb]
        token_type_ids = self.token_type_ids[index]

        if len(input_ids) < self.opt.sen_len:
            input_ids = np.append(input_ids, [0 for i in range(self.opt.sen_len - len(input_ids))])

        #print('-->',len(torch.tensor(input_ids[0:self.opt.sen_len])))
        return torch.tensor(input_ids[0:self.opt.sen_len]), torch.tensor(parent_label), torch.tensor(child_label)




    def __len__(self):
        '''
        @return: the shape of vector, tuple (quantity of data, length of vectors)
        '''
        return len(self.text_corpus)



    def getLabelDes(self):
        '''
        @return array of tensor (representing label descriptions based on their tokens' ids in the dictionary)
        '''
        #Get quantity of children labels are desired in classification
        clabel_nb = self.opt.clabel_nb

        res = []
        counter = 0
        max_d = -1
        for label in self.labels:
            if counter == clabel_nb:
                break
            counter += 1
            des = self.sequence_classification_tokenizer.encode_plus(self.labels[label])['input_ids']

            max_d = max(max_d, len(des))
        counter = 0
        for label in self.labels:
            if counter == clabel_nb:
                break
            counter += 1
            des = self.sequence_classification_tokenizer.encode_plus(self.labels[label])['input_ids']

            if len(des) < max_d:
                des = np.append(des, [0 for i in range(max_d - len(des))])
            res.append(des)

        return torch.tensor(res)

'''
For Testing Purpose:

def main():

if __name__ == "__main__":
    main()
'''