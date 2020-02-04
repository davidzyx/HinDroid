
def sample_df_random(apps, n=10):
    """Randomly sample n apps from the dataframe. Returns an iterator.

    :param apps: dataframe from metadata.parquet.
    :param n: max number of apps in the sample.
    :yields:  int -- the return code.
    """
    history = []
    while True:
        if len(history) == n:
            break

        sample = apps.sample(1).squeeze()
        app_index = sample.package
        if app_index in history:
            continue
        else:
            history.append(app_index)

        yield f"https://apkpure.com/{sample.name_slug}/{sample.package}"
