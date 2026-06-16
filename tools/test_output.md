Egyptian Informatics Journal 30 (2025) 100643 

**==> picture [61 x 67] intentionally omitted <==**

Contents lists available at ScienceDirect Egyptian Informatics Journal 

journal homepage: www.sciencedirect.com 

**==> picture [57 x 72] intentionally omitted <==**

## Full Length Article 

## A real-time system for monitoring and classification of human falls on stairs using 2.4 GHz XBee3 micro modules with a tri-axial accelerometer and KNN algorithms 

**==> picture [29 x 30] intentionally omitted <==**

## Apidet Booranawong[a][,][*] , Sittiporn Sukveeraphan[a] , Liangrui Pan[b] , Nattha Jindapetch[a] , Pornchai Phukpattaranont[a] , Hiroshi Saito[c] 

a _Department of Electrical and Biomedical Engineering, Faculty of Engineering, Prince of Songkla University, Songkhla 90110, Thailand_ b _College of Computer Science and Electronic Engineering, Hunan University, Hunan 410083, China_ c _Division of Computer Engineering, The University of Aizu, Aizu-Wakamatsu 965-8580, Japan_ 

A R T I C L E I N F O A B S T R A C T _Keywords:_ In this paper, a monitoring and classification system for human activities on stairs is presented. The contribution Human falls of this work is that, first, we develop the real-time wireless sensor monitoring system for measuring human Stairs motion data using 2.4 GHz IEEE 802.15.4 XBee3 micro modules as the low-power wireless modules, where the Tri-axial accelerometer GY-521 accelerometer sensor is attached. Here, human activities on stairs, including stair ascent, stair descent, 2.4 GHz XBee Classification turning around, and falling, are mainly focused on preventing any dangerous accidents. Second, using the measured data, the signal vector magnitude (SVM) calculation, signal filtering using an exponentially weighted moving average (EWMA), feature extraction using the mean, maximum, interquartile range (IQR), standard deviation (STDEV), variance, and peak-to-peak (PTP) amplitude, and classification using the K-nearest neighbors (KNN) algorithm are applied. Experiments have been conducted in a home scenario. Results indicate that the proposed system can efficiently monitor human activities on stairs in real-time with reliable communications, as indicated by a strong level of the received signal strength indicator (RSSI), and a packet delivery ratio (PDR) of 100 % for both line-of-sight (LoS) and non-line-of-sight (NLoS) communications. Additionally, the proposed system using only one variance feature and the KNN classifier provides classification accuracy of 89 % for stair ascent, 70 % for stair descent, 95 % for turning around, and 100 % for falling (a critical or focused event); 88 % on average results. Thus, our system, which includes devices and classification algorithms, has the potential to monitor and categorize human falls on stairs via wireless communication, and it can be applied in practical situations. 

## **1. Introduction** 

Falls are an important cause of injury, loss of independence, and increased health care utilization. The risk of falling among the elderly population increases with age, with 50 % of older people experiencing a fall-related incident each year [1,2]. Additionally, a number of people aged 65 or over fall each year, and the number increases for those aged 70 or over [3]. Aging and living conditions (i.e., home environments) are two of the most common causes of falls. In elderly people, multiple physical changes make them more prone to falling. For example, vision changes over time, making it more difficult to investigate their surroundings and identify obstacles. Falls also influence psychological 

health (e.g., depression) and family caregivers’ quality of life [4,5]. Among elderly people, falls inside the home are frequently the cause of both fatal and non-fatal accidental injuries [4]. Particularly, falls on stairs are among the serious causes of injuries and long-term medical expenses. Due to their weakened visual and musculoskeletal systems, older people are at risk for dangerous situations on stairways. Consequently, to reduce the negative consequences of a fall event, automatic fall detection systems are being developed to identify when a person falls and alert caregivers to provide assistance on time and deliver timely medical services. 

With the advancement of sensing and computing techniques, artificial intelligence (AI), high-performance embedded devices, and wireless 

- Corresponding author. 

_E-mail address:_ apidet.b@psu.ac.th (A. Booranawong). 

https://doi.org/10.1016/j.eij.2025.100643 

Received 25 May 2024; Received in revised form 23 December 2024; Accepted 12 March 2025 Available online 19 March 2025 

1110-8665/© 2025 THE AUTHORS. Published by Elsevier BV on behalf of Faculty of Computers and Artificial Intelligence, Cairo University. This is an open access article under the CC BY-NC-ND license (http://creativecommons.org/licenses/by-nc-nd/4.0/). 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**Table 1** 

A summary of related works and this work. 

|Ref./|Sensor technology|Wireless technology|Human activities|Test areas|Results/Accuracy|
|---|---|---|---|---|---|
|Year||||||
|[3]|Multiple cameras|No|Falls|−|100 %|
|2019|Video kinematic data|||Using sports||
|||||dataset||
|[6]|Kinect|No|Falls|Home|95 %|
|2022|||Non-falls|||
|[7]|3D motion sensor|No|Falls and near falls|Laboratory|92 %|
|2015|Microsoft Kinect|||on stairs||
|[2]|• Accelerometer|Bluetooth|Falls|Laboratory|96.9 %.|
|2010|• Barometric pressure sensor|||||
|[8]|• Triaxial accelerometer|A MSP430FR5969 microcontroller with|Falls|Laboratory|93.0 %|
|2016|• Barometric pressure sensor|a RFM73 transceiver|||Estimated battery life of 664.9|
||||||days|
|[9]|• Triaxial accelerometer|An ATmega328 microcontroller with|Falls|Laboratory|90.37 %.|
|2015|• Gyroscope|Bluetooth||||
||• Magnetometer|||||
|[10]|• Triaxial orthogonal accelerometer|No|Wheelchair falls|Laboratory|97.1 %|
|2023|• Gyroscope|||||
|[11]|Inertial sensors|No|Wheelchair tips and|Laboratory|96 %.|
|2023|||falls|||
|[12]|• Triaxial accelerometer|No|Heart rate|Home|87 %|
|2019|• Grove-ear-clip heart rate sensor||Falls from walking or|||
||• Photoelectric sensors||standing|||
|[13]|A single, waist-mounted triaxial|A MSP430 microcontroller with a|Falls and Walking|Laboratory|95.6 %|
|2006|accelerometer|CC2420 RF transceiver||||
|[14]|Wearable accelerometer|No|Falls|−|96 % to 100 %|
|2021||||Using three public||
|||||datasets||
|[15]|Accelerations through the wrist-worn|No|Walk-Fall-Still|Laboratory|90 %|
|2023|M5StickC-Plus watch|||||
|**This**<br>**work**|**A single triaxial accelerometer**|**2.4 GH IEEE 802.15.4**<br>**XBee3 micro modules**|**Stair ascent**<br>**Stair descent**|**Home**<br>**on stairs**|• **Real-time monitoring and**<br>**classifcation**|
||||**Turning around**||• **100 % (fall detection**|
||||**Falls on stair**||**accuracy on stairs)**|
||||||• **100 % (PDR: communication**|
||||||**reliability)**|



communication technology, an autonomous monitoring and classification system to detect human falls can be established. A review of related works is discussed here. The difference between related works and the proposed work is also summarized in Table 1. 

Lu _et al._ (2018) [3] developed a three-dimensional convolutional neural network (3D CNN) technique for fall detection. Sport datasets were used to train the 3D CNN, which was then merged with a long short-term memory scheme. Video kinematic data were recorded and used to train a feature generator. Experiments demonstrated the effectiveness of the suggested technique for detecting falls. 100 % accuracy could be attained using the information from multiple camera fall datasets. A non-invasive fall detection system with real-time tracking using Kinect was described in [6]. The authors created a lowcomputational cost technique that depended on the head joint extracted, while the standard deviation (STDEV) formula was applied to check variation in the y-axis of head joints in every frame. The K-nearest neighbor (KNN) classification model was used to separate falls and nonfalls in home scenarios. The system achieved an accuracy of 95 %. In [7], lower body motion analysis to detect falls and near falls on stairs using computer vision and machine learning techniques was presented. Threedimensional motion sensor data were captured by a Microsoft Kinect mounted at the top of a staircase, and supervised learning algorithms were applied. Stairway ascents, descents, and falls in a laboratory were considered. The authors concluded that their proposed system achieved 92 % fall detection accuracy. 

In [2], barometric pressure and triaxial accelerometry-based fall event detection were presented. The barometric pressure sensor was used as a surrogate measure of altitude. The acceleration data are recorded using a wearable device attached to the subject’s waist. The MSP430F149, a microcontroller with a Bluetooth module, was used to acquire three acceleration signals and barometric pressure signals. The 

decision tree classifier was applied to label suspected falls. In laboratory tests, such a system showed an accuracy of 96.9 %. Wang _et al._ (2016) [8] also proposed a low-power fall detector using triaxial accelerometry and barometric pressure sensing. The authors stated that most studies on fall detection focused on detection accuracy while neglecting power efficiency and battery life. Thus, the developed fall detectors could not usually operate for a long period of time. The authors then presented a low-power fall detector that could reduce its power consumption through both hardwareand firmware-based techniques. A MSP430FR5969 microcontroller with a RFM73 transceiver was used for testing in a laboratory. Fall detectors achieved a high efficiency of 93.0 % while providing an estimated battery life of 664.9 days. 

Pierleoni _et al._ (2015) [9] proposed a fall detection system using a triaxial accelerometer, gyroscope, and magnetometer. Raw data were filtered with Madgwick’s orientation filter, and data fusion and if-else fall detection methods were applied. Data measurement in a laboratory was done using an ATmega328 microcontroller with a Bluetooth transceiver. Results indicated an average accuracy of 90.37 %. In [10], a wheelchair fall anomaly detection framework based on isolation forests and threshold-based methods was proposed. The sensor data were obtained from the tri-axial orthogonal accelerometer and gyroscope MPU6050 sensor. Sensor fusion was applied to create multi-dimensional training data from the best features selected using the ReliefF algorithm. The accuracy was up to 97.1 %. These authors also introduced a wheelchair fall detection system using unsupervised one-class support vector machines, as shown in [11], where a prototype with the inertial sensors captured trends in the sensor measurements due to wheelchair tips and falls. It was demonstrated that fall-detection accuracy was achieved up to 96 %. Makhlouf _et al._ (2019) [12] described a system for the monitoring of heart rate, fall detection, and a human’s location. The fall detection service monitored the acceleration from a tri-axial 

2 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

accelerometer placed on the person’s belt, where falls from walking or standing were considered. The heart disorder detection service monitored the person’s heart rate with a grove-ear-clip heart rate sensor placed in his or her ear. The location service uses eight photoelectric sensors placed on the four rooms’ doors. Results identified 87 % accuracy for the fall detection service. 

Implementation of a real-time classification system based on a single, waist-mounted triaxial accelerometer was introduced in [13]. The system could distinguish between periods of activity and rest. It could also detect walking and falls using the if-else conditional technique. The MSP430 microcontroller with an accelerometer and a 2.4 GHz CC2420 RF transceiver was used for laboratory-based tests. The authors reported that detection of possible falls was made with 95.6 % accuracy. A fall detection method based on wearable accelerometer data was proposed in [14]. Three public datasets have been used to validate the method, and more than 7,700 cross-disciplinary time-series features were investigated. Correlated features using the Pearson correlation coefficient, the Boruta algorithm, were applied, while different classical machine learning (ML) algorithms were employed to detect falls. Results 

using the ML classifier achieved accuracy within a range of 96 % to 100 %. Finally, Li _et al._ (2023) [15] presented a fall detection system focused on the walk-fall-still pattern. Accelerations through the wrist-worn M5StickC-Plus watch were collected, where the data were locally analyzed in the watch. Fall detection using a threshold-based method could be reported and notify service staff of accidents in one second. Moreover, the alarm signal was sent in real time to a remote healthcare system via Wi-Fi. With lab-scale testing, the system has been proven to be 90 % accurate in detecting falls. The authors concluded that the lowcost device could be used in care homes and was also suitable for elderly people living alone. 

According to the research literature discussed above, existing works have developed fall detection systems using video-based and sensorbased solutions with different focus points. In this work, the contribution and novelty are that we introduce a real-time system for monitoring and classifying human activities on stairs that employs a 2.4 GHz wireless Xbee3 micro module with a single tri-axial accelerometer sensor. Here, sensor data measurement and autonomous wireless communication systems are designed and developed, with a focus on 

**==> picture [504 x 460] intentionally omitted <==**

**Fig. 1.** Sensor measurement and wireless communication. 

3 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**==> picture [465 x 277] intentionally omitted <==**

**Fig. 1.** ( _continued_ ). 

human activities on stairs in homes: stair ascent, stair descent, turning around, and falling. For signal processing and classification, the SVM calculation, the EWMA filter for noise reduction, feature extraction with different features, and the KNN classification algorithm are applied. Experimental results indicate that the proposed system can successfully monitor human activities on stairs in real-time with high communication reliability. The system can also efficiently classify human activities on stairs, with high accuracy for human falls. 

The structure of this paper is as follows: the proposed system, including sensor data measurement and wireless communication systems, signal processing, feature extraction, and classification, is presented in Section 2. Section 3 describes the experiments and test scenarios. Results and discussion, including signal monitoring results via the proposed wireless communication system and classification results, are in Section 4. Finally, Section 5 concludes this paper. 

## **2. Proposed system** 

## _2.1. Sensor data measurement and wireless communication system_ 

The proposed system consists of the wireless communication part and the signal processing and classification part. As shown in Fig. 1, to capture the data of human activities on stairs, there are two wireless nodes using the 2.4 GHz IEEE802.15.4 XBee3 micro modules with chip antennas from SparkFun Thing Plus. One is the stationary node used as the base station (BS) node for receiving sensor data from the transmitter (Tx) node and connected to the computer as the processing center. The rest is the Tx node; this mobile node is attached to humans at the waist position of the human body [16]. The Tx node includes the accelerometer sensor, GY-521, with 3-axis acceleration data (ax, ay, and az, respectively) [17,18]. For these XBee3 micro modules, we configure a data rate of 250 kbps, 1 Mbps of serial data rate, +8 dBm of transmit power, and − 103 dBm of receiver sensitivity. The communication range for indoors is 200 ft or 60 m, approximately. The XBee nodes can communicate with the computer via I2C interfaces. The GY-521 and 

## **Table 2** 

GY-521 and XBee3 micro module specifications. 

|**Accelerometer Specifcations**||
|---|---|
|Accelerometer range|±2_g_, ±4_g_, ±8_g_, and±16_g_|
|ADC word length|16 bits|
|Interface|I2C|
|Power supply voltage|2.375 V–3.46 V|
|Accelerometer normal|500 µA|
|operating current||
|Low power accelerometer mode|10µA at 1.25 Hz, 20µA at 5 Hz, 60µA at 20 Hz,|
|current|and 110 µA at 40 Hz|
|**XBee3 micro module specifcations**||
|Operating frequency band|2.4–2.4835 GHz|
|RF data rate|250 Kbps|
|Indoor/urban range|Up to 200 ft (60 m)|
|Outdoor/line of sight range|Up to 4000 ft (1200 m)|
|Transmit power|+8 dBm (maximum power) or 6.3 mW|
|Receiver sensitivity|−103 dBm|
|Serial communications|UART, I2C|
|Supply voltage|2.6 VDC−<br>3.6 VDC|
|Operating current (transmit,|40 mA, @+3.3 V,+8 dBm|
|typical)||
|Operating current (receive,|17 mA|
|typical)||
|Power-down current, typical|2µA @ 25 ◦C|
|Number of channels|16 direct sequence channels|
||Channels 11 to 26|



XBee3 micro listed in Table 2. module specifications are In this work, the sampling rate can also be automatically and flexibly configured by users based on the resolution of the signals to be collected via a graphic user interface (GUI) window, as shown in Fig. 1(c). For this application, human activity monitoring, it is set to 100 ms. The RSSI level between Tx and BS, which represents the power level of the signal in the cases of LoS and NLoS communications, can also be monitored and evaluated. Therefore, with this proposed system, the acceleration data and the RSSI signals of the received packet can be automatically 

4 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**==> picture [455 x 522] intentionally omitted <==**

**Fig. 2.** Signal processing, feature extraction, and classification. 

measured and collected at the same time. 

For wireless communications, we select a different radio channel from the other 2.4 GHz Wi-Fi channels available in the home. This is to avoid radio signal interference and packet loss on the same radio frequency [19,20]. For the communication sequence between the Tx and the BS, we intend to configure the BS as the control unit. Here, when the BS and computer want to know the human motion information, the BS will broadcast a request packet to the Tx node that has the same ID assigned in the request packet, and a request sampling interval will also be assigned. Upon receiving the request packet, the Tx will connect to the BS and then suddenly send a reply packet as the data packet, which includes the accelerometer data, to the BS via unicast communications. The packet ID and timestamp are also added to the packet format. Also, 

it continuously sends the sensor data with the assigned sampling. In the event that the BS cannot connect to the Tx for longer than a predefined time period, it will reconnect the process again until the communication is successful. 

We note that in this work, because +8 dBm of transmit power (highest level) was chosen, the device’s maximum communication range was reached. However, network scalability and reliability should be considered when supporting larger deployments, wide areas with obstacles, and buildings with multiple floors. Relay nodes or multiple receivers can be used. In addition, to employ our devices with multiperson scenarios, additional wireless devices, new communication sequences and protocols, and optimal classification frameworks should be designed to support such a mentioned requirement. 

5 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

around, and falling, are mainly focused. There are two phases for processing: offline and online phases. In the offline phase, the measured signals of the tests 1 to n are used for determining the feature table (i.e., numerical features indicating stair ascent, stair descent, turning around, and falling) employed for the database. In the online phase, the signals from n + 1 are tested, and human activities can be automatically classified. Here, we describe the process in more detail below. 

## **Table 3** 

Numerical features applied in this work. 

|**Table 3**<br>Numerical features applied|in this work.|around, and falling, are mainly focused. There are two phases for pro-<br>cessing: offine and online phases. In the offine phase, the measured<br>il f h      d f dii h f bl i|
|---|---|---|
|Features (F)|Equations|sgnas o te tests 1 to n are use or etermnng te eature tae (.e.,|
|**F1: Mean**<br>The average value of the|_μFSVM_ =<br>1<br>_N_<br>∑_N_<br>_i FSVMi_|numerical features indicating stair ascent, stair descent, turning around,<br>and falling) employed for the database. In the online phase, the signals|
|_FSVMi_ for each window<br>period (_N_)<br>**F2: Max**|_max_(_FSVMi,_⋯_FSVMN_)|from n + 1 are tested, and human activities can be automatically clas-<br>sifed. Here, we describe the process in more detail below.|
|The maximum value of<br>the _FSVMi_ for each<br>window period||_2.2.1. Signal processing_<br>First, the raw acceleration signals (i.e.,_ax,i_,_ay,i_, and_az,i_, where_i_is the|
|**Quartile**|_Quartile_(_FSVMi_→_N,_0) = _Percentile_(_FSVMi_→_N,_0) =|sample index) will be transformed into the signal vector magnitude|
|The minimum value, the<br>25th percentile, the 50th<br>percentile, the 75th<br>percentile, and the|_min_(_FSVMi,_⋯_FSVMN_)_Quartile_(_FSVMi_→_N,_1) =<br>_Percentile_(_FSVMi_→_N,._25)_Quartile_(_FSVMi_→_N,_2) =<br>_Percentile_(_FSVMi_→_N,._50) =_median_(_FSVMi,_⋯_FSVMN_)<br>_Quartile_(_FSVMi_→_N,_3) = _Percentile_(_FSVMi_→_N,._75)|(_SVMi_), as in (1). Then, to reduce noise and variation in the raw data, the<br>widely-used exponentially weighted moving average (EWMA) flter is<br>applied to_SVMi_stream, as expressed in (2). This flter is selected because|
|maximum value of the|_Quartile_(_FSVMi_→_N,_4) =_Percentile_(_FSVMi_→_N,_1) =|the mathematical operations are simple for implementation, and it can|
|_FSVMi_ for each window|_max_(_FSVMi,_⋯_FSVMN_)_Percentile_(_FSVMi_→_N,_|provide smooth result [21]. The outputs after applying the EWMA is|
|period<br>**F3: Inter Quartile**<br>**Range (IQR)**<br>The different level|_._75) −_Percentile_(_FSVMi_→_N,._25)|_FSVMi_. The _FSVMi_ depends on the previous smoothed value (_FSVMi_−1)<br>and the recent input (_SVMi_) multiplied by the weighting factor<br>(0≤_α_≤1). The weight is close to 0, the _FSVMi_−1 plays a role in the|
|between the 75th<br>percentile and the 25th<br>percentile<br>**F4: Standard deviation;**<br>The amount of variation<br>in the _FSVMi_ for each|_σFSVM_ =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>1<br>_N_<br>∑_N_<br>_i_ (_FSVMi_ −_μFSVM_)2<br>√|calculation. If it is close to 1, the recent input has a higher priority. In<br>this work,_α_is varied in the experiments to fnd the optimal value. Based<br>on our tests, _α_=0_._3 obtained the best result, as shown in (3). For the<br>derivation of (2) to the general form, it is also shown in (4), where the<br>weighting for each older datum decreases exponentially.|
|window period<br>**F5: Variance;**<br>The square of the|_σFSVM_2 =<br>1<br>_N_<br>∑_N_<br>_i_ (_FSVMi_ −_μFSVM_)2|_SVMi_ =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅**̅**<br>(<br>_ax,i_2 +_ay,i_2 +_az,i_2)<br>√<br>(1)|
|standard deviation|||
|**F6: Peak to Peak (Range;**|_max_(_FSVMi,_⋯_FSVMN_) −_min_(_FSVMi,_⋯_FSVMN_)|_FSVMi_ = (_α_×_SVMi_) + (1−_α_) ×_FSVMi_−1<br>(2)|
|**Max-Min)**|||
|The range between the||_FSVMi_ = (0_._3×_SVMi_) + (0_._7×_FSVMi_−1)<br>(3)|
|maximum and the|||
|minimum values of the|||
|_FSVMi_ for each window|||
|period|||



_FSVMi_ = _α_ × _SVMi_ + (1 − _α_ ) × _FSVMi_ − 1 = _α_ × _SVMi_ + (1 − _α_ ) × [ _α_ × _FSVMi_ − 1 + (1 − _α_ ) × _FSVMi_ − 2 ] = _α_ × _SVMi_ + _α_ × (1 − _α_ ) × _FSVMi_ − 1 + (1 − _α_ )[2] × _FSVMi_ − 2 = _α_ × _SVMi_ + _α_ × (1 − _α_ ) × _FSVMi_ − 1 + (1 − _α_ )[2] × [ _α_ × _FSVMi_ − 2 + (1 − _α_ ) × _FSVMi_ − 3 ] = _α_ × _SVMi_ + _α_ × (1 − _α_ ) × _FSVMi_ − 1 + _α_ × (1 − _α_ )[2] × _FSVMi_ − 2 + (1 − _α_ )[3] × _FSVMi_ − 3 

## _2.2. Signal processing, feature extraction, and classification_ 

After the computer receives the sensor information, the data will be forwarded to the second part, which includes signal processing, feature extraction, and classification, as shown in Fig. 2. In this figure, four human activities on stairs, including stair ascent, stair descent, turning 

**==> picture [252 x 37] intentionally omitted <==**

## **Table 4** 

all features. Classification for 

|**able 4**<br>lassifcation for all features.||||
|---|---|---|---|
|_DF_1 to_DFk_|_DF_1→<br>{<br>_DF_1_,_1_, DF_1_,_2_, DF_1_,_3_, DF_1_,_4<br>}<br>_DF_2→<br>{<br>_DF_2_,_1_, DF_2_,_2_, DF_2_,_3_, _|_DF_2_,_4<br>}<br>…_DFk_→<br>{|_DFk,_1_, DFk,_2_, DFk,_3_, DFk,_4<br>}|
|_DF_1_,_1 to_DFk,_1|_DF_1_,_1 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>(<br>_F_1_i_ −_F_1_,_1<br>)2<br>√<br>,_DF_1_,_2 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>(<br>_F_1_i_ −_F_1_,_2<br>)2<br>√<br>_,DF_1_,_3 =|̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>(<br>_F_1_i_ −_F_1_,_3<br>)2<br>√<br>,|_DF_1_,_4 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>(<br>_F_1_i_ −_F_1_,_4<br>)2<br>√|
||_DF_2_,_1 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>(<br>_F_2_i_ −_F_2_,_1<br>)2<br>√<br>,_DF_2_,_2 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>(<br>_F_2_i_ −_F_2_,_2<br>)2<br>√<br>_,DF_2_,_3 =|̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>(<br>_F_2_i_ −_F_2_,_3<br>)2<br>√<br>,|_DF_2_,_4 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅<br>(<br>_F_2_i_ −_F_2_,_4<br>)2<br>√|
||…|||
||_DFk,_1 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅**̅**<br>(<br>_Fki_ −_Fk,_1<br>)2<br>√<br>, _DFk,_2 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅**̅**<br>(<br>_Fki_−_Fk,_2<br>)2<br>√<br>_,DFk,_3 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅**̅**<br>(<br>_Fki_ −_Fk,_3<br>)2<br>√<br>,_DFk,_4 =<br>̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅**̅**<br>(<br>_Fki_−_Fk,_4<br>)2<br>√|||
|_DF_1_,min_ to_DFk,min_<br>Classifcation for_F_(1→_k_)_,i_|_DF_1_,min_ = _min_(_DF_1_,_1_,DF_1_,_2_,DF_1_,_3_,DF_1_,_4)_DF_2_,min_ = _min_(_DF_2_,_1_,DF_2_,_2_,DF_2_,_3_,DF_2_,_4)…_DFk,min_ =_min_(_DFk,_1_,DFk,_2_,DFk,_3_,DFk,_4)<br>⎧<br>⎪<br>⎪<br>⎨<br>⎪<br>⎪<br>⎩<br>_IfDF_(1→_k_)_, min_ =_DF_(1→_k_)_,_1→_Stairascent_;1<br>_IfDF_(1→_k_)_,min_ =_DF_(1→_k_)_,_2→_Turningaround_;2<br>_IfDF_(1→_k_)_,min_ =_DF_(1→_k_)_,_3→_Stairdescent_;3<br>_ELSE, DF_(1→_k_)_,min_ =_DF_(1→_k_)_,_4→_Falling_;4|||



6 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**==> picture [455 x 610] intentionally omitted <==**

**Fig. 3.** Illustration of test environments, devices, and human activities. 

7 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**==> picture [455 x 228] intentionally omitted <==**

**==> picture [455 x 37] intentionally omitted <==**

**Fig. 3.** ( _continued_ ). 

## _2.2.2. Feature extraction_ 

After signal filtering, feature extraction is then performed to transform raw data (i.e., at this stage, the filtered data) into numerical features. Therefore, each human activity will be indicated by each selected feature. In this work, six commonly used features are applied, including the mean value, the maximum value, the interquartile range (IQR), the standard deviation (STDEV), the variance, and the peak-to-peak amplitude. Their mathematical equations are demonstrated in Table 3. 

We note that each feature will be calculated from the data in every window period (i.e., 15 samples per window). When the output is decided, the window will be moved up one step (or one sample). With this solution, a stream of features will be obtained, and each feature result can be sent to the classification process continuously. We note that this is for the online phase, which is slightly different from the offline phase. In the offline phase, before feature calculation, the segmentation process is applied to separate and mark each human activity. If the raw signal consists of four durations of human activities, the four durations will be separated, and the features of each duration will be calculated. A feature table can be obtained and used as the database. We also note that, as demonstrated in Fig. 2, the signals of the tests 1 to n are used for feature table calculation. Each feature, like F1,1 (i.e., feature 1 for the activity ①), is the average value from all F1,1 of the tests 1 to n. 

## _2.2.3. Classification_ 

As mentioned above, in the online phase, starting with the signal n + feature’s data will be 1, it is applied for testing and classification. Each compared with the database listed in the feature table, where the different levels between them are determined. For example, as in Fig. 2 and Table 3, if _F_ 1 refers to the mean feature (see Table 3, F1 to F6, where _k_ = 6) and _F_ 1 _,_ 1 to _F_ 1 _,_ 4 are the mean features for stair ascent, turning around, stair descent, and falling stored in the database, the difference between _F_ 1 _i_ (i.e., the mean feature of the window _i_ calculated during the test in the online phase) and _F_ 1 _,_ 1 to _F_ 1 _,_ 4 are determined. Therefore, four values of different levels ( _DF_ 1 _,_ 1 to _DF_ 1 _,_ 4) are obtained, as expressed in (5). By finding the minimum value ( _DF_ 1 _,min_ ) among _DF_ 1 _,_ 1 to _DF_ 1 _,_ 4 in (6), the KNN classification result of each sample can be obtained, as expressed in (7) [22,23]. We define that 1 to 4 in (7) refer to stair ascent, 

turning around, stair descent, and falling, respectively. Such numbers will be used to indicate classification results and determine classification accuracy. All equations for F1 (mean feature) to F6 (peak to peak feature) are also provided in Table 4. 

**==> picture [111 x 11] intentionally omitted <==**

**==> picture [252 x 94] intentionally omitted <==**

**==> picture [252 x 58] intentionally omitted <==**

## **3. Experiments and test scenarios** 

The experiments have been conducted in home environments in HatYai city, Songkhla, Thailand, as demonstrated in Fig. 3. In this home, there is 2.4 GHz Wi-Fi to be used as a general standard for other homes. There are two floors with a staircase (19 levels, or 20 steps of walking). A man who performs the test is the healthy subject, with an age of 22 years, a height of 173 cm, and a weight of 63 kg. The Tx node, the mobile node with the accelerometer sensor, was belted on the waist of the subject [23], while the BS node was connected to the computer as the monitoring center located on the first floor. Thus, the communication between the mobile node and the BS can be both LoS and NLoS communications. We also ensure that there is no signal interference from WiFi channels in the home environments and surroundings, since we 

8 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

initially check them by using the Wi-Fi analyzer software and configure different channels to our device. 

We should mention that at the beginning of our investigation, two cases were tested. First, the Tx node, which had the GY-521 accelerometer sensor, was attached to the subject’s waist. Second, it was attached to the chest, with the ax, ay, and az directions fixed to the same. We acquired well-measured 3-axis acceleration signals. However, from the user’s perspective, the sensor linked to the waist is more convenient to operate. The waist location was then determined. Since there were several tests, the sensor positioning at the subject’s waist was marked during the experiments. 

For the test scenario, the subject is ascending stairs (with 19 levels, or 20 steps of walking) to the second floor and then turning around to descend the stairs. The subject then suddenly falls while reaching the first floor. We also protect any subject’s dangerous during falls by 

providing a thick mattress for safety. Additionally, at the beginning of our research, the subject was described and asked for permission to allow and perform the test, and he agreed to participate in the research study. We defined that the subject could stop the test if he had any accidents or injuries during testing. We note that the use of a thick mattress for safety during the simulated falls in our experiments may affect the realism of the falls, especially in terms of how the sensor data captures the dynamics of an actual fall. The described test pattern was repeated twenty times, and the experiment took twenty days at different times during the day and night. This is also for the subject’s safety, especially if he falls on stairs. Sixteen tests were for the database calculation, and the rest were for testing and classification (i.e., 80 % for the database calculation and 20 % for testing). 

The research assumptions for our test are that the suggested system given in Section 2.1 will function well by giving real-time three-axis 

**==> picture [455 x 502] intentionally omitted <==**

**Fig. 4.** Illustration of 3-axis acceleration, SVM, and FSVM signals. 

9 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**==> picture [455 x 583] intentionally omitted <==**

**Fig. 4.** ( _continued_ ). 

10 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**==> picture [455 x 185] intentionally omitted <==**

**Fig. 4.** ( _continued_ ). 

acceleration data. These sensor data are successfully sent from the transmitter to the reviewers using the developed wireless communication protocol, which has a high packet delivery ratio and a small end-toend delay. Furthermore, the filtering approach, feature extraction, and KNN classification methods can produce good classification accuracy when separating human actions such as stair ascent, turning around, stair descent, and falling. 

## **4. Experimental results and discussion** 

## _4.1. Signal monitoring results via the proposed wireless communication system_ 

The experimental results, including the 3-axis accelerometer data, the SVM signals, and the FSVM signals, are shown in Fig. 4. We note that tests #3 and #6 are demonstrated as examples. Also, by applying the EWMA filter to the SVM signal, the output or FSVM results, as shown in Fig. 4(c), are more clear and stable. The results here indicate that the accelerometer, SVM, and FSVM signals can represent human activities. Each human activity on the stairs has its own characteristic. For example, in test #3, the signals follow the following patterns: stair ascent (i.e., sample numbers 100–280, approximately), turning around (i.e., sample numbers 280–335, approximately), stair descent (i.e., sample numbers 336–525, approximately), and falling (i.e., from the sample numbers 526, approximately). Additionally, the signals fluctuate corresponding to the walking step (human gait pattern) when the man walks up the stair with 20 steps and goes down the stair with 20 steps. Also, the amplitude of signals during walking down is higher than in the case of walking up, and the peak-to-peak amplitude of signals is high during the man’s fall to the ground. Finally, both 3-axis acceleration and SVM signals become stable at certain levels after falling and lying down on the ground. 

Related to Fig. 4, the RSSI signals that represent the power level of the signal from LoS and NLoS communications in the home environment are also illustrated in Fig. 5. As seen in the figure, when the man moves (goes up the stairs) far from the BS, which is located on the first floor, the trend of the RSSI level is getting lower (weak signal level). Also, when he moves back to the starting position (goes down the stairs), the RSSI then increases and returns back to the original level, approximately (strong signal level). We can also observe that the RSSI signals fluctuate due to the mobile node communications (i.e., dynamic events) and the multipath effects in the stair environment. In addition, after the man falls and is stationary on the ground, the RSSI is also stable at a certain level for a period of time. From these results, we believe that the RSSI signal pattern, as the metric from the wireless communication part, can be 

useful for this monitoring and classification application, but it should be more thoroughly tested and investigated. 

In this work, although the experiments were tested in the NLoS scenario, the obtained RSSI levels, as seen in Fig. 5, are quite strong, which is related to the acceptable level of the packet error rate. The RSSI levels in this work are approximately above − 90 dBm, where the receiver sensitivity of the XBee3 micro module is − 103 dBm. According to these results, we found that the packet delivery ratio (PDR), defined as the ratio of the total number of packets successfully received at the BS to the total number of packets sent by the Tx [24], reaches 100 %, as shown in Table 5. The PDR indicates the level of delivery data to the BS and can directly represent communication reliability [25]. Furthermore, in Fig. 6, we also show the timestamp of each received packet measured at the BS for test #3. Since the sampling rate of the Tx is set to 100 ms, the total time or the end-to-end delay for sending the first packet (1) to the last packet (800) should be 80,000 ms (i.e., 800 * 100 ms, 80.00 s, or 1.333 minus). Experimental results here indicate that the timestamp of the final packet is 84399 ms, as in Fig. 6. Therefore, the end-to-end delay is equal to 84.93 s, or 1.415 minus, which indicates the response time of the proposed system. 

## _4.2. results Classification_ 

The results of the human activities on stairs obtained classification by each feature are demonstrated in Fig. 7. The classification accuracy is the ratio between the total number of correct predicted results and the total number of samples for each activity. The experimental results indicate that the variance feature provides the highest accuracy on average. The classification accuracy is 89 % for stair ascent, 95 % for turning around, 70 % for stair descent, and 100 % for falling. Thus, the average result is 88 % with a lowest confidence interval. Considering these results, the accuracy is quite high for the cases of turning around and falling. The accuracy for stair ascent (89 %) is lower than those two cases because sometimes the system predicts stair descent instead. For stair descent, the system gives the lowest classification accuracy. This is because the variance feature in the case of stair descent is between the stair ascent and the fall. Thus, the system predicts stair ascent and falls sometimes. This is so challenging for classification in this case. However, for this considered scenario, we can achieve monitoring and detecting falls on stairs in real-time with 100 % classification accuracy and 100 % wireless communication reliability when only one feature is applied. This claims the potential and contribution of our proposed system to possibly be used for smart home and healthcare applications. 

We note that the findings in Fig. 7 demonstrate that our suggested system can use the STDEV, VAR, and PTP features to classify human fall 

11 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**==> picture [455 x 508] intentionally omitted <==**

**Fig. 5.** Illustration of raw RSSI signals collected from tests #3 and #6. 

## **5. Conclusions** 

## **Table 5** 

|**Table 5**||
|---|---|
|Packet delivery ratio.||
|Communication reliability|Results|
|Average packet delivery ratio|100 %|



(class 4) with an accuracy of 100 %. But according to our investigations, the system occasionally classifies stair descent (class 3) as class 4. This indicates that a more efficient solution should be applied to address this issue. 

A real-time system for monitoring and classifying human activities on stairs using 2.4 GHz XBee3 micro modules with a single tri-axial accelerometer sensor is introduced in this work. Sensor data measurement and wireless communication systems are developed while human activities on stairs, including stair ascent, stair descent, turning around, and falling, are focused. For signal processing and classification, the SVM calculation, signal filtering using EWMA, feature extraction using various features, and classification using the K-nearest neighbors algorithm are applied. Experimental results demonstrate that the proposed system can efficiently monitor human activities on stairs in real-time with a PDR of 100 % for NLoS communications. The re- classification sults using only one variance feature and the K-nearest neighbor 

12 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

**==> picture [398 x 202] intentionally omitted <==**

**Fig. 6.** Example of the timestamp of each received packet for test #3; the end-to-end delay is 84.93 s. 

**==> picture [455 x 261] intentionally omitted <==**

**Fig. 7.** Classification results of human activities on stairs. 

classifier obtain 88 % average accuracy, where the system achieves 100 % accuracy to monitor and classify falls on stairs. Therefore, our system has the potential to monitor and classify human activities on stairs with wireless communication and can be deployed for smart home and healthcare scenarios. 

In future work, to enhance the reliability and robustness of the proposed system and method, more diverse subjects with different demographic factors, including age, gender, and physical conditions, should be taken into account for testing. More subjects will be asked to perform the experiments and data collection with varied environmental conditions. The proposed system should account for dynamic environmental changes such as different stair layouts, staircase levels, number of floors, variations in lighting, obstacles on stairs, and stair fall positions. Feature extraction and classification using multiple sensors, features, and classifiers will be investigated. Other critical human activities, 

such as slipping and tripping, to support the full option of healthcare scenarios, will be taken into consideration. Finally, sensor failure and communication breakdown of the system should be studied, and the Internet of Things (IoT) should be applied to this system for greater utilization. 

## **Human ethics and consent to participate declarations** 

The analysis of the recorded data was conducted using completely anonymous data. The experimental study did not involve any invasive or medical procedures. All subjects gave their informed consent prior to the collection and acquisition of the data, which was carried out in compliance with the ethical principles of the Helsinki Declaration. Also, the participants’ identities were kept confidential. 

13 

_A. Booranawong et al._ 

_Egyptian Informatics Journal 30 (2025) 100643_ 

## **Consent for publication** 

All authors have agreed to submit the paper for publication. 

## **CRediT authorship contribution statement** 

**Apidet Booranawong:** Writing – review & editing, Writing – original draft, Methodology, Investigation, Conceptualization. **Sittiporn Sukveeraphan:** Writing – review & editing, Methodology, Investigation, Conceptualization. **Liangrui Pan:** Writing – review & editing, Supervision. **Nattha Jindapetch:** Writing – review & editing, Supervision. **Pornchai Phukpattaranont:** Writing – review & editing, Supervision. **Hiroshi Saito:** Writing – review & editing, Supervision. 

## **Funding** 

Faculty of Engineering, Prince of Songkla University. 

## **Declaration of competing interest** 

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper. 

## **Acknowledgements** 

This work was supported by the Faculty of Engineering, Prince of Songkla University, Thailand, and the University of Aizu, Japan. 

## **Data availability** 

Data generated or analyzed during this study are included in this published article. 

## **References** 

- [1] Lapierre N, Neubauer N, Miguel-Cruz A, Rincon AR, Liu L, Rousseau J. The state of knowledge on technologies and their use for fall detection: a scoping review. Int J Med Inf 2018;111:58–71. 

- [2] Bianchi F, Redmond SJ, Narayanan MR, Cerutti S, Lovell NH. Barometric pressure and triaxial accelerometry-based falls event detection. IEEE Trans Neural Syst Rehabil Eng 2010;18(6):619–27. 

- [3] Lu N, Wu Y, Feng L, Song J. Deep learning for fall detection: three-dimensional CNN combined with LSTM on video kinematic data. IEEE J Biomed Health Inform 2018;23(1):314–23. 

- [4] Bet P, Castro PC, Ponti MA. Fall detection and fall risk assessment in older person using wearable sensors: a systematic review. Int J Med Inf 2019;130:103946. 

- [5] Kavuncuoglu˘ E, Uzunhisarcıklı E, Barshan B, Ozdemir[¨] AT. Investigating the Performance of Wearable Motion Sensors on recognizing falls and daily activities via machine learning. Digital Signal Process 2022;126:103365. 

- [6] Mansoor M, Amin R, Mustafa Z, Sengan S, Aldabbas H, Alharbi MT. A machine learning approach for non-invasive fall detection using Kinect. Multimed Tools Appl 2022;81(11):15491–519. 

- [7] Parra-Dominguez GS, Snoek J, Taati B, Mihailidis A. Lower body motion analysis to detect falls and near falls on stairs. Biomed Eng Lett 2015;5:98–108. 

- [8] Wang C, Lu W, Narayanan MR, Chang DCW, Lord SR, Redmond SJ, et al. Lowpower fall detector using triaxial accelerometry and barometric pressure sensing. IEEE Trans Ind Inf 2016;12(6):2302–11. 

- [9] Pierleoni P, Belli A, Palma L, Pellegrini M, Pernini L, Valenti S. A high reliability wearable device for elderly fall detection. IEEE Sens J 2015;15(8):4544–53. 

- [10] Yousuf S, Kadri MB. A ubiquitous architecture for wheelchair fall anomaly detection using low-cost embedded sensors and isolation forest algorithm. Comput Electr Eng 2023;105:108518. 

[11] Sheikh SY, Jilani MT. A ubiquitous wheelchair fall detection system using low-cost embedded inertial sensors and unsupervised one-class SVM. J Ambient Intell Hum Comput 2023;14(1):147–62. 

[12] Makhlouf A, Boudouane I, Saadia N, Ramdane Cherif A. Ambient assistance service for fall and heart problem detection. J Ambient Intell Hum Comput 2019;10: 1527–46. 

- [13] Karantonis DM, Narayanan MR, Mathie M, Lovell NH, Celler BG. Implementation of a real-time human movement classifier using a triaxial accelerometer for ambulatory monitoring. IEEE Trans Inf Technol Biomed 2006;10(1):156–67. 

- [14] Al Nahian MJ, Ghosh T, Al Banna MH, Aseeri MA, Uddin MN, Ahmed MR, et al. Towards an accelerometer-based elderly fall detection system using crossdisciplinary time series features. IEEE Access 2021;9:39413–31. 

- [15] Li S. Fall detection with wrist-worn watch by observations in statistics of acceleration. IEEE Access 2023;11:19567–78. 

- [16] Ozdemir[¨] AT. An analysis on sensor locations of the human body for wearable fall detection devices: Principles and practice. Sensors 2016;16(8):1161. 

- [17] Muangprathub J, Sriwichian A, Wanichsombat A, Kajornkasirat S, Nillaor P, Boonjing V. A novel elderly tracking system using machine learning to classify signals from mobile and wearable sensors. Int J Environ Res Public Health 2021;18 (23):12652. 

- [18] Ribeiro O, Gomes L, Vale Z. IoT-Based human fall detection system. Electronics 2022;11(4):592. 

- [19] Booranawong A, Jindapetch N, Saito H. A system for detection and tracking of human movements using RSSI signals. IEEE Sens J 2018;18(6):2531–44. 

- [20] Booranawong A, Sengchuai K, Buranapanichkit D, Jindapetch N, Saito H. RSSIbased indoor localization using multi-lateration with zone selection and virtual position-based compensation methods. IEEE Access 2021;9:46223–39. 

- [21] Booranawong A, Sengchuai K, Jindapetch N. Implementation and test of an RSSIbased indoor target localization system: Human movement effects on the accuracy. Measurement 2019;133:370–82. 

- [22] Liu KC, Hsieh CY, Huang HY, Hsu SJP, Chan CT. An analysis of segmentation approaches and window sizes in wearable-based critical fall detection systems with machine learning models. IEEE Sens J 2019;20(6):3303–13. 

- [23] Usmani S, Saboor A, Haris M, Khan MA, Park H. Latest research trends in fall detection and prevention using machine learning: a systematic review. Sensors 2021;21(15):5134. 

- [24] Cheng CH, Ho CC. Implementation of multi-channel technology in ZigBee wireless sensor networks. Comput Electr Eng 2016;56:498–508. 

- [25] Misra S, Roy SK, Roy A, Obaidat MS, Jha A. MEGAN: multipurpose energyefficient, adaptable, and low-cost wireless sensor node for the internet of things. IEEE Syst J 2019;14(1):144–51. 

14 

