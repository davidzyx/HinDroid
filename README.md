# HinDroid

![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/davidzz/hindroid)

This repository is a rough implementation of the [Hindroid](https://www.cse.ust.hk/~yqsong/papers/2017-KDD-HINDROID.pdf) model (DOI:[10.1145/3097983.3098026](https://doi.org/10.1145/3097983.3098026)). More efforts are spent building the data pipeline than replicating the entire paper to each detail. Only PID {1,2,3,5} referenced in Table 3 of the paper are implemented here.

The task of interest here is to effectively classify Android applications as benign or malicious. Malicious applications pose security threats to the public as they often intentionally obtain sensitive information from the victim's phone. Our intent is to replicate the findings presented in this paper by sourcing the data by ourselves and then applying machine learning techniques mentioned on the data we acquired.

## Docker Image

<https://hub.docker.com/repository/docker/davidzz/hindroid>

More usage details will be added. For more information, please refer to the reports in `./writeups`.

## Config file usage

`config/data-params.json`

```json
{
    "nproc": 4,
    "data_dir": "/Volumes/Lexar/HinDroid/data",
    "data_subdirs": {
        "raw": "raw",
        "interim": "interim",
        "processed": "processed"
    },
    "data_classes": {
        "class0": {
            "stage": "apkpure",
            "sampling": {
                "method": "category",
                "category_targets": {
                    "communication": 2,
                    "tools": 2
                }
            }
        },
        "class1": {
            "stage": "apkpure",
            "sampling": {
                "method": "random",
                "n": 2
            }
        },
        "class2": {
            "stage": "url",
            "sampling": {
                "method": "url",
                "url_targets": ["https://apkpure.com/elearning-py-2014/com.Facultad.Learning"]
            }
        },
        "class3": {
            "stage": "apk",
            "external_dir": "test/tools",
            "external_structure": "flat",
            "sampling": {
                "method": "random",
                "n": 1
            }
        },
        "class4": {
            "stage": "smali",
            "external_dir": "/Volumes/exf/smali",
            "external_structure": "flat",
            "sampling": {
                "method": "random",
                "n": 1
            }
        }
    }
}

```
