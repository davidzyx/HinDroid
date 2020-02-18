import sys
import json

from src.data.get_data import get_data, clean_raw
from src.features.build_features import build_features, clean_features

DATA_PARAMS = 'config/data-params.json'
TEST_PARAMS = 'config/test-params.json'


def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)

    return param


def main(targets):
    # make the data target
    if 'data' in targets:
        cfg = load_params(DATA_PARAMS)
    elif 'data-test' in targets:
        cfg = load_params(TEST_PARAMS)
    else:
        return

    # make the clean target
    if 'clean' in targets:
        clean_raw(**cfg)
        clean_features(**cfg)
        return

    # make the data target
    if 'ingest' in targets:
        get_data(**cfg)

    if 'process' in targets:
        get_data(**cfg)
        build_features(**cfg)


    return


if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
