import os
import sys
from glob import glob
from tqdm import tqdm
import pandas as pd
import shutil
# !pip install multiprocess
from pathos.multiprocessing import ProcessPool
from p_tqdm import p_map, p_umap

import src.utils as utils
from src.features.smali import SmaliApp, HINProcess
from src.features.app_features import FeatureBuilder

# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.linear_model import LogisticRegression
# from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
# from sklearn.metrics import confusion_matrix, f1_score


def is_large_dir(app_dir, size_in_bytes=1e8):
    if utils.get_tree_size(app_dir) > size_in_bytes:
        return True
    return False


def process_app(app_dir, out_dir):
    if is_large_dir(app_dir):
        print(f'Error {out_dir} too big')
        return None
    try:
        app = SmaliApp(app_dir)
        out_path = os.path.join(out_dir, app.package + '.csv')
        app.info.to_csv(out_path, index=None)
        package = app.package
        del app
    except:
        print(f'Error extracting {app_dir}')
        return None
    return package, out_path


def extract_save(in_dir, out_dir, class_i, nproc):
    app_dirs = glob(os.path.join(in_dir, '*/'))

    print(f'Extracting features for {class_i}')

    meta = p_umap(process_app, app_dirs, out_dir, num_cpus=nproc, file=sys.stdout)
    meta = [i for i in meta if i is not None]
    packages = [t[0]for t in meta]
    csv_paths = [t[1]for t in meta]
    return packages, csv_paths


def build_features(**config):
    """Main function of data ingestion. Runs according to config file"""
    # Set number of process, default to 2
    nproc = config['nproc'] if 'nproc' in config.keys() else 2

    labels = {}
    csvs = []
    for cls_i in utils.ITRM_CLASSES_DIRS.keys():
        raw_dir = utils.RAW_CLASSES_DIRS[cls_i]
        itrm_dir = utils.ITRM_CLASSES_DIRS[cls_i]
        packages, csv_paths = extract_save(raw_dir, itrm_dir, cls_i, nproc)
        labels[cls_i] = packages
        csvs += csv_paths

    flatten = lambda ll: [i for j in ll for i in j]
    meta = pd.DataFrame({
        'label': flatten([[k] * len(v) for k, v in labels.items()])
    }, index=flatten(labels.values()))
    meta.to_csv(os.path.join(utils.PROC_DIR, 'meta.csv'))

    hin = HINProcess(csvs, utils.PROC_DIR, nproc=nproc)
    hin.run()


    # # Build API-level features (interim)
    # for class_i in config['data_classes'].keys():
    #     extract_save_raw_class(raw_classes_dirs[class_i], interim_classes_dirs[class_i], class_i, nproc)
    # # Aggregate csv files
    # agg_df, labels = aggregate_raw(interim_classes_dirs)

    # fb = FeatureBuilder(agg_df, labels)
    # proc_dir = os.path.join(data_dir, 'processed')
    # os.mkdir(proc_dir)
    # fb.out.to_csv(os.path.join(proc_dir, 'processed.csv'))

    # lr_f1 = []
    # rf_f1 = []
    # gb_f1 = []
    # for i in range(10):
    #     X_train, X_test, y_train, y_test = train_test_split(
    #         fb.out, fb.labels == 'class1',
    #         test_size=0.3
    #     )
    #     lr = LogisticRegression(solver='liblinear')
    #     lr.fit(X_train, y_train)
    #     lr_f1.append(f1_score(y_test, lr.predict(X_test)))

    #     rf = RandomForestClassifier(n_estimators=10)
    #     rf.fit(X_train, y_train)
    #     rf_f1.append(f1_score(y_test, rf.predict(X_test)))

    #     gb = GradientBoostingClassifier()
    #     gb.fit(X_train, y_train)
    #     gb_f1.append(f1_score(y_test, gb.predict(X_test)))

    # print("Average f1 scores:")
    # print(np.mean(lr_f1), np.mean(rf_f1), np.mean(gb_f1))
    # print("Std of f1 scores:")
    # print(np.std(lr_f1), np.std(rf_f1), np.std(gb_f1))
