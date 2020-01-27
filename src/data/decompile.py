import urllib
import requests
import os
import subprocess
import shutil
import glob

# !pip install beautifulsoup4
from bs4 import BeautifulSoup


def get_app(app_url):
    app_url += '/download?from=details'
    download_page = requests.get(app_url)
    soup = BeautifulSoup(download_page.content, features="lxml")
    try:
        apk_url = soup.select('#iframe_download')[0].attrs['src']
    except:
        print(f'Download error for {app_url}')
        return None

    return requests.get(apk_url).content


def run(data_dir, urls):
    apps_dir = os.path.join(data_dir, 'apps')
    if not os.path.exists(apps_dir):
        os.mkdir(apps_dir)
    
    for url in urls:
        app_slug, app_pkg = url.split('/')[-2:]
        app_slug = urllib.parse.unquote(app_slug)  # include or not
        pkg_dir = os.path.join(apps_dir, app_pkg)
        if not os.path.exists(pkg_dir):
            os.mkdir(pkg_dir)
        
        apk = get_app(url)
        if apk is None:
            os.rmdir(pkg_dir)
            continue
        
        apk_fn = os.path.join(pkg_dir, app_slug + '.apk')
        apk_fp = open(apk_fn, 'wb')
        apk_fp.write(apk)
        print(apk_fn)
        
        code_dir = os.path.join(pkg_dir, app_slug)
        if os.path.exists(code_dir):
            shutil.rmtree(code_dir)
            
        print('Decompiling apk...')
        command = subprocess.run([
            'apktool', 'd',  # decode
            #  '-r',            # no resources, but it seems to corrupt the AndroidManifest.xml file, idk why
            apk_fn,          # apk filename
            '-o', code_dir   # decompiled out path
        ], capture_output=True)
        print(command.stdout.decode())


        for dir in set(glob.glob(os.path.join(code_dir, '*/'))) - set(glob.glob(os.path.join(code_dir, 'smali*/'))):
            shutil.rmtree(os.path.abspath(dir))
        os.remove(apk_fn)
