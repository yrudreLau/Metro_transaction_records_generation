# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 17:07:09 2025

@author: Admn
"""

import numpy as np
from scipy import optimize

def main(od_probs, thetas, norms, initial_fracs, signal_path_fracs, initial_alphas, true_paths_fracs):

    def objective_fun(x, od_probs, thetas, norms, initial_fracs, signal_path_fracs, ):
        z = 0
        od_num = len(od_probs)
        for i in range(od_num):
            path_num = len(od_probs[i])
            for j in len(path_num):
                z += od_probs[i]*np.log(x[i]*thetas[i][j]+norms[i][j])
        return -z
    
    
    fx0 = initial_fracs
    cons = ( # xyz=1
            {'type': 'ineq', 'fun': lambda x: x[0] - 0.0}, # x>=e，即 x > 0
            {'type': 'ineq', 'fun': lambda x: -x[0] + (1/signal_path_fracs[0])},
            {'type': 'ineq', 'fun': lambda x: x[1] - 0.0},
            {'type': 'ineq', 'fun': lambda x: -x[1] + (1/signal_path_fracs[2])}
           )
    
    res = optimize.minimize(objective_fun, fx0, method='SLSQP',options={'xatol': 1e-6, 'disp': True}, constraints=cons)
    print(res.x, initial_alphas, (res.x-np.array([initial_alphas[0], initial_alphas[2]]))/np.array([initial_alphas[0], initial_alphas[2]]))
    synthetic_estimate_alpha = np.array([res.x[0], (1-res.x[0]*signal_path_fracs[0])/signal_path_fracs[1], \
                                         res.x[1], (1-res.x[1]*signal_path_fracs[2])/signal_path_fracs[3]])
    err = (synthetic_estimate_alpha*signal_path_fracs - true_paths_fracs) / true_paths_fracs
    delta_frac = synthetic_estimate_alpha*signal_path_fracs - true_paths_fracs
    print('# =============================================================================')
    print('estimated alpha--',res.x, initial_alphas, (res.x-np.array([initial_alphas[0], initial_alphas[2]]))/np.array([initial_alphas[0], initial_alphas[2]]))
    print('Test results: err--', err)
    print('# =============================================================================')
    
    return synthetic_estimate_alpha, err, delta_frac

    
