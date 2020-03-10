import pandas as pd
import numpy as np
from scipy import sparse
import os
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from tqdm import tqdm

import src.utils as utils


class HinDroid():
    def __init__(self, B_mat, P_mat, metapaths):
        self.B_mat = B_mat
        self.P_mat = P_mat
        self.metapaths = metapaths
        self.kernels = self.construct_kernels(metapaths)
        self.svms = [SVC(kernel='precomputed') for mp in metapaths]

    def _kernel_func(self, metapath):
        B_mat = self.B_mat
        P_mat = self.P_mat
        if metapath == 'AA':
            f = lambda X, Y: np.dot(X, Y.T)
        elif metapath == 'ABA':
            f = lambda X, Y: np.dot(X, B_mat).dot(Y.T)
        elif metapath == 'APA':
            f = lambda X, Y: np.dot(X, P_mat).dot(Y.T)
        elif metapath == 'APBPA':
            f = lambda X, Y: np.dot(X, P_mat).dot(B_mat).dot(P_mat).dot(Y.T)
        else:
            raise NotImplementedError

        return lambda X, Y: f(X, Y).todense()

    def construct_kernels(self, metapaths):
        kernels = []
        for mp in metapaths:
            kernels.append(self._kernel_func(mp))
        return kernels

    def train(self, X, y):
        accs = []
        for i in tqdm(range(len(self.kernels))):
            gram_train = self.kernels[i](X, X)
            self.svms[i].fit(gram_train, y)
            accs.append(self.svms[i].score(gram_train, y))
        return accs

    def test(self, X_test, X_train, y):
        accs = []
        for i in tqdm(range(len(self.kernels))):
            gram_test = self.kernels[i](X_test, X_train)
            accs.append(self.svms[i].score(gram_test, y))
        return accs

    def evaluate(self, X, y, test_size=0.33):
        X = sparse.csr_matrix(X, dtype='uint64')
        X_train, X_test, y_train, y_test = \
            train_test_split(X, y, test_size=test_size)

        training_accs = self.train(X_train, y_train)
        testing_accs = self.test(X_test, X_train, y_test)

        return pd.DataFrame({
            'kernels': self.metapaths,
            'train_acc': training_accs,
            'test_acc': testing_accs
        })


def run(**config):
    PROC_DIR = utils.PROC_DIR
    A_mat, B_mat, P_mat = [
        sparse.load_npz(os.path.join(PROC_DIR, mat))
        for mat in ['A.npz', 'B.npz', 'P.npz']
    ]

    meta_fp = os.path.join(PROC_DIR, 'meta.csv')
    meta = pd.read_csv(meta_fp, index_col=0)
    print(meta.label.value_counts())
    labels = (meta.label == 'class1').astype(int).values

    metapaths = ['AA', 'APA', 'ABA', 'APBPA']
    out_csv = os.path.join(PROC_DIR, 'results.csv')
    hin = HinDroid(B_mat, P_mat, metapaths)
    results = hin.evaluate(A_mat, labels)
    print(results)
    results.to_csv(out_csv, index=None)
