import os
from glob import glob
from tqdm import tqdm
import pandas as pd
import shutil
# !pip install multiprocess
from multiprocess import Pool

from src.features.smali import SmaliApp
from src.data.get_data import prep_dir
from src.features.app_features import FeatureBuilder

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import confusion_matrix, f1_score

def extract_save_raw_class(raw_dir, interim_dir, class_i, nproc):
    app_dirs = glob(os.path.join(raw_dir, '*/'))

    print(f'Extracting features for {class_i}')
    with Pool(nproc) as p:
        smali_apps = list(tqdm(
            p.imap_unordered(SmaliApp, app_dirs), total=len(app_dirs)
        ))

    print(f'Saving raw features for {class_i}')
    for app in tqdm(smali_apps):
        out_path = os.path.join(interim_dir, app.package + '.csv')
        app.info.to_csv(out_path, index=None)

def aggregate_raw(interim_classes_dirs):
    labels = {}
    class_dfs = []
    for class_i, interim_dir in interim_classes_dirs.items():
        csv_ls = glob(os.path.join(interim_dir, '*.csv'))
        app_dfs = []

        print(f'Reading csv files for {class_i}')
        for csv in tqdm(csv_ls):
            app_df = pd.read_csv(csv)
            app_package = os.path.basename(csv)[:-4]
            labels[app_package] = class_i
            app_df['package'] = app_package
            app_dfs.append(app_df)

        class_i_df = pd.concat(app_dfs, ignore_index=True)
        class_i_df['class'] = class_i
        class_dfs.append(class_i_df)

    df = pd.concat(class_dfs, ignore_index=True)
    return df, labels

def build_features(**config):
    """Main function of data ingestion. Runs according to config file"""
    data_dir = config['data_dir']
    raw_dir, interim_dir, raw_classes_dirs, interim_classes_dirs = \
        prep_dir(data_dir, config['data_classes'])

    # Set number of process, default to 2
    nproc = 2
    if 'nproc' in config.keys():
        nproc = config['nproc']

    # Build API-level features (interim)
    for class_i in config['data_classes'].keys():
        extract_save_raw_class(raw_classes_dirs[class_i], interim_classes_dirs[class_i], class_i, nproc)
    # Aggregate csv files
    agg_df, labels = aggregate_raw(interim_classes_dirs)
    
    fb = FeatureBuilder(agg_df, labels)
    proc_dir = os.path.join(data_dir, 'processed')
    os.mkdir(proc_dir)
    fb.out.to_csv(os.path.join(proc_dir, 'processed.csv'))

    lr_f1 = []
    rf_f1 = []
    gb_f1 = []
    for i in range(10):
        X_train, X_test, y_train, y_test = train_test_split(
            fb.out, fb.labels == 'class1',
            test_size=0.3
        )
        lr = LogisticRegression(solver='liblinear')
        lr.fit(X_train, y_train)
        lr_f1.append(f1_score(y_test, lr.predict(X_test)))
        
        rf = RandomForestClassifier(n_estimators=10)
        rf.fit(X_train, y_train)
        rf_f1.append(f1_score(y_test, rf.predict(X_test)))

        gb = GradientBoostingClassifier()
        gb.fit(X_train, y_train)
        gb_f1.append(f1_score(y_test, gb.predict(X_test)))

    print("Average f1 scores:")
    print(np.mean(lr_f1), np.mean(rf_f1), np.mean(gb_f1))
    print("Std of f1 scores:")
    print(np.std(lr_f1), np.std(rf_f1), np.std(gb_f1))
    


def clean_features(**config):
    data_dir = config['data_dir']
    interim_dir = os.path.join(data_dir, 'interim')
    proc_dir = os.path.join(data_dir, 'processed')
    for dir_i in [interim_dir, proc_dir]:
        shutil.rmtree(dir_i, ignore_errors=True)