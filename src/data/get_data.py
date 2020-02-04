import json
import pandas as pd
import os

import preload
import sample
import decompile


# def sample_random(apps, n=10):
#     """Randomly sample n number of apps from the dataframe"""
#     df = apps.sample(n)
#     return ('https://apkpure.com/' + df.name_slug + '/' + df.package).to_list()

def preload_data(fn):
    """Check if parquet data exists. If not, proceed to download"""
    if not os.path.exists(fn):
        print('Preload file does not exist')
        exit
        # preload.run(data_dir)

    print(f'Reading {fn}')
    apps = pd.read_parquet(fn)
    print('done')
    return apps

def get_data(**config):
    # Check if data_dir exists
    data_dir = config['data_dir']
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    
    if config['preload'] is True:
        fn = os.path.join(data_dir, 'metadata.parquet')
        apps = preload_data(fn)
    else:
        # dynamic sample
        pass


    if config['sampling']['method'] == 'random':
        urls_iter = sample.sample_df_random(apps, config['sampling']['n'])

    decompile.run(data_dir, urls)

if __name__ == "__main__":
    cfg = json.load(open('data-params.json'))
    get_data(**cfg)
