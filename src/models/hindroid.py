import pandas as pd
import numpy as np
from scipy import sparse
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

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

    def _evaluate(self, X_train, X_test, y_train, y_test):
        results = []
        for mp, kernel, svm in zip(self.metapaths, self.kernels, self.svms):
            print(f'Evaluating {mp}...', end='', file=sys.stderr, flush=True)
            gram_train = kernel(X_train, X_train)
            svm.fit(gram_train, y_train)
            train_acc = svm.score(gram_train, y_train)

            gram_test = kernel(X_test, X_train)
            y_pred = svm.predict(gram_test)
            test_acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

            results.append(pd.Series({
                'train_acc': train_acc, 'test_acc': test_acc, 'f1': f1,
                'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn
            }))
            print('done', file=sys.stderr)

        return results

    def evaluate(self, X, y, test_size=0.33):
        X = sparse.csr_matrix(X, dtype='uint32')
        X_train, X_test, y_train, y_test = \
            train_test_split(X, y, test_size=test_size)

        results = self._evaluate(X_train, X_test, y_train, y_test)
        results = [res.rename(mp) for res, mp in zip(results, self.metapaths)]
        results = pd.DataFrame(results)
        results.index.name = 'metapath'
        return results


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
    hin = HinDroid(B_mat, P_mat, metapaths)
    results = hin.evaluate(A_mat, labels)
    print(results)
    out_csv = os.path.join(PROC_DIR, 'results.csv')
    results.to_csv(out_csv)

    # runs = []
    # for i in range(10):
    #     results = hin.evaluate(A_mat, labels)
    #     print(results)
    #     runs.append(results)
    #     out_csv = os.path.join(PROC_DIR, f'results_{i}.csv')
    #     results.to_csv(out_csv)
