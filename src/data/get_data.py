import os
import shutil
from glob import glob
import random

import src.utils as utils
import src.data.preload as preload
import src.data.sampling as sampling
import src.data.decompile as apktool


class IngestionPipeline():
    def __init__(self, category, n, out_dir, nproc):
        self.n_remaining = n
        self.out_dir = out_dir
        self.nproc = nproc
        self.url_iter = self.init_sample_iter(category)
        self.run()

    def init_sample_iter(self, category):
        sitemaps_by_cat = sampling.construct_categories()
        if category == 'random':
            return sampling.dynamic_random(sitemaps_by_cat)
        else:
            return sampling.dynamic_category(sitemaps_by_cat, category)

    def step_download_apks(self, url_iter):
        """Pipeline block: Download apks from url iterators to out directory"""
        jobs = [next(url_iter) for _ in range(self.n_remaining)]
        apk_fps = apktool.mt_download_apk(jobs, self.out_dir, self.nproc)
        self.n_failed += sum(1 for i in apk_fps if i is None)
        return [i for i in apk_fps if i is not None]

    def step_decompile_apks(self, apk_fps):
        apk_dirs = apktool.decompile_apks(apk_fps, self.out_dir, self.nproc)
        return apk_dirs

    def run(self):
        while self.n_remaining > 0:
            self.n_failed = 0
            apk_fps = self.step_download_apks(self.url_iter)
            smali_dirs = self.step_decompile_apks(apk_fps)
            self.n_remaining = self.n_failed


def run_pipeline(data_cfg, nproc):
    for cls_i, cls_i_cfg in data_cfg.items():
        out_dir = utils.RAW_CLASSES_DIRS[cls_i]
        if cls_i_cfg['stage'] == "apkpure":
            sampling_cfg = cls_i_cfg['sampling']
            if sampling_cfg['method'] == 'random':
                IngestionPipeline('random', sampling_cfg['n'], out_dir, nproc)
            elif sampling_cfg['method'] == 'category':
                for target, n in sampling_cfg['category_targets'].items():
                    IngestionPipeline(target, n, out_dir, nproc)
                    # break
            else: raise NotImplementedError
        else: raise NotImplementedError




def get_data(**config):
    """Main function of data ingestion. Runs according to config"""
    # Set number of process, default to 2
    nproc = config['nproc'] if 'nproc' in config.keys() else 2

    run_pipeline(config['data_classes'], nproc)


    # # Data pipeline
    # for class_i, class_i_config in config['data_classes'].items():

    #     # Stage 0: sampling, gives iterator
    #     if class_i_config['stage'] in ['sampling']:
    #         apk_jobs = []  # [(url_iter, n),..]
    #         if class_i_config['apkpure_preload_metadata_fp']:  # preload
    #             raise NotImplementedError
    #         else:  # dynamic sampling
    #             sitemaps_by_cat = sampling.construct_categories()
    #             if class_i_config['sampling']['method'] == 'url':
    #                 apk_jobs.append(
    #                     (iter(class_i_config['sampling']['urls']), None)
    #                 )
    #             elif class_i_config['sampling']['method'] == 'random':
    #                 n = class_i_config['sampling']['n']
    #                 apk_jobs.append(
    #                     (sampling.dynamic_random(sitemaps_by_cat), n)
    #                 )
    #             elif class_i_config['sampling']['method'] == 'category':
    #                 for cat, n in class_i_config['sampling']['category_targets'].items():
    #                     apk_jobs.append(
    #                         (sampling.dynamic_sample_category(sitemaps_by_cat, cat), n)
    #                     )

    #     # Stage 1: get apks from url iterators and decompile
    #     if class_i_config['stage'] in ['sampling']:
    #         if class_i_config['stage'] == 'apk':
    #             raise NotImplementedError
    #         # Extract raw features
    #         app_dir_ls = []
    #         for job_iter, job_n in apk_jobs:
    #             ls = decompile.download_decompile(raw_classes_dirs[class_i], job_iter, job_n)
    #             app_dir_ls += ls
    #         continue

    #     if class_i_config['stage'] in ['apk']:
    #         assert class_i_config['origin'] == 'external'
    #         app_dir_ls = decompile.decompile_apk_dir(class_i_config['external_dir'])

    #     # Stage 2: decompile
    #     if class_i_config['stage'] in ['apk', 'smali']:
    #         if class_i_config['origin'] == 'external':
    #             if class_i_config['external_structure'] == 'flat':
    #                 app_dir_ls = glob(
    #                     os.path.join(class_i_config['external_dir'], '*/')
    #                 )
    #                 assert len(app_dir_ls) > 0, "external_dir has no recognizable app"
    #                 assert class_i_config['sampling']['method'] == 'random'
    #                 app_dir_ls = random.sample(
    #                     app_dir_ls, class_i_config['sampling']['n']
    #                 )
    #             elif class_i_config['external_structure'] == 'by_category_variety':
    #                 app_dir_ls = glob(
    #                     os.path.join(class_i_config['external_dir'], '*', '*', '*/')
    #                 )
    #                 if class_i_config['sampling']['method'] == 'random':
    #                     app_dir_ls = random.sample(
    #                         app_dir_ls, class_i_config['sampling']['n']
    #                     )
    #                 else:
    #                     raise NotImplementedError
    #             else:
    #                 raise NotImplementedError

    #             print("Copying apps from external directory")
    #             for app_dir in app_dir_ls:
    #                 app_package = os.path.basename(os.path.dirname(app_dir))
    #                 shutil.copytree(
    #                     app_dir,
    #                     os.path.join(raw_classes_dirs[class_i], app_package)
    #                 )
    #         else:
    #             raise NotImplementedError


