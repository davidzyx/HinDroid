import urllib
import requests
import os
import subprocess
import shutil
from glob import glob
import sys

# !pip install beautifulsoup4
from bs4 import BeautifulSoup


def prep_dir(apps_dir, url):
    """Make the directory to store data specific to the requested app

    :param apps_dir: path to apps in data directory
    :param url: app to be prepped/downloaded
    :returns: app_dir -- path to where app is going to be stored
    :returns: package -- package name of the app
    """
    print('Prepping...')
    package = url.split('/')[-1]
    app_dir = os.path.join(apps_dir, package)
    if not os.path.exists(app_dir):
        os.mkdir(app_dir)
    return app_dir, package

def get_apk(app_url):
    """Scrape the apk file from APKPure
    
    :param app_url: url to app on APKPure
    :returns: APK in bytes
    """
    print('Downloading apk...')
    app_url += '/download?from=details'
    download_page = requests.get(app_url)
    soup = BeautifulSoup(download_page.content, features="lxml")
    try:
        apk_url = soup.select('#iframe_download')[0].attrs['src']
    except:
        raise Exception('Error, download link not found')
    return requests.get(apk_url).content

def save_apk(app_dir, apk):
    """Save apk bytecode to filesystem

    :param app_dir: path to app directory
    :param apk: APK package bytes
    :returns: filename of APK
    """
    apk_fn = app_dir + '.apk'
    apk_fp = open(apk_fn, 'wb')
    apk_fp.write(apk)
    return apk_fn

def apktool_decompile(apk_fn, app_dir):
    """Decompile the apk package to its directory using apktool

    :param apk_fn: filename for the APK
    :param app_dir: path to app directory for output
    :raises: Exception is something bad happened
    """
    print('Decompiling apk...')

    command = subprocess.run([
        'apktool', 'd',     # decode
        apk_fn,             # apk filename
        '-o', app_dir,      # out dir path
        '-f'                # overwrite out path
    ], capture_output=True)

    print(command.stdout.decode(), end="")
    if command.stderr != b'':
        print(command.stderr.decode())
        raise Exception('apktool error')

def decom_clean(app_dir):
    """Clean unwanted files and other folders (resources) from app directory
    
    :param app_dir: path to app directory
    """
    # os.remove(apk_fn)
    unwanted_subdirs = (
        set(glob(os.path.join(app_dir, '*/'))) -
        set(glob(os.path.join(app_dir, 'smali*/')))
    )
    for dir in unwanted_subdirs:
        shutil.rmtree(os.path.abspath(dir))
        
def clean(app_dir, package):
    """Remove anything that is from this package"""
    shutil.rmtree(app_dir)
    apk_fn = app_dir + '.apk'
    if os.path.exists(apk_fn):
        os.remove(apk_fn)

def validity_check(app_dir):
    """Check if decompiled app directory has smali files"""
    smali_fn_ls = sorted(glob(
        os.path.join(app_dir, 'smali*/**/*.smali'), recursive=True
    ))
    if len(smali_fn_ls) == 0:
        raise Exception('App has no smali files')

def decompile(apps_dir, urls_iter, n):
    """TODO: multiprocess this? may be worth trying"""
    count = 0
    app_dir_ls = []
    for url in urls_iter:
        if count == n:
            print('Complete')
            break

        print('Downloading', url)
        app_dir, package = prep_dir(apps_dir, url)
        try:
            apk = get_apk(url)
            apk_fn = save_apk(app_dir, apk)
            apktool_decompile(apk_fn, app_dir)
            decom_clean(app_dir)
            validity_check(app_dir)
            app_dir_ls.append(app_dir)
            count += 1
            print()  # empty line

        except Exception as e:
            print("Unexpected error:", e)
            # raise
            clean(app_dir, package)
            print()
            continue
    return app_dir_ls
