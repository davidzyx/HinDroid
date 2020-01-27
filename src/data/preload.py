import pandas as pd
import requests
import gzip
from tqdm import tqdm
import io
import xml.etree.ElementTree as ET
import re
# from sqlalchemy import create_engine
from multiprocess import Pool


def extract_apps(sitemap_url):
    """Extract a single sitemap.xml.gz and return a dataframe of apps

    >>> df = extract_apps('https://apkpure.com/sitemaps/art_and_design-2.xml.gz')
    >>> df.shape
    (1000, 4)
    """
    try:
        r = requests.get(sitemap_url).content
    except:
        print('error', sitemap_url)
        return pd.DataFrame()
    
    fp = io.StringIO(gzip.decompress(r).decode())
    sitemap_root = ET.parse(fp).getroot()
    apps = list(sitemap_root)
    apps = [app for app in apps if 'image' in app[4].tag]
    
    df = pd.DataFrame({
        'url': [a[0].text for a in apps],
        'lastmod': [a[1].text for a in apps],
        'name': [a[4][1].text for a in apps],
    })
    df.lastmod = pd.to_datetime(df.lastmod)
    df['category'] = re.search('(\w+)', sitemap_url.split('/')[-1]).groups()[0]
    
    return df


def run(datadir):
    """Runs the first step of the data pipeline
    Gets the entire sitemap and stores it in datadir

    datadir: output directory for metadata.parquet

    >>> run('../../data/')
    """
    r = requests.get('https://apkpure.com/sitemap.xml').content
    fp = io.StringIO(r.decode())
    root = ET.parse(fp).getroot()
    urls = [c[0].text for c in root]
    urls = [u for u in urls if not ('default' in u or 'topics' in u or 'tag' in u or 'group' in u)]

    print('Getting app data...')
    with Pool(16) as p:
        df_list = list(tqdm(p.imap_unordered(extract_apps, urls), total=len(urls)))

    print('ok')
    metadata = pd.concat(df_list, ignore_index=True)

    metadata = metadata[~(
        (metadata['name'] == 'Vendetta Miami Police Simulator 2019') & (metadata['category'] == 'comics')
    )]

    more_data = metadata['url'].str.rsplit('/', n=2, expand=True) \
        .rename(columns=dict(zip(range(3), ['domain', 'name_slug', 'package'])))
    more_data.head()

    metadata = pd.concat([metadata, more_data], axis=1)
    metadata = metadata.drop(columns=['domain', 'url'])
    metadata = metadata.reset_index(drop=True)[['package', 'name', 'category', 'name_slug', 'lastmod']]

    print(f'Saving to {datadir} ...')
    metadata.to_parquet(os.path.join(datadir, 'metadata.parquet'), engine='pyarrow')

