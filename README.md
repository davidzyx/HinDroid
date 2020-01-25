# HinDroid

This repository is a thorough implementation attempt at the [Hindroid](https://www.cse.ust.hk/~yqsong/papers/2017-KDD-HINDROID.pdf) paper (DOI:[10.1145/3097983.3098026](https://doi.org/10.1145/3097983.3098026)).

The task of interest here is to effectively classify Android applications as benign or malicious. Malicious applications pose security threats to the public as they often intentionally obtain sensitive information from the victim's phone. Our intent is to replicate the findings presented in this paper by sourcing the data by ourselves and then applying machine learning techniques mentioned on the data we acquired.

## The Data

The paper uses a static analysis method to identify malware. It only analyze the code instead of running a more dangerous dynamic analysis method to monitor the app's behavior. Essentially, we need to extract code from an Android app. Android apps are compiled and distributed as packages in the .apk (Android Application Package) format. This package contains unreadable dex code files, which can be decompiled into Smali code to be read and processed using [ApkTool](https://ibotpeaches.github.io/Apktool/). We then parse the smali codes to get useful information for classifying an app is malicious or not.

The most important feature this paper is focused on is API calls in smali codes. API stands for Application Programming Interfaces, they are an abstract layer of function calls that can be imbedded in code to accomplish anything the developer wants. While there are low-level APIs like string contatenation or parsing a string to an integer, the APIs that trigger our senses should be those that are asking system permissions or sending HTTP requests to a suspecting IP address. Shown below is an excerpt of .smali file that is the decomposition of appending two strings using StringBuilder in Java:

```smali
invoke-virtual {v9, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

invoke-virtual {v9}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
```

A call can be decomposed into 6 components:

1. Invoke method
2. Arguments that are used to call the methods (parameters)
3. Library of the function
4. Function name
5. Type of arguments in parenthesis
6. Return type

In this section, we are going to explain how we are going to get the data that leads to the feature extraction in smali code.

### Acquiring Data

#### Overview

The data we need consist of two parts: benign apps and malicious apps.

We get our benign apps from an online APK distribution platform [APKPure](https://apkpure.com), where APK files can be downloaded directly. This tool is preferable because of the relative ease of downloading APK files and the scraping-friendly interface -- getting those from the Google Play Store is rather a burden. The malicious apps are obtained through a private source, since databases that collect these data are sensitive and could be used in malicious ways, which is the opposite of what we want. By acquiring apps with both positive and negative labels in our classification task, we can apply machine learning algorithms for binary classification to separate their varying intent.

#### Connection to the Problem

Although the sitemap that describes the structure of APKPure's website was last updated on 09/16/2019, the APK files linked in the website is updated to the latest version, so the benign part of the data accurately represent what people are using on their phones, thus they contain the latest features from that group. On the apps that are malicious, they are from historical databases. They are still relevant to the question since malicious apps are often of certain types or their variants, and these groups often exhibit similar behavior, which can be represented in the same API calls in their codebase. This can be extracted from the decompiled executable, and combined with the relationship between them, they will be used as features in the model.

Since malicious apps are provided in very limited quantities, they are dwarfed by the number of benign applications hosted on APKPure. We can thus adjust the makeup of the benign apps data by our preference to better represent the population of Android apps and also boost the performance of various machine learning algorithms on binary classification.

#### Shortcomings

One big assumption made here is that every app in the APKPure market is taken as benign. This assumption is necessary because the best attempt at testing if an app is malicious is to analyze them by security experts, a practice that is costly which the paper is trying to mitigate. This assumption is also dangerous since APKPure does not say on its website where they obtained the APK files. While the Google Play Store can be assumed to have the best security screens, apps obtained from other sources or platforms can potentially contain malware. Anyway, APKPure is the best that we have.

There is also a small inconsistency between the app formation in the real world setting and the data that is obtained here. Because of copyright and legal issues, APKPure only provide free apps on their platform where real Android users can purchase apps with a price. This makes the data not an exact representation of its intended population. Though the conditional probability that an app is malicious given it's a paid app is low because of the significantly high bar of transmission and return in this case. I would argue this composition of benign free apps in the data is better because malicious code mostly come from free apps, thus it is easier to distinguish them apart in production.

This paper also only focuses on the relationships between API calls themselves and the connections between API calls and different applications. These are only a subset of features that we can extract from the smali files. Since smali files are placed in folder as each file represents a subclass in their parent superclass, how the class structure is made is not being considered in this paper. Also, the repeated use of one API call is not represented as is in the feature presented in the paper. An API call

#### Past Efforts

The standard in identifying security threats on the fly has been mainly using the signature of the application in question to check against a database of identified malicious apps. This method requires the data obtained in the first step of our data acquirement process because the extraction tool cannot run on the Android kernel.

Other research studies on identifying malware have been using either dynamic analysis, or using only the API calls and system access requests. These efforts are either computationally heavy since running the application requires an active virtual runtime for analysis, and it takes significant more time to predict.

In this paper, relationships between API calls are extracted using a heterogeneous information network (HIN). Similarities between apps are then calculated from meta-paths constructed by multiplying the different combinations of adjacency matrices. These higher-dimension features are fed to a multi-kernel learning system where a decision boundary can be drawn. It is also faster to analyze as it requires no dynamic tools to run the software, and the learnings are semi-interpretable as similarity between other identified malwares can be easily checked using the kernel method.

### Ingesting Data

#### Data Pipeline

In the first step of the data pipeline, we use [APKPure](https://apkpure.com) to download benign Android applications. The site's robots.txt file contains a sitemap.xml file which can be parsed to get information on all the apps available on the website. The sitemap.xml lists all the additional xml files that each consists of roughly 1000 apps in the same category. We can aggregate only the information that we need and store it in a Apache Arrow [Parquet](https://parquet.apache.org/) file. We do this by dynamically requesting the url instead of saving all subfiles into a file system. There are ~7700 xml files stored in the master file, and saving them will require ~2.35GB of disk space. The dynamically processed procedure saves file IO overhead that would slow down data extraction speed and further decrease read and query efficiency down the pipeline.

The columns that are stored in the table includes:

+ `url`: Link to the app on the website
+ `name`: Name of the application in UTF-8
+ `category`: Category of the application/game
+ `lastmod`: The datetime of the last update~~
+ ~~`changefreq`: How often it checks for updates~~
+ ~~`priority`: Unknown~~
+ `image_loc`: The Cloudare CDN link to the app's logo
+ `sitemap_url`: The URL in sitemap.xml that contains this entry
+ `name_slug`: Name of the application in URL encoding format
+ `package`: The package name for the apk file

Among these columns, changefreq and priority have only one unique value, where changefreq is all weekly and priority is all 0.6, so both columns are dropped. For `name_slug` and `package`, they are extracted from the url column, where individual apps' url are constructed this way: `https://apkpure.com/{name_slug}/{package}`. The `package` name can also be found in the `AndroidManifest.xml` manifest file. To save disk space and read speed later on, columns `url`, `image_loc`, `sitemap_url` are dropped because they are either redundant or irrelevant.

Given the dataframe, we can apply custom sampling method to cater to different needs, such as giving equal representation on all categories or just purely random sample without replacement. Also, the dataframe file can be easily distributed because it has only one compact file.

The second step of the data pipeline lets the user choose a sampling method to generate a list of urls that feeds into the third step. For now, we provide an naive way, simple random sample without replacement, for a baseline data.

The script will output a list of urls that link to the application on APKPure.

The third step of the data pipeline involves extracting the smali assembly code out of APK files. The centerpiece of this pipeline is the popular [ApkTool](https://ibotpeaches.github.io/Apktool/) for decompiling. Given a configuration file containing the app url on APKPure, the python script will download the APK from the web and store it in a custom structured directory, and smali codes will be extracted in the same directory where the APK is downloaded. This config file being fed here should be generated by an additional sampling script that reads the dataframe table from the first pipeline. The data_params.json should be structured as follow:

```json
{
    "data_dir": "./data",
    "urls": [
        "https://apkpure.com/instagram/com.instagram.android",
        "https://apkpure.com/wallpaper-for-iphone-x-8-8/com.wallpapersforiphoneX.themeapplock88plus"
    ]
}
```

Within `data_dir`, the script will create a subdirectory `apps`, which includes more subdirectories named by the `dev` field of the corresponding app, these `dev` folders will contain both the APK files and their extracted content. Inside the extracted directory, we only store the app's `AndroidManifest.xml` metadata file and its smali subdirectories in order to save disk space. We also keep a log file that store which app are downloaded and their MD5 sum. The apktool command we use is: `$ apktool decode app_name.apk -o ./data/apps/{dev}/{name}`. The file schema is designed like this because after some EDA, we discovered that some apps may have the same name but can never have the same dev. The above configuration file would result in the following file structure:

```
data/
|-- apps/
|   |-- com.instagram.android/
|   |   |-- instagram.apk
|   |   |-- instagram/
|   |   |   |-- AndroidManifest.xml
|   |   |   |-- smali*/
|   |
|   |-- com.wallpapersforiphoneX.themeapplock88plus/
|   |   |-- wallpaper-for-iphone-x-8-8.apk
|   |   |-- wallpaper-for-iphone-x-8-8/
|   |   |   |-- AndroidManifest.xml
|   |   |   |-- smali*/
```

After the extraction, the script will delete all the irrelevant files, while only storing `AndroidManifest.xml` and the subdirectories that start with "smali". An optional step can be applied to the smali folders in the extracted content. The intent is to compress the complicated file structure that smali folders have. There are at least 100 smali files in every project and they are just some of the basic or low level APIs that every app must include. Because of that reason, we could create a `tar` archive for every app's smali folders to reduce the file size down to only 1, similar to the first step of the data pipeline. However, since the smali folders only get read by the next step only once for every analysis, it isn't strictly necessary for the tarball. Although we can save some disk space while gziping the tar archive.

<!-- The third step is primarily focused on the ease of extracting features in the EDA part of this project. Reading many a complex directory tree can be computationally inefficient when a prior preprocessing step can be applied to extract all the details in general. For the preparation of this specific paper, we can extract only the sufficient lines and stack them in a giant text file. The lines we are going to extract should contain only API method opens and closes. The information is sufficient because if the lines are stored in the same order as they appear in files, we can parse them later to see which APIs are in the same method and call components can be extracted using regex. In this way, we get one smali text file for  -->

#### Pipeline Applicability

The data pipeline is designed so that each python file can be runned as an independent step. The usage of the entire pipeline is shown in `get_data.py`.

#### Legal Issues and Privacy

In APKPure's [Terms of Use](https://apkpure.com/terms.html), it specifies that the website and its data are only for "personal use", and there is not any restrictions on scraping the website. Our use case in this project conforms to this term as there is no commercial intent and sales of any software and services.

IN APKPure's [robots.txt](https://apkpure.com/robots.txt) file, a [sitemap.xml](https://apkpure.com/sitemap.xml) is provided for scraping the site. Because of this, we do not violate any implicit rules set by the robots.txt file.

