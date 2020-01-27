
def sample_random(apps, n=10):
    """Randomly sample n number of apps from the dataframe"""
    df = apps.sample(n)
    return ('https://apkpure.com/' + df.name_slug + '/' + df.package).to_list()
