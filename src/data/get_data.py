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


def get_data(**config):
    data_dir = config['data_dir']
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    
    if config['preload'] is True:
        apps_fn = os.path.join(data_dir, 'metadata.parquet')
        assert os.path.exists(apps_fn)
        print(f'Reading {apps_fn}')
        apps = pd.read_parquet(apps_fn)
    else:
        pass
        preload.run(data_dir)

    if config['sampling']['method'] == 'random':
        urls = sample.sample_random(apps, config['sampling']['n'])

    decompile.run(data_dir, urls)

if __name__ == "__main__":
    cfg = json.load(open('data-params.json'))
    get_data(**cfg)
