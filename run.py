import sys
import json

from src.data.get_data import get_data, clean_data
from src.features.build_features import build_raw_features, clean_raw_features

DATA_PARAMS = 'config/data-params.json'
TEST_PARAMS = 'config/test-params.json'


def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)

    return param


def main(targets):
    cfg = load_params(DATA_PARAMS)

    # make the clean target
    if 'clean' in targets:
        clean_data(**cfg)
        clean_raw_features(**cfg)
        return

    # make the data target
    if 'data' in targets:
        get_data(**cfg)

    if 'raw_feature' in targets:
        build_raw_features(**cfg)


    return


if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
