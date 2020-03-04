import os
import shutil
from collections import defaultdict

RAW_DIR = None
ITRM_DIR = None
RAW_CLASSES_DIRS = None
ITRM_CLASSES_DIRS = None


def prep_dir(**cfg):
    """Prepare necessary directory structure inside data_dir"""

    global RAW_DIR
    global ITRM_DIR
    global RAW_CLASSES_DIRS
    global ITRM_CLASSES_DIRS

    if not os.path.exists(cfg['data_dir']):
        os.mkdir(cfg['data_dir'])

    RAW_DIR = os.path.join(cfg['data_dir'], cfg['data_subdirs']['raw'])
    ITRM_DIR = os.path.join(cfg['data_dir'], cfg['data_subdirs']['interim'])
    data_classes = cfg['data_classes']

    RAW_CLASSES_DIRS = {
        class_i: os.path.join(RAW_DIR, class_i)
        for class_i in data_classes.keys()
    }
    ITRM_CLASSES_DIRS = {
        class_i: os.path.join(ITRM_DIR, class_i)
        for class_i in data_classes.keys()
    }

    dir_ls = [RAW_DIR, ITRM_DIR] + list(RAW_CLASSES_DIRS.values()) + \
        list(ITRM_CLASSES_DIRS.values())

    for dir_i in dir_ls:
        if not os.path.exists(dir_i):
            os.mkdir(dir_i)


def clean_raw(**cfg):
    data_dir = cfg['data_dir']
    raw_dir = os.path.join(data_dir, cfg['data_subdirs']['raw'])
    shutil.rmtree(raw_dir, ignore_errors=True)


def clean_features(**cfg):
    data_dir = cfg['data_dir']
    itrm_dir = os.path.join(data_dir, cfg['data_subdirs']['interim'])
    shutil.rmtree(itrm_dir, ignore_errors=True)


class UniqueIdAssigner():
    def __init__(self):
        self.uid_lookup = defaultdict(lambda: len(self.uid_lookup))
        self.value_by_id = lambda: list(self.uid_lookup.keys())

    def add(self, *values):
        uids = [self.uid_lookup[v] for v in values]
        return uids

    def __getitem__(self, k):
        return self.value_by_id()[k]

    def __len__(self):
        return len(self.uid_lookup)
