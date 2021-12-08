import pandas as pd 
import numpy as np
import statistics as math
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

##### Fairness metrics
def fairness_metric_basic(bw1, bw2):
    return float(bw1/bw2)

def fairness_metric_jain(bw1, bw2):
    numerator = (bw1+bw2)**2
    denominator = 2*(bw1**2 + bw2**2)
    return float(numerator/denominator)

def fairness_metric_ours(bw1, bw2):
    d = bw1 + bw2
    return max(float(bw1/d), float(bw2/d))

def compute_stats (fairness):
    '''
    Takes as input an array of real numbers
    and returns the average and standard deviation
    of the numbers
    '''
    avg_fairness = []
    std_fairness = []
    for i in range(len(fairness)):
        avg_fairness.append(math.mean(fairness[i]))
        std_fairness.append(math.stdev(fairness[i]))
    return (avg_fairness, std_fairness)

def unit_conversion(v, u):
    if u == "Kbits/sec":
        return v * 0.001
    elif u == "bits/sec":
        return v * 0.000001
    else:
        return v
    

def compute_fairness(data, metric):
    '''
    Takes multiple TCP runs data as input and computes the
    fairness metric on the runs.
    '''
    TCP_runs = data.TCP_Type.unique()
    
    fairness_basic = []
    fair_subarray_b = []
    
    avg_tput_A = []
    avg_tput_C = []
    num_runs = 5
    
    for i in range(len(TCP_runs)):
        bw_col = data[data["TCP_Type"] == TCP_runs[i]]
        A_bw_avg = bw_col["Bandwidth - A"].mean()
        C_bw_avg = bw_col["Bandwidth - C"].mean()
        avg_tput_A.append(A_bw_avg)
        avg_tput_C.append(C_bw_avg)
        fair_subarray_b.append(metric(A_bw_avg, C_bw_avg))
        if i%num_runs == (num_runs-1):
            fairness_basic.append(fair_subarray_b)
            fair_subarray_b = []
    return fairness_basic



def timeseries_plot(data, run, title):
  
    unfair= data[data["TCP_Type"] == run]
    bw_A = unfair["Bandwidth - A"]
    bw_C = unfair["Bandwidth - C"]
    time = unfair["Time"]

    plt.plot(time, bw_A, label="TCP Reno", color="red")
    plt.plot(time, bw_C, label="TCP Illinois", color="blue")
    plt.title(title)
    plt.ylabel('Bandwidth (Mbps)')
    plt.xlabel("Time (seconds)")
    plt.legend()
    plt.show()


def make_table(A, num_comb, std=False):
    '''
    Takes an array A = [a,b,c,d,e,f] 
    and returns B = [[a,b,c], [d, e], [f]]
    '''
    B = np.ones((num_comb, num_comb))
    index = 0
    for i in range(num_comb):
        for j in range(i, num_comb):
            B[i][j] = A[index]
            if std:
                B[j][i] = B[i][j]
            else:
                B[j][i] = float(1/B[i][j])
                
            index +=1
    return B
  
    
############ HEATMAP ################
def make_heatmap(data, stdev, distance, threshold, title):
    
    TCP_versions=["Reno", "Westwood", "Illinios"]
    fig, ax = plt.subplots()
    
    # Show all ticks and label them with the respective list entries
    ax.set_xticks(np.arange(len(TCP_versions)))
    ax.set_yticks(np.arange(len(TCP_versions)))
    
    ax.set_xticklabels(TCP_versions)
    ax.set_yticklabels(TCP_versions)
    
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")
    textcolors = ["k", "w"]
    
    # Loop over data dimensions and create text annotations.
    for i in range(len(TCP_versions)):
        for j in range(len(TCP_versions)):
            ax.text(j, i, str(data[i, j]) +  u"\u00B1" + str(stdev[i, j]),
                           ha="center", va="center", color=textcolors[distance[i,j]> threshold])
    
    ax.set_title(title)
    fig.tight_layout()
    plt.imshow(distance, cmap='Greens')
    plt.show()
    
    
# Read in the file, do some housekeeping
data = pd.read_csv("WorkingDemo.csv")
data = data.rename(columns={"Unnamed: 0": "TCP_Type", "Unnamed: 1": "Time", "Bandwidth Unit - A": "BW_unit_A", "Bandwidth Unit - C": "BW_unit_C"})
data = data[data['Time']<20]

## Convert bandwidth units from Kbits/sec to Mbits/sec
data['Bandwidth - A'] = data.apply(lambda x: unit_conversion(x['Bandwidth - A'], x['BW_unit_A']), axis=1)
data['BW_unit_A'] = data.apply(lambda x: "Mbits/sec", axis=1)
data['Bandwidth - C'] = data.apply(lambda x: unit_conversion(x['Bandwidth - C'], x['BW_unit_C']), axis=1)
data['BW_unit_C'] = data.apply(lambda x: "Mbits/sec", axis=1)
 
## Compute fairness of the TCP connections   
fairness_basic = compute_fairness(data, fairness_metric_basic)
(basic_avg, basic_std) = compute_stats(fairness_basic)

## Make timeseries plot of an interesting run
timeseries_plot(data, "reno/illinois:4", "Bandwidth Over Time for TCP Reno vs TCP Illinois \n Topology 2, 1990's Internet")

#### Make heatmap plot of all runs    
basic_avg2 = np.around(make_table(basic_avg, 3), decimals=2)
basic_std = np.around(make_table(basic_std, 3, std=True), decimals=2)

## Make subplot to set the color scheme
basic_color = np.around(make_table(basic_avg, 3, std=True), decimals=2)
basic_distance = np.abs(np.ones((3,3)) - basic_color)



make_heatmap(basic_avg2,  basic_std, basic_distance, 0.3, "Throuput Ratio Fairness of TCP Types \n Topology 2, 1990's Internet")




