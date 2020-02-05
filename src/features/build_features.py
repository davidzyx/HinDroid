import re
import pandas as pd
import numpy as np
from glob import glob
import networkx as nx
import matplotlib.pyplot as plt
# from functools import reduce
import os
from itertools import combinations

# !conda install -c conda-forge tqdm -y
from tqdm import tqdm
# !pip install multiprocess
from multiprocess import Pool


class SmaliApp():
    INVOKE_PATTERN = (
        "(invoke-\w+)(?:\/range)? {.*}, "     # invoke
        + "(\[*[ZBSCFIJD]|\[*L[\w\/$-]+;)->"   # package
        + "([\w$]+|<init>).+"                 # method
    )
    
    def __init__(self, app_dir):
        self.app_dir = app_dir
        self.package = app_dir.split('/')[-2]
        self.smali_fn_ls = sorted(glob(os.path.join(app_dir, 'smali*/**/*.smali'), recursive=True))
        if len(self.smali_fn_ls) == 0:
            raise Exception('Invalid app directory')

        self.info = self.extract_info()

    def _extract_line_file(fn):
        with open(fn) as f:
            pattern = '(^\.method.*)|(^\.end method)|(invoke-.*)'
            data = re.findall(pattern, f.read())
            if len(data) == 0: return pd.DataFrame()
        
        data = np.array(data)
        assert data.shape[1] == 3
        
        df = pd.DataFrame(
            np.array(data),
            columns=['start', 'end', 'call']
        )
        df['filename'] = fn

        return df
    
    def _assign_code_block(df):
        df['code_block_id'] = (df.start.str.len() != 0).cumsum()
        return df
    
    def _assign_package_invoke_method(df):
        res = (
            df.call.str.extract(SmaliApp.INVOKE_PATTERN)
            .rename(columns={0: 'invocation', 1: 'package', 2: 'method_name'})
        )
        return pd.concat([df, res], axis=1)
        
    
    def extract_info(self):
        agg = [SmaliApp._extract_line_file(f) for f in self.smali_fn_ls]
        df = pd.concat(agg, ignore_index=True)        
        
        df = SmaliApp._assign_code_block(df)
        df = SmaliApp._assign_package_invoke_method(df)
        df['api_id'] = df.groupby(['package', 'method_name']).ngroup()
#         self.info = df

        # clean
        assert (df.start.str.len() > 0).sum() == (df.end.str.len() > 0).sum()
        df = df[df.call.str.len() > 0].drop(columns=['start', 'end']).reset_index(drop=True)
        
        # verify no nans
        extract_nans = df.isna().sum(axis=1)
#         df.loc[df.isna().sum(axis=1) > 0, :].call.values
        assert (extract_nans == 0).all(), f'nan in {extract_nans.values.nonzero()}'

#         self.info = df
        return df

class SmaliHIN():
    
    def __init__(self, apps_dir, nproc=8):
        self.app_dirs = glob(os.path.join(apps_dir, '*/'))[:8]
        with Pool(nproc) as p:
            smali_apps = list(tqdm(p.imap_unordered(SmaliApp, self.app_dirs), total=len(self.app_dirs)))
        self.apps = {app.package: app for app in smali_apps}
        self.packages = list(self.apps.keys())
        
    def construct_graph_A(self):
        unique_APIs_app = [set(app.info.package + '->' + app.info.method_name) for app in self.apps.values()]
        unique_APIs_all = set.union(*unique_APIs_app)
        
        A_cols = []
        for unique in unique_APIs_all:
            bag_of_API = [1 if unique in app_set else 0 for app_set in unique_APIs_app]
            A_cols.append(bag_of_API)
            
        A_mat = np.array(A_cols).T
        # shape: (# of apps, # of unique APIs)
        self.A_mat = A_mat
        return self.A_mat
        