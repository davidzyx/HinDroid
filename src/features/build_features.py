import os
from glob import glob
from tqdm import tqdm
import shutil
# !pip install multiprocess
from multiprocess import Pool

from src.features.smali_features import SmaliApp
from src.data.get_data import prep_dir

def extract_save_raw(apps_dir, out_dir, nproc, label=False):
    app_dirs = glob(os.path.join(apps_dir, '*/'))

    if label:
        raise NotImplementedError

    with Pool(nproc) as p:
        smali_apps = list(tqdm(
            p.imap_unordered(SmaliApp, app_dirs), total=len(app_dirs)
        ))
    
    print('Saving raw features')
    for app in smali_apps:
        out_path = os.path.join(out_dir, app.package + '.csv')
        app.info.to_csv(out_path, index=None)


def build_raw_features(**config):
    """Main function of data ingestion. Runs according to config file"""
    data_dir = config['data_dir']
    prep_dir(data_dir)

    # Set number of process
    if 'nproc' not in config:
        config['nproc'] = 2
    
    raw_dir = os.path.join(data_dir, 'raw')
    raw_benign_apps_dir = os.path.join(raw_dir, 'benign_apps')
    proc_dir = os.path.join(data_dir, 'processed')
    proc_benign_dir = os.path.join(proc_dir, 'benign')
    proc_malicious_dir = os.path.join(proc_dir, 'malicious')

    extract_save_raw(raw_benign_apps_dir, proc_benign_dir, config['nproc'], label=False)


def clean_raw_features(**config):
    data_dir = config['data_dir']
    proc_dir = os.path.join(data_dir, 'processed')
    for dir_i in [proc_dir]:
        shutil.rmtree(dir_i, ignore_errors=True)