import sys
import json

from src.data.get_data import get_data, clean_data

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

    # make the data target
    elif 'data' in targets:
        get_data(**cfg)


    return


if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
