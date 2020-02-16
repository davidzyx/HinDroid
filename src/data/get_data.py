import json
import os
import shutil

import src.data.preload as preload
import src.data.sampling as sampling
import src.data.decompile as decompile


def prep_dir(data_dir):
    """Prepare necessary directory structure inside data_dir"""
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    
    raw_dir = os.path.join(data_dir, 'raw')
    raw_benign_apps_dir = os.path.join(raw_dir, 'benign_apps')
    proc_dir = os.path.join(data_dir, 'processed')
    proc_benign_dir = os.path.join(proc_dir, 'benign')
    proc_malicious_dir = os.path.join(proc_dir, 'malicious')

    for dir_i in [raw_dir, raw_benign_apps_dir, 
                  proc_dir, proc_benign_dir, proc_malicious_dir]:
        if not os.path.exists(dir_i):
            os.mkdir(dir_i)


def get_data(**config):
    """Main function of data ingestion. Runs according to config file"""
    data_dir = config['data_dir']
    prep_dir(data_dir)

    # Set number of process
    if 'nproc' not in config:
        config['nproc'] = 2

    # preloaded ingestion
    raw_dir = os.path.join(data_dir, 'raw')
    raw_benign_apps_dir = os.path.join(raw_dir, 'benign_apps')

    if config['preload'] is True or 'preload_fp' in config.keys():
        if 'preload_fp' in config.keys():
            apps = preload.load_data(data_dir, config['nproc'], config['preload_fp'])
        else:
            apps = preload.load_data(data_dir, config['nproc'])


        if config['sampling']['method'] == 'random':
            urls_iter = sampling.df_random(apps)
        elif config['sampling']['method'] == 'category':
            raise NotImplementedError

    else:  # dynamic ingestion
        sitemaps_by_cat = sampling.construct_categories()

        if config['sampling']['method'] == 'random':
            urls_iter = sampling.dynamic_random(sitemaps_by_cat)
        elif config['sampling']['method'] == 'category':
            for cat, n in config['sampling']['category_targets'].items():
                urls_iter = sampling.dynamic_sample_category(sitemaps_by_cat, cat)
                decompile.run(raw_benign_apps_dir, urls_iter, n)

            return

    decompile.run(raw_benign_apps_dir, urls_iter, config['sampling']['n'])

def clean_data(**config):
    data_dir = config['data_dir']
    raw_dir = os.path.join(data_dir, 'raw')
    proc_dir = os.path.join(data_dir, 'processed')
    for dir_i in [raw_dir, proc_dir]:
        shutil.rmtree(dir_i,ignore_errors=True)
