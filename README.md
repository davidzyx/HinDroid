# HinDroid

This repository is a thorough implementation attempt at the [Hindroid](https://www.cse.ust.hk/~yqsong/papers/2017-KDD-HINDROID.pdf) paper (DOI:[10.1145/3097983.3098026](https://doi.org/10.1145/3097983.3098026)).

The task of interest here is to effectively classify Android applications as benign or malicious. Malicious applications pose security threats to the public as they often intentionally obtain sensitive information from the victim's phone. Our intent is to replicate the findings presented in this paper by sourcing the data by ourselves and then applying the machine learning techniques mentioned on the data we acquired.

## The Data

The paper uses a static analysis method to identify malware. It only analyze the code to extract information instead of running a more dangerous dynamic analysis method to monitor the app's behavior. Therefore we need to extract the code from an Andriod app. Android apps are compiled and distributed as packages in the .apk (Android Application Package) format. This package contains unreadable dex code files, which can be decompiled into Smali code to be read and processed using [ApkTool](https://ibotpeaches.github.io/Apktool/). We then parse the smali codes to get the useful information for classifying an app is malicious or not.

### Acquiring Data

#### Overview

The data consists of two parts: benign apps and malicious apps.

We get our benign apps from an online APK distribution platform [APKPure](https://apkpure.com), where APK files can be downloaded directly. This tool is preferrable because of the relative ease of downloading APK files and the scraping-friendly interface -- getting those from the Google Play Store is rather a burden. The malicious apps are obtained through a private source, since databases that collect these data are sensitive and could be used in malicious ways, which is the opposite of what we want. By acquiring apps with both positive and negative labels in our classification task, we can apply machine learning algorithms for binary classification to separate their different intent.

#### Connection to the Problem

Although the sitemap that describes the structure of APKPure's website is last updated on 09/16/2019, the APK files linked in the website is updated to the latest version, so the benign part of the data accurately represent what people are using on their phones, thus they contain the latest features from that group. On the apps that are malicious, the data we get are from historical databases. They are still relevant to the question since malicious apps are often of certain types or their variants, and these groups often exhibit similar behavior, which can be represented in the same API calls in their codebase. These information can be extracted from the decompiled executable as well as the relationship between them will be used as features in the model later on.

Since malicious apps are provided in very limited quantities, they are dwarfed by the number of benign applications hosted on APKPure. We can thus adjust the makeup of the benign apps data by our preference to better represent the population of Android apps and also benefit the performance of various machine learning algorithms on binary classification.

#### Shortcomings

One big assumption made here is that every app in the APKPure market is taken as benign. This assumption is necessary because the best attempt at testing if an app is malicious is to analyze them by security experts, a practice that is costly which the paper is trying to mitigate. This assumption is also dangerous since APKPure does not say on its website where they obtained the APK files. While the Google Play Store can be assumed to have the best security screens, apps obtained from other sources or platforms can potentially contain malware. Anyway, APKPure is the best that we have.

There is also a small inconsistency between the app formation in the real world setting and the data that is obtained here. Because of copyright and legal issues, APKPure only provide free apps on their platform where real Android users can purchase apps with a price. This makes the data not an exact representation of its intended population. Though the conditional probability that an app is malicious given it's a paid app is low because of the significantly high bar of transmission and return in this case. I would argue this composition of benign free apps in the data is better because malicious code mostly come from free apps, thus it is easier to distinguish them apart in production.

This paper also only focuses on the relationships between API calls themselves and the connections between API calls and different applications. These are only a subset of features that we can extract from the smali files. Since smali files are placed in folder as each file represent a subclass in their parent superclass, how the class structure is made is not being consider in this paper. Also, the repeated use of one API call is not represented as is in the feature presented in the paper. An API call

#### Past Efforts

The standard in identifying security threats in Android apps on the fly have been mainly using the signature of the application in question to check against a database of identified malicious apps. This methods requires the data obtained in the first step of our data acquirement process because the extraction tool cannot run on the Android kernel.

Other research studies on identifying malware have been using either dynamic analysis, or using only the API calls and system access requests. These efforts are either computionally heavy since running the application requires an active virtual runtime for analysis, and it takes significant more time to predict.

In this paper, relationships between API calls are extracted using a heterogeneous information network (HIN). Similarities between apps are then calculated from meta-paths constructed by multiplying the different combinations of adjacency matrices. These higher-dimension features are fed to a multi-kernel learning system where a decision boundary can be drawn. It is also faster to analyze as it requires no dynamic tools to run the software, and the learnings are semi-interpretable as similarity between other identified malwares can be easily checked using in the kernel method.

<!-- ### Ingesting Data -->
