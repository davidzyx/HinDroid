import urllib
import requests
import os
import subprocess
import shutil
from glob import glob

# !pip install beautifulsoup4
from bs4 import BeautifulSoup


def prep_dir(main_dir, url):
    """Make the directory to store data specific to the requested app

    :param main_dir: path to apps in data directory
    :param url: app to be prepped/downloaded
    :returns: app_dir -- path to where app is going to be stored
    :returns: package -- package name of the app
    """
    print('Prepping...')
    package = url.split('/')[-1]
    app_dir = os.path.join(main_dir, package)
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
        return None
    return requests.get(apk_url).content

def save_apk(app_dir, apk):
    """Save apk bytecode to filesystem

    :param app_dir: path to app directory
    :param apk: APK package bytes
    :returns: filename of APK
    """
    print('Saving apk...')
    apk_fn = os.path.join(app_dir + '.apk')
    apk_fp = open(apk_fn, 'wb')
    apk_fp.write(apk)
    return apk_fn

def decompile(apk_fn, app_dir):
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

def clean(app_dir):
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

def run(data_dir, urls_iter):
    main_dir = os.path.join(data_dir, 'apps')
    if not os.path.exists(main_dir):
        os.mkdir(main_dir)

    for url in urls_iter:
        app_dir, package = prep_dir(main_dir, url)
        try:
            apk = get_apk(url)
            apk_fn = save_apk(app_dir, apk)
            decompile(apk_fn, app_dir)
            clean(app_dir)
            # log
        except:
            print('something bad happened')
            shutil.rmtree(app_dir)
            continue
        finally:
            pass
