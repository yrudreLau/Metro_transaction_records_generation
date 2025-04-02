# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 11:42:22 2025

@author: Admn
"""

import numpy as np
import pandas as pd
import random

def gaussian(x, mu, sigma):
    return np.exp(-(x-mu)**2/(2*sigma**2))/(np.sqrt(2*np.pi)*sigma)

def generate_gaussian(mean, sigma, data_num):
    return sigma * np.random.randn(data_num) + mean

def intervals_discrete(data, length):
    lower = int(int(data.min()/length)*length)
    # print('lower--', lower)
    upper = int(int(data.max()/length+1)*length)
    # print('upper--', upper)
    discrete_intervals = np.linspace(lower, upper, int((upper - lower)/length+1))
    # print(discrete_intervals)
    
    return discrete_intervals
# for i in range(interval_nums):
    
def test_count(x, discrete_intervals):
    # print('inter--', discrete_intervals)
    for ii in range(int(discrete_intervals.shape[0])-1):
        # print('---')
        if x >= discrete_intervals[ii] and x < discrete_intervals[ii+1]:
            x = (discrete_intervals[ii] + discrete_intervals[ii+1])/2
            break
        else:
            pass
   
    return x
    
def main(paths_frac, signal_path_frac, entry_time_mean, entry_time_sigma, in_vehicle_time_mean, \
         in_vehicle_time_sigma, egress_time_mean, egress_time_sigma, transfer_time_mean, \
             transfer_time_sigma, length, tapinend, pax_num, err):
    afc_syn = pd.DataFrame()

    afc_syn['pax_id'] = np.arange(pax_num)

    ori = 9
    des = 17
    afc_syn['origin'] = ori

    afc_syn['destination'] = des

    afc_syn['tap_in'] = np.random.randint(0, tapinend, pax_num, int)

    afc_syn['path_id'] = 1

    afc_syn['mobile_tag'] = 1

    index_num = pax_num*paths_frac*signal_path_frac
    od_path_num = int(paths_frac[0]*pax_num)

    index = np.arange(pax_num).tolist()
    
    od_path_index = random.sample(index, od_path_num)
    
    afc_syn['path_id'].loc[od_path_index] = 0

    
    od_path1_mobile = random.sample(od_path_index, int(index_num[0]))
    od_path2_mobile = random.sample(afc_syn[afc_syn.path_id==1]['pax_id'].values.tolist(), int(index_num[1]))

    afc_syn['mobile_tag'].loc[od_path1_mobile] = 0
    afc_syn['mobile_tag'].loc[od_path2_mobile] = 0

    afc_syn['travel_time'] = 0
    
    real_path_journey_time_mean = []
    real_path_journey_time_sigma = []
    for i in range(len(in_vehicle_time_mean)):
        mean = entry_time_mean[i] + in_vehicle_time_mean[i] + transfer_time_mean[i] + egress_time_mean[i]
        sigma = np.sqrt(entry_time_sigma[i]**2 + in_vehicle_time_sigma[i]**2 + transfer_time_sigma[i]**2 + egress_time_sigma[i]**2)
        real_path_journey_time_mean.append(mean)
        real_path_journey_time_sigma.append(sigma)

    path_journey_time_mean_err = np.array(real_path_journey_time_mean)
    path_journey_time_sigma_err = np.array(real_path_journey_time_sigma)*(1+err)

    afc_syn['travel_time'].loc[afc_syn.path_id==0 ] = generate_gaussian(path_journey_time_mean_err[0], path_journey_time_sigma_err[0], od_path_num).round(0)
    afc_syn['travel_time'].loc[afc_syn.path_id==1] = generate_gaussian(path_journey_time_mean_err[1], path_journey_time_sigma_err[1], pax_num - od_path_num).round(0)
   
    ### discrete travel time
    
    od_observed_travel_time = afc_syn['travel_time'].values

    afc_syn['Journety_time_interval_median'] = afc_syn.travel_time.apply(lambda x: test_count(x, intervals_discrete(od_observed_travel_time, length)))
    od_x_series = afc_od.probability_count.value_counts(True, True, False).sort_index().index
    od_probs = afc_od.probability_count.value_counts(True, True, False).sort_index().values
    time_intervals = od_x_series
                 
    norm = []
    for i in range(len(path_journey_time_mean_err)):
        norm.append(gaussian(time_intervals, real_path_journey_time_mean[i], real_path_journey_time_sigma[i]))
    
    theta = signal_path_frac[0]*(norm[0]-norm[1])

                
    return afc_syn, norm, theta

if __name__ == '__main__':
    
    # example parameters
    np.random.seed(42)
    pax_num = 500
    
    in_vehicle_time_mean = [1369, 1382, 1398, 1465]
    in_vehicle_time_sigma = [30, 30, 30, 30]
    transfer_time_mean = np.array([0, 628.68, 0, 619.61])
    transfer_time_sigma = np.array([0, 320.78, 0, 318.77])
    entry_time_mean = np.array([227.57, 186.34, 165.49, 165.49])
    entry_time_sigma = np.array([98.99, 70.72,  83.25, 83.25])
    egress_time_mean = np.array([150.23,  150.23, 148.07, 134.51])
    egress_time_sigma = np.array([110.76, 110.76, 112.84, 89.63])
    
    paths_frac = np.array([0.8, 0.2, 0.85, 0.15])
    
    # paths_penetration = np.array([0.2, 0.9, 0.2, 0.2])
    signal_path_frac = np.array([0.2, 0.8, 0.1, 0.9 ])
    length = 50
    tapinend = 1920
    err = [0.1, -0.1]
    

    generated_afc_list = []
    for e in err:
        generated_afc = main(paths_frac, signal_path_frac, entry_time_mean, entry_time_sigma, in_vehicle_time_mean, \
                             in_vehicle_time_sigma, egress_time_mean, egress_time_sigma, transfer_time_mean, \
                             transfer_time_sigma, length, tapinend, pax_num, e)
        generated_afc_list.append(generated_afc)

    
    
