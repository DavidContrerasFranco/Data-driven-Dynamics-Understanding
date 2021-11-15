
import time
import copy
import operator
import functools
import numpy as np

from sysidentpy.utils.display_results import results
from sysidentpy.model_structure_selection import FROLS
from sysidentpy.basis_function._basis_function import Polynomial

def narmax_state_space(nx_model:FROLS, X_train, X_test, states_names):
    xlag = nx_model.xlag if type(nx_model.xlag) == int else max(functools.reduce(operator.iconcat, nx_model.xlag, []))
    max_lag = max(xlag, nx_model.ylag)
    f_size = len(states_names)
    narmax_time = 0
    coeffs = []
    sim = []

    for s_id, state in enumerate(states_names):
        model = copy.deepcopy(nx_model)

        x_train = np.delete(X_train, s_id, axis=1)[:-1]
        y_train = X_train[1:, s_id].reshape(-1, 1)

        x_test = np.delete(X_test, s_id, axis=1)
        y_test = X_test[0:nx_model.ylag, s_id].reshape(-1, 1)

        # Train model for one state and get time
        tic = time.time()
        model.fit(X=x_train, y=y_train)
        toc = time.time()
        narmax_time += toc - tic

        # Print resulting model
        param = results(model.final_model, model.theta, model.err, model.n_terms, dtype='sci')
        param_names = np.delete(states_names, s_id, axis=0).tolist()
        display_nx_model(param, model.theta, state, param_names, max_lag)

        # Simulate model for the state Z
        coeffs += [np.pad(model.theta.flatten(), (0, model.basis_function.__sizeof__() - len(model.theta)))]
        sim += [model.predict(X=x_test, y=y_test)]

    # Stack results for models and predictions
    narmax_model = np.vstack(coeffs)
    narmax_sim = np.hstack(sim)

    return narmax_model, narmax_sim, narmax_time





def display_nx_model(results, theta, output:str, input_vars, max_lag=1):
    regressors = ''
    for idx, regressor in enumerate(results):
        if idx > 0:
            regressors += ' +'
        for lag in range(0, max_lag):
            regressor[0] = regressor[0].replace('(k-' + str(lag + 1) + ')', '[k-' + str(lag) + ']')
        regressors += ' ' + f'{theta[idx][0]:.3E}' + ' ' + regressor[0].replace('-0', '')

    regressors = regressors.replace('y', output).replace('+ -', '- ')
    for idx, var in enumerate(input_vars):
        regressors = regressors.replace('x' + str(idx+1), var)

    print(output + '[k+1] =' + regressors)