import os
import shutil
from glob import glob
import random

import src.data.preload as preload
import src.data.sampling as sampling
import src.data.decompile as decompile


def prep_dir(data_dir, data_classes):
    """Prepare necessary directory structure inside data_dir"""
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    
    raw_dir = os.path.join(data_dir, 'raw')
    interim_dir = os.path.join(data_dir, 'interim')
    raw_classes_dirs = {
        class_i: os.path.join(raw_dir, class_i)
        for class_i in data_classes.keys()
    }
    interim_classes_dirs = {
        class_i: os.path.join(interim_dir, class_i)
        for class_i in data_classes.keys()
    }

    for dir_i in [raw_dir, interim_dir] + \
                 list(raw_classes_dirs.values()) + \
                 list(interim_classes_dirs.values()):
        if not os.path.exists(dir_i):
            os.mkdir(dir_i)

    return raw_dir, interim_dir, raw_classes_dirs, interim_classes_dirs

# def 


def get_data(**config):
    """Main function of data ingestion. Runs according to config"""
    data_dir = config['data_dir']
    raw_dir, interim_dir, raw_classes_dirs, interim_classes_dirs = \
        prep_dir(data_dir, config['data_classes'])

    # Set number of process, default to 2
    nproc = 2
    if 'nproc' in config.keys():
        nproc = config['nproc']

    app_dirs = {}

    # Data pipeline
    for class_i, class_i_config in config['data_classes'].items():

        # Stage 0: sampling, gives iterator
        if class_i_config['stage'] in ['sampling']:
            apk_jobs = []  # [(url_iter, n),..]
            if class_i_config['apkpure_preload_metadata_fp']:  # preload
                raise NotImplementedError
            else:  # dynamic sampling
                sitemaps_by_cat = sampling.construct_categories()
                if class_i_config['sampling']['method'] == 'url':
                    apk_jobs.append(
                        (iter(class_i_config['sampling']['urls']), None)
                    )
                elif class_i_config['sampling']['method'] == 'random':
                    n = class_i_config['sampling']['n']
                    apk_jobs.append(
                        (sampling.dynamic_random(sitemaps_by_cat), n)
                    )
                elif class_i_config['sampling']['method'] == 'category':
                    for cat, n in class_i_config['sampling']['category_targets'].items():
                        apk_jobs.append(
                            (sampling.dynamic_sample_category(sitemaps_by_cat, cat), n)
                        )

        # Stage 1: get apks from iterators and decompile
        if class_i_config['stage'] in ['sampling', 'apk']:
            if class_i_config['stage'] == 'apk':
                raise NotImplementedError
            # Extract raw features
            app_dir_ls = []
            for job_iter, job_n in apk_jobs:
                ls = decompile.decompile(raw_classes_dirs[class_i], job_iter, job_n)
                app_dir_ls += ls
            app_dirs[class_i] = app_dir_ls
            continue

        # Stage 2: decompile
        if class_i_config['stage'] in ['apk', 'smali']:
            if class_i_config['origin'] == 'external':
                if class_i_config['external_structure'] == 'flat':
                    app_dir_ls = glob(
                        os.path.join(class_i_config['external_dir'], '*')
                    )
                    assert class_i_config['sampling']['method'] == 'random'
                    app_dir_ls = random.sample(
                        app_dir_ls, class_i_config['sampling']['n']
                    )
                elif class_i_config['external_structure'] == 'by_category_variety':
                    app_dir_ls = glob(
                        os.path.join(class_i_config['external_dir'], '*', '*', '*')
                    )
                    if class_i_config['sampling']['method'] == 'random':
                        app_dir_ls = random.sample(
                            app_dir_ls, class_i_config['sampling']['n']
                        )
                    else:
                        raise NotImplementedError
                else:
                    raise NotImplementedError

                print("Copying apps from external directory")
                for app_dir in app_dir_ls:
                    app_package = os.path.basename(app_dir)
                    shutil.copytree(
                        app_dir,
                        os.path.join(raw_classes_dirs[class_i], app_package)
                    )
            else:
                raise NotImplementedError


def clean_raw(**config):
    data_dir = config['data_dir']
    raw_dir = os.path.join(data_dir, 'raw')
    for dir_i in [raw_dir]:
        shutil.rmtree(dir_i, ignore_errors=True)
