import re
import pandas as pd
import numpy as np
from glob import glob
import networkx as nx
import matplotlib.pyplot as plt
# from functools import reduce
import os
from itertools import combinations
from collections import defaultdict
from p_tqdm import p_map, p_umap
from scipy import sparse

# !conda install -c conda-forge tqdm -y
from tqdm import tqdm

from src.utils import UniqueIdAssigner


class SmaliApp():
    LINE_PATTERN = re.compile('^(\.method.*)|^(\.end method)|^[ ]{4}(invoke-.*)', flags=re.M)
    INVOKE_PATTERN = re.compile(
        "(invoke-\w+)(?:\/range)? {.*}, "     # invoke
        + "(\[*[ZBSCFIJD]|\[*L[\w\/$-]+;)->"   # package
        + "([\w$]+|<init>).+"                 # method
    )

    def __init__(self, app_dir):
        self.app_dir = app_dir
        self.package = app_dir.split('/')[-2]
        self.smali_fn_ls = sorted(glob(
            os.path.join(app_dir, 'smali*/**/*.smali'), recursive=True
        ))
        if len(self.smali_fn_ls) == 0:
            print('Skipping invalid app directory:', self.app_dir)
            return
            raise Exception('Invalid app directory', app_dir)

        self.info = self.extract_info()

    def _extract_line_file(self, fn):
        with open(fn) as f:
            data = SmaliApp.LINE_PATTERN.findall(f.read())
            if len(data) == 0: return None

        data = np.array(data)
        assert data.shape[1] == 3  # 'start', 'end', 'call'

        relpath = os.path.relpath(fn, start=self.app_dir)
        data = np.hstack((data, np.full(data.shape[0], relpath).reshape(-1, 1)))
        return data

    def _assign_code_block(df):
        df['code_block_id'] = (df.start.str.len() != 0).cumsum()
        return df

    def _assign_package_invoke_method(df):
        res = (
            df.call.str.extract(SmaliApp.INVOKE_PATTERN)
            .rename(columns={0: 'invocation', 1: 'library', 2: 'method_name'})
        )
        return pd.concat([df, res], axis=1)

    def extract_info(self):
        agg = [self._extract_line_file(f) for f in self.smali_fn_ls]
        df = pd.DataFrame(
            np.vstack([i for i in agg if i is not None]),
            columns=['start', 'end', 'call', 'relpath']
        )

        df = SmaliApp._assign_code_block(df)
        df = SmaliApp._assign_package_invoke_method(df)

        # clean
        assert (df.start.str.len() > 0).sum() == (df.end.str.len() > 0).sum(), f'Number of start and end are not equal in {self.app_dir}'
        df = (
            df[df.call.str.len() > 0]
            .drop(columns=['start', 'end']).reset_index(drop=True)
        )

        # verify no nans
        extract_nans = df.isna().sum(axis=1)
        assert (extract_nans == 0).all(), f'nan in {extract_nans.values.nonzero()} for {self.app_dir}'
        # self.info.loc[self.info.isna().sum(axis=1) != 0, :]

        return df


class HINProcess():

    def __init__(self, csvs, out_dir, nproc=4):
        self.csvs = csvs
        self.out_dir = out_dir
        self.nproc = nproc
        self.packages = [os.path.basename(csv)[:-4] for csv in csvs]
        self.infos = p_map(HINProcess.csv_proc, csvs, num_cpus=nproc)
        self.prep_ids()

    def prep_ids(self):
        self.API_uid = UniqueIdAssigner()
        for info in self.infos:
            info['api_id'] = self.API_uid.add(*info.api)

        self.APP_uid = UniqueIdAssigner()
        for package in self.packages:
            self.APP_uid.add(package)

    def csv_proc(csv):
        df = pd.read_csv(
            csv, dtype={'method_name': str}, keep_default_na=False
        )
        df['api'] = df.library + '->' + df.method_name
        return df

    def construct_graph_A(self):
        unique_APIs_app = [set(info.api_id) for info in self.infos]
        unique_APIs_all = set.union(*unique_APIs_app)

        A_cols = []
        for unique in unique_APIs_all:
            bag_of_API = [1 if unique in app_set else 0 for app_set in unique_APIs_app]
            A_cols.append(bag_of_API)

        A_mat = np.array(A_cols).T  # shape: (# of apps, # of unique APIs)
        return A_mat

    def _prep_graph_B(info):
        func_pairs = lambda d: list(combinations(d.api_id.unique(), 2))
        edges = pd.DataFrame(
            info.groupby('code_block_id').apply(func_pairs).explode()
            .reset_index(drop=True).drop_duplicates().dropna()
            .values.tolist()
        ).values.T.astype('uint32')
        return edges

    def _prep_graph_P(info):
        func_pairs = lambda d: list(combinations(d.api_id.unique(), 2))
        edges = pd.DataFrame(
            info.groupby('library').apply(func_pairs).explode()
            .reset_index(drop=True).drop_duplicates().dropna()
            .values.tolist()
        ).values.T.astype('uint32')
        return edges

    def _save_interim_BP(Bs, Ps, csvs, nproc):
        p_umap(
            lambda arr, file: np.save(file, arr),
            Bs + Ps,
            [f[:-4] + '.B' for f in csvs] + [f[:-4] + '.P' for f in csvs],
            num_cpus=nproc
        )

    def prep_graph_BP(self, out=True):
        Bs = p_map(HINProcess._prep_graph_B, self.infos, num_cpus=self.nproc)
        Ps = p_map(HINProcess._prep_graph_P, self.infos, num_cpus=self.nproc)
        if out:
            HINProcess._save_interim_BP(Bs, Ps, self.csvs, self.nproc)
        return Bs, Ps

    def _build_coo(arr_ls, shape):
        arr = np.hstack(arr_ls)
        arr = np.hstack([arr, arr[::-1, :]])
        values = np.full(shape=arr.shape[1], fill_value=1, dtype='i1')
        sparse_arr = sparse.coo_matrix(
            (values, (arr[0], arr[1])), shape=shape
        )
        sparse_arr.setdiag(1)
        return sparse_arr

    def construct_graph_BP(self, Bs, Ps):
        shape = (len(self.API_uid), len(self.API_uid))
        B_mat = HINProcess._build_coo(Bs, shape).tocsr()
        P_mat = HINProcess._build_coo(Ps, shape).tocsr()
        return B_mat, P_mat

    def save_matrices(self):
        path = self.out_dir
        np.save(os.path.join(path, 'A'), self.A_mat)
        sparse.save_npz(os.path.join(path, 'B'), self.B_mat)
        sparse.save_npz(os.path.join(path, 'P'), self.P_mat)

    def run(self):
        self.A_mat = self.construct_graph_A()
        Bs, Ps = self.prep_graph_BP()
        self.B_mat, self.P_mat = self.construct_graph_BP(Bs, Ps)
        self.save_matrices()



