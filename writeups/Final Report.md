# DSC180A: Malware - Replication Project Final Report

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

The third step of the data pipeline involves extracting the smali assembly code out of APK files. The centerpiece of this pipeline is the popular [ApkTool](https://ibotpeaches.github.io/Apktool/) for decompiling. Given a configuration file containing the app url on APKPure, the python script will download the APK from the web and store it in a custom structured directory, and smali codes will be extracted in the same directory where the APK is downloaded. The user can also provide a path to a directory that contains the smali files to save time or to accommodate pre-decompiled malware.

Within the `raw` directory in `data_dir`, the script will create subdirectories for each class. Inside the extracted directory, we only store the app's `AndroidManifest.xml` metadata file and its smali subdirectories in order to save disk space. The apktool command to decompile the apk is: `$ apktool decode app_name.apk -o ./data/apps/{dev}/{name}`. The above configuration file would result in the following file structure:

```raw
data/
|-- class0/
    |-- raw/
    |   |-- com.instagram.android.apk
    |   |-- com.instagram.android/
    |   |   |-- AndroidManifest.xml
    |   |   |-- smali*/
    |   |
    |   |-- com.wallpapersforiphoneX.themeapplock88plus.apk
    |   |-- com.wallpapersforiphoneX.themeapplock88plus/
    |   |   |-- AndroidManifest.xml
    |   |   |-- smali*/
```

After the extraction, the script will delete all the irrelevant files, while only storing `AndroidManifest.xml` and the subdirectories that start with "smali".

#### Pipeline Applicability

The data pipeline is designed so that each python file can be runned as an independent step. The usage of the entire pipeline is shown in `get_data.py`.

#### Legal Issues and Privacy

In APKPure's [Terms of Use](https://apkpure.com/terms.html), it specifies that the website and its data are only for "personal use", and there is not any restrictions on scraping the website. Our use case in this project conforms to this term as there is no commercial intent and sales of any software and services.

IN APKPure's [robots.txt](https://apkpure.com/robots.txt) file, a [sitemap.xml](https://apkpure.com/sitemap.xml) is provided for scraping the site. Because of this, we do not violate any implicit rules set by the robots.txt file.

## Cleaning and EDA

### Graph definitions

The HinDroid paper extracts information in smali code to construct a Heterogeneous Information Network with a graph representation. The graph consists of two types of node and four types of edges. Every node inside the HIN represent either an App or an API. Every app node is only directly connected to API nodes and must not directly to other App nodes. This type of edge is denoting that the connected APIs can be found inside the App's smali code. Every other type of edges are edges between only APIs. These edges are features inside the smali code. Edge type B connects every pair of APIs that are co-appeared inside the same code block in every app. Edge type P connects every pair of APIs that are from the same library (package) inside every app. Edge type I connects every pair of APIs that are using the same invoke method for present in every app. The entire HIN graph is generated for every passthrough of the prediction task. Later we will deconstruct the graph to four adjacency matrices which correspond to the four types of edges.

### Compute intensive jobs

In order to gather the information needed for the HIN, we run text processing algorithms for every apps' smali codebase separately and store the information in a dataframe and save it to a csv file. The processed csv files are located in the interim folder in the data directory.

The columns of the dataframes are:

```pre
 #   Column         Description
---  ------         -----------
 0   call           Line of text containing the API call
 1   relpath        The relative path to the file containing this call
 2   code_block_id  The unique id of the code block containing the call
 3   invocation     The invoke method of the API call
 4   library        The library (package) the call is from
 5   method_name    The method name of the API
 6   package        The APK package name where the file is from
 7   class          Class label specified in config
 ```

### Raw text feature extraction algorithm

For the features, we only need to extract the lines containing either a code block start statement, a code block end statement, or an API call which begins with `invoke`. These lines are put in a numpy array and the values containing API calls are further extracted to get the invoke type, library(package), and method name. Every smali file inside the app codebase is fed through this pipeline and the information is aggregated to a dataframe. Cleaning is then applied. The `code_block_id` gets assigned and the rows containing the start and end statements are then dropped. Finally, it goes through assertions verifying that there is no missing data and saves it to the `interim` directory in their respective label folder.

## EDA

We are looking at two different types of apps: benign and malicious. The different csvs are aggregated to a giant dataframe so that we can run various aggregation function at the app level to get a feature vector corresponding to each app.

Empirically, the malwares are smaller in every way. Out of the 50 random sample that we take, there is only around 17000 API calls in an malware while a normal app averages around 90000 calls. They also use significantly less librarys. The median of number of libraries a malware calls is only around 5000, while that of normal app is 79000. Within a block, however, the median number of API calls for a malware is around 7 and that of normal apps is 4.3. This could be a result of bad coding habit presented among malware developers.

Comparing the API appearances, `Ljava/lang/StringBuilder` seems to differ the most across these two categories. The usage of this library could be an attempt to obfuscate the malicious strings (e.g. shady websites) against traditional malware detection programs. `Landroid/os/Parcel;`, `Ljava/lang/String;`, `Ljava/lang/StringBuffer;`, `Landroid/content/Intent;` are among others whose appearances in either categories differ.

## Baseline Model

The `FeatureBuilder` class is used to transform the dataframe listing all API calls to a dataframe indexed by individual apps in the dataframe. The features constructed here are almost all numerical. They are:

- number of API calls
- number of library used
- number of code blocks used
- max number of code block within a file
- mean number of code block within a file
- number of invokes for every type

just to name a few. Some basic features are categorical:

- top 5 libraries used in each app, one-hot coded

After the features are extracted, the resulting dataframe is saved to `processed`. We then use 3 basic models (linear regression, random forest and gradient boosted tree) to calculate the baseline performance of the model. We choose f1 score as our evaluating method. The reason is that in testing, the number of benign apps vastly outweight of the number of malwares, and both false positive and false negative are to be eliminated. Accuracy cannot give such insight to our specific problem, so f1 score is chosen. Out of 1000 trials with 50 benign apps and 50 malicious apps, the average reported f1 score for each model is:

| Model                      | F1 Score: avg | F1 Score: std |
|----------------------------|---------------|---------------|
| LinearRegression           | 0.8005        | 0.0784        |
| RandomForestClassifier     | 0.8042        | 0.0765        |
| GradientBoostingClassifier | 0.8255        | 0.0676        |

The f1 scores are averaging above 0.80 so it is fairly strong baseline. Among the models, gradient boosted tree is performing best.

## Result Replication

### HinDroid Intuition

The HinDroid model calculates similarities between apps and feeds the similarities to a SVM to form a decision boundary between two data classes. It constructs a Heterogeneous Information Network (HIN) to capture the relationships between apps and between APIs. The network consists of two node types and four edge types. Edge type A connects apps to APIs if the API is used by that app. Edge type B connects every pair of APIs that are co-appeared inside the same code block in every app. Edge type P connects every pair of APIs that are from the same library (package). Edge type I connects every pair of APIs that are using the same invoke method for present in every app. Each type of these edges will be represented by an adjacency matrix. To calculate the similarity, we formalize it as the number of common features that are both present in the HIN. If the similarity between two apps is high, there may be something to be said for it. We define this common feature as the number of metapaths between apps. A metapath starts from an app and ends with an app and it goes through a symmetric node path in the HIN. For example, A-A means how many APIs are common within a pair of apps; A-P-A means how many pairs of APIs (one API from a<sub>i</sub>, one API from a<sub>j</sub>) that use a common library. HinDroid assumes these metapaths represent a unique common feature between applications. For the case of metapath A-B-A, if two apps both called these specific APIs within a block somewhere in the source code, then their functionality or intent should be similar. Based on this intuition, we can see that if an app is more similar to a malware in terms of high similarity, we can be more confident that the mystery app should be a malware as well. In implementation, these metapaths are calculated using multiplication of adjacency matrices, and the result is used as a Gram matrix for the SVM algorithm to find a decision boundary between the two classes. Next we are going to talk about how to come to that result.

### Replication Methodology and Process

From the pre-processing pipeline in EDA, we extracted the features needed for the HinDroid model as a csv format for each app. This step then follow through after the csvs are saved to file and are read again.

Using the csv from the previous step, we have the necessary information to construct the edge type A, B, P, I in the Heterogeneous Information Network. Matrix A will have a shape of (# of apps, # of APIs) and matrices {B,P,I} will be symmetric and have a shape of (# of APIs, # of APIs). As the number of apps increases, the # of APIs present in the codebase grows as well. Matrices {A,B,P} will be saved as Compressed Sparse Row matrices ([`scipy.sparse.csr_matrix`](https://docs.scipy.org/doc/scipy/reference/sparse.html#module-scipy.sparse)) and matrix I will not be considered in this replication because of its high density.

To generate the A adjacency matrix, we used a unique ID finder (src.utils.UniqueIdAssigner) that assigns an unique integer ID to each unique API. We then keep a set of API IDs that appear in an app for each app and save these sets as a sparse matrix. The table of the one-to-one association between API and ID is also saved.

For adjacency matrices B and P, we do the following for each edge B and P. First, we generate pairs of API IDs from `itertools.combinations(APIs, 2)` for each condition that follows the edge type. This result in a matrix of shape (2, # of pairs) where every column of this matrix is a pair of API which are connected in the HIN, so that its corresponding value () in the final matrix should be 1. This step is parallelized by using multiprocessing. Then, these matrices are horizontally stacked together to create a sparse matrix in COOrdinate format ([`scipy.sparse.coo_matrix`](https://docs.scipy.org/doc/scipy/reference/sparse.html#module-scipy.sparse)). The pair of IDs are extracted because conversion between COO format and CSR format are "efficient, linear-time operations", and CSR format are suitable for matrix multiplication which is essential for this model. As far as I know, this should be the most efficient way of constructing the adjacency matrices, both using parallelism and using appropriate aggregation methods.

The number of meta-paths between the apps can then be calculated by multiplying the A matrix to other adjacency matrices and their appropriate inverses. For example, metapath `APBP^TA^T` will amount to `A.dot(P).dot(B).dot(P.T).dot(A.T)` in matrix multiplication.

### Replication Details

For each app, there is a csv file where each row is an API call in the codebase and its relevant details are also stored according to the schema in EDA. These csv files are stored inside the `process` directory under `data`, ungrouped. The aggregation happens afterwords and the coordinates are saved for each app in a separate numpy file. The naming scheme follows `{app_package}.B.npy` or `{app_package}.P.npy`. These matrices are of shape (2, # number of pairs). The aggregated A, B, P matrices are first stored as COO format in memory and written to disk in CSR format. These files are saved under `processed` using the `A.npz`/`B.npz`/`P.npz` naming scheme.

As the number of apps in the dataset grows, the number of API goes up as well. For 10 apps, there will be around 80k APIs; and for 1000 apps, there will be around 1.5M. The growth of the unique APIs is sublinear to the number of apps, and intuitively, as the the dimension increases, the number of values in the sparse matrices should increases quadratically. However, since CSR format only stores the non-zero values along a row, we can say that the file size increases linearly. We also keep a record of the mapping between API and their ids in a csv file. For around 1000 apps, the A sparse matrix file (`A.npz`) takes 15MB; and for B (`B.npz`) and P (`P.npz`), it's 47MB and 11MB respectively. The list of unique APIs (`APIs.csv`) takes up 88MB of space. These file sizes are within reasonable bounds and much much smaller than the raw data.

### Experiment Results and Interpretation

The dataset consists of 500 benign apps and 500 malware. In the benign app, we sampled 100 apps from each of the categories Communication, Tools, Comics, Art and Design, and Beauty. We assume these apps will have an adequate codebase size (as opposed to that in gaming categories) and should represent a wide ranging of APIs in the sample space. After pruning large or invalid smali codebases, there remain 481 benign apps and 484 malware. The dataset is then splitted into training and testing sets using a 2:1 ratio. We evaluate the performance of four metapaths in the paper: `AA^T`, `ABA^T`, `APA^T`, `APBP^TA^T`. Using 11 trials of random splitting, we have the following metrics. Only the median of each metric is shown.

| metapath | train_acc | test_acc | F1     | TP    | FP   | TN    | FN   |
|----------|-----------|----------|--------|-------|------|-------|------|
| AA       | 1.0000    | 0.9561   | 0.9562 | 158   | 10   | 147   | 4    |
| APA      | 1.0000    | 0.9373   | 0.9412 | 155   | 14   | 145   | 6    |
| ABA      | 0.9149    | 0.8558   | 0.8671 | 147   | 27   | 130   | 19   |
| APBPA    | 0.9040    | 0.8339   | 0.8408 | 140   | 32   | 126   | 22   |

The training accuracies of `AA` and `APA` are always 1.0. Interestingly, `AA` performs the best across both testing accuracies and F1 scores. Intuitively, adding more information should increase the testing accuracy, but here, the accuracy goes down when the metapath gets more complex. The F1 scores are very close to the corresponding accuracy because the testing set has balanced labels thanks to the curated dataset. In dealing with hardware, false negatives should be the most dangerous as they can slip through the detection and do actual harm. We see that in our implementation, FNs are smaller for the simpler metapaths. Adding more information in the kernel obfuscated the similarity and make the decision boundary less confident. The reason for this is explained in the next section.

To compare to the results referenced in the HinDroid paper, we should use F1 scores because the testing set in HinDroid's implementation has an imbalance of true and false labels. The F1 scores for `AA` are virtually the same. The scores for `APA` did slightly worse than HinDroid's with a 2% difference. For `ABA` and `APBPA`, the F1 scores are much worse than HinDroid's, getting at least a 10% drop. It seems like the more complex metapaths did not give more relevant information to aid the classification.

### Shortcomings and Possible Improvements

There is one important weakness in my implementation of the preprocessing stage that may lead to data leakage into the model and it is also part of the reason that simpler metapath has a higher accuracy. The training and testing data as a whole are passed through the matrix generating process exactly once, so the APIs will include all the seen APIs in the training and testing dataset, instead of keeping two separate sets of matrices {A, B, P}. Only at training time, A matrix is splitted into training rows and testing rows to calculate the Gram matrix, but the feature vector representing an app has a dimension of the number of unique APIs in the whole dataset, which prompted the data leakage. Furthermore, in adjacency matrices B and P, there is no way to discern whether the nonzero values (1s) are from the connections in the training set. The train-test split should be done at feature extraction step to isolate the features in the two classes. It is a design oversight as train-test splitting were not taken into account at the beginning of implementation design. This bug could take some effort to fix because of it.

To improve the model, it is beneficial to apply ensemble learning methods since a single metapath cannot give a clear decision boundary in its limited feature space. One method we can use is to use a voting algorithm that combines the predicted confidences of several kernels and unify a single decision. Another way is to follow the combined-kernel method which uses the Laplacian Scores for feature selection. The best method in the paper uses a multi-kernel learning algorithm, and can also be used to improve the model.

## Conclusion

Through a rough but non-trivial implementation of the HinDroid paper, we learned that handling large amounts of unstructured data can be very difficult to handle and it requires tremendous effort to construct a custom data pipeline with a user-friendly interface and high versatility. Indeed, a large portion of the data science workflow is working on data and not on the model. For replication, we tested a small portion of the HinDroid paper's findings and found some similarities and inconsistencies for the F1 scores. We also find that there are many things that could be done to improve the model, where fixing data leakage is the most significant one.
