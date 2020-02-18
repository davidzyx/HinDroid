## Cleaning and EDA

### Graph definitions

The HinDroid paper extracts information in smali code to construct a Heterogeneous Information Network with a graph representation. The graph consists of two types of node and four types of edges. Every node inside the HIN are representations of either an App or an API, which is defined in XXX. Every app node is only directly connected to API nodes and must not directly to other App nodes. This type of edge is denoting that the connected APIs can be found inside the App's smali code. Every other type of edges are edges between only APIs. These edges are features inside the smali code. Edge type B connects every pair of APIs that are co-appeared inside the same code block in every app. Edge type P connects every pair of APIs that are from the same library (package) inside every app. Edge type I connects every pair of APIs that are using the same invoke method for present in every app. The entire HIN graph is generated for every passthrough of the prediction task. Later we will deconstruct the graph to four adjacency matrices which correspond to the four types of edges.

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
 6   package        The apk package name where the file is from
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
