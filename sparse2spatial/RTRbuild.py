



def get_features_used_by_model_list(models_list=None, RFR_dict=None):
    """ Get the (set of) features used by a list of models """
    # Get dictionary of shared data if not provided
    if isinstance(RFR_dict, type(None)):
        RFR_dict = build_or_get_current_models()
    # get models to use (assume top models, if not provided)
    if isinstance(models_list, type(None)):
        models_list = get_top_models(RFR_dict=RFR_dict, NO_DERIVED=True)
    # now plot up in input variables
    testing_features_dict = RFR_dict['testing_features_dict']
    vars2use = []
    for model_name in models_list:
        vars2use += [testing_features_dict[model_name].split('+')]
    # remove double ups
    vars2use = [j for i in vars2use for j in i]
    return list(set(vars2use))


def get_top_models(n=10, stats=None, RFR_dict=None, NO_DERIVED=True,
                   exclude_ensemble=True, verbose=True):
    """
    retrieve the names of the top 10 models
    """
    # get stats on models in RFR_dict
    if isinstance(RFR_dict, type(None)):
        RFR_dict = build_or_get_current_models()
    if isinstance(stats, type(None)):
        stats = get_stats_on_current_models(RFR_dict=RFR_dict, verbose=False)
    # Don't count the Ensemble in the topten
    if exclude_ensemble:
        var_ = 'RFR(Ensemble)'
        try:
            stats = stats.T[[i for i in stats.T.columns if var_ not in i]].T
            if verbose:
                print('removed {} from list'.format(var_))
        except:
            if verbose:
                print('failed to remove {} from list'.format(var_))
    # return the top model's names (with ot without derivative values)
    if NO_DERIVED:
        params2inc = stats.T.columns
        params2inc = [i for i in params2inc if 'DOC' not in i]
        params2inc = [i for i in params2inc if 'Prod' not in i]
        return list(stats.T[params2inc].T.head(n).index)
    else:
        return list(stats.head(n).index)


def get_choosen_model_from_features_selection(rtn_features=True):
    """ Load choosen model and retrieve its testing features"""
    from sklearn.externals import joblib
    import glob
    # load best estimator model
    iodide_data_dir = get_Oi_file_locations('iodide_data')
    wrk_dir = iodide_data_dir + '/models/LIVE/CHOOSEN_MODEL/'
    prefix = 'my_model_'
    model_savename = glob.glob(wrk_dir+prefix+"*.pkl")
    N = len(model_savename)
    assert N == 1, 'There should be only one choosen model! Not {}'.format(N)
    model_savename = model_savename[0]
    name = model_savename.split(prefix)[1][:-4]
    model = joblib.load(model_savename)
    # Return model and variables as dict
    mdict = {'model': model, 'name': name}
    if rtn_features:
        mdict['testing_features'] = get_model_testing_features_dict(name)
    return mdict

def Hyperparameter_Tune4choosen_models(RFR_dict=None,
                                       testset='Test set (strat. 20%)',
                                       target_name=['Iodide']):
    """ Driver to tune mutiple RFR models """
    from sklearn.externals import joblib
    # testset='Test set (strat. 20%)'; target_name=['Iodide']
    # Get the data for the models
    if isinstance(RFR_dict, type(None)):
        RFR_dict = build_or_get_current_models()
    #

    # Set models to optimise
    models2compare = get_top_models(RFR_dict=RFR_dict, NO_DERIVED=True)
    # save model to dictionary of best estimators (BE)
#    BE_dict = {}
    #
#    models2compare =  models2compare[6:]
#    models2compare =  models2compare[:6]

    # get variables needed from core dictionary
    testing_features_dict = RFR_dict['testing_features_dict']
    models_dict = RFR_dict['models_dict']

    # use five fold cross validation.
    cv = 7

    # Loop and save optimised model
    # NOTE: this could be speed up by using more cores
    for model_name in models2compare:
        print('Optimising model: {}'.format(model_name))
        # Get model
        model = models_dict[model_name]
        # get testing features
        testing_features = testing_features_dict[model_name].split('+')
        # Tune parameters
        BE = Hyperparameter_Tune_model(model=model, use_choosen_model=False,
                                       save_best_estimator=True, model_name=model_name,
                                       RFR_dict=RFR_dict,
                                       testing_features=testing_features, cv=cv)
        # Save
#        iodide_data_dir = get_Oi_file_locations('iodide_data')
#        wrk_dir = iodide_data_dir+'/models/'+'/LIVE//BEST_ESTIMATORS/'
#
#        joblib.dump(BEST_ESTIMATOR, wrk_dir + model_savename)

    # --- Test the tuned models against the test set
    test_the_tuned_models = False
    if test_the_tuned_models:
        # Get the core data
        df = RFR_dict['df']

        # get the data
        test_set = df.loc[df[testset] == True, :]
        train_set = df.loc[df[testset] == False, :]
        # also sub select all vectors for input data

        #
        iodide_data_dir = get_Oi_file_locations('iodide_data')
        wrk_dir = iodide_data_dir+'/models/'+'/LIVE/OPTIMISED_MODELS/'

        # Test the improvements in the optimised models?
        for model_name in models2compare:
            # - Get existing model
            model = models_dict[model_name]
            # get testing features
            testing_features = testing_features_dict[model_name].split('+')

            # -  Get the data
            # ( Making sure to remove the target!!! )
    #        train_features = df[testing_features].loc[ train_set.index  ]
    #        train_labels = df[target_name].loc[ train_set.index  ]
            test_features = df[testing_features].loc[test_set.index]
            test_labels = df[target_name].loc[test_set.index]

            # - test the existing model
            print(' ---------------- '*3)
            print(' ---------------- {}: '.format(model_name))
            print(' - Base values: ')
            quick_model_evaluation(model, test_features, test_labels)

            # - Get optimised model
            try:
                model_savename = "my_model_{}.pkl".format(model_name)
                OPmodel = joblib.load(wrk_dir + model_savename)
                #
                print(' - Optimised values: ')
                quick_model_evaluation(OPmodel, test_features, test_labels)
            except:
                pass

    # --- Test the tuned models against the training set
        # Get the core data
        df = RFR_dict['df']
        # get the data
        test_set = df.loc[df[testset] == True, :]
        train_set = df.loc[df[testset] == False, :]
        # also sub select all vectors for input data
        # locations of the optimised models
        iodide_data_dir = get_Oi_file_locations('iodide_data')
        wrk_dir = iodide_data_dir+'/models/'+'/LIVE/OPTIMISED_MODELS/'

        # Test the improvements in the optimised models?
        for model_name in models2compare:
            # - Get existing model
            model = models_dict[model_name]
            # get testing features
            testing_features = testing_features_dict[model_name].split('+')

            # -  Get the data
            # ( Making sure to remove the target!!! )
            train_features = df[testing_features].loc[train_set.index]
            train_labels = df[target_name].loc[train_set.index]
#            test_features = df[testing_features].loc[ test_set.index ]
#            test_labels = df[target_name].loc[ test_set.index ]

            # - test the existing model
            print(' ---------------- '*3)
            print(' ---------------- {}: '.format(model_name))
            print(' - Base values: ')
            quick_model_evaluation(model, train_features, train_labels)

            # - Get optimised model
            try:
                model_savename = "my_model_{}.pkl".format(model_name)
                OPmodel = joblib.load(wrk_dir + model_savename)
                #
                print(' - Optimised values: ')
                quick_model_evaluation(OPmodel, train_features, train_labels)
            except:
                pass


def Hyperparameter_Tune_model(use_choosen_model=True, model=None,
                              RFR_dict=None, df=None, cv=3,
                              testset='Test set (strat. 20%)', target_name=['Iodide'],
                              testing_features=None, model_name=None,
                              save_best_estimator=True):
    """ Tune hyperparmeters of model """
    from sklearn.externals import joblib
    from sklearn.ensemble import RandomForestRegressor
    # use_choosen_model=True; testset='Test set (strat. 20%)'; target_name=['Iodide']
    # Get data to test
    if isinstance(df, type(None)):
        #        df = get_dataset_processed4ML()
        df = RFR_dict['df']

    # Use the model selected from the feature testing
    if use_choosen_model:
        assert_str = "model name not needed as use_choosen_model selected!"
        assert isinstance(model, type(None)), assert_str
        # select a single chosen model
        mdict = get_choosen_model_from_features_selection()
        testing_features = mdict['testing_features']
        model = mdict['model']
        model_name = mdict['name']

    # - extract training dataset
    test_set = df.loc[df[testset] == True, :]
    train_set = df.loc[df[testset] == False, :]
    # also sub select all vectors for input data
    # ( Making sure to remove the target!!! )
    train_features = df[testing_features].loc[train_set.index]
    train_labels = df[target_name].loc[train_set.index]
    test_features = df[testing_features].loc[test_set.index]
    test_labels = df[target_name].loc[test_set.index]

    # - Make the base model for comparisons
    base_model = RandomForestRegressor(n_estimators=10, random_state=42,
                                       criterion='mse')
    base_model.fit(train_features, train_labels)
    quick_model_evaluation(base_model, test_features, test_labels)

    # - First make an intial explore of the parameter space
    rf_random = Use_RandomizedSearchCV_to_explore_hyperparams(cv=cv,
                                                            train_features=train_features,
                                                              train_labels=train_labels,
                                                        testing_features=testing_features)
#        test_features=test_features, test_labels=test_labels
    # Check the performance by Random searching (RandomizedSearchCV)
    best_random = rf_random.best_estimator_
    best_params_ = rf_random.best_params_
    print(rf_random.best_params_)
    quick_model_evaluation(best_random, test_features, test_labels)

    # - Now do a more focused optimisation
    # get the parameters based on the RandomizedSearchCV output
    param_grid = define_hyperparameter_options2test(
        testing_features=testing_features, best_params_=best_params_,
        param_grid_based_on_RandomizedSearchCV=True)
    # Use GridSearchCV
    grid_search = use_GridSearchCV_to_tune_Hyperparameters(cv=cv,
                                                           train_features=train_features,
                                                           param_grid=param_grid,
                                                           train_labels=train_labels,
                                                        testing_features=testing_features,
                                                           #        test_features=test_features, test_labels=test_labels
                                                           )
    print(grid_search.best_params_)
    # Check the performance of grid seraching searching
    BEST_ESTIMATOR = grid_search.best_estimator_
    quick_model_evaluation(BEST_ESTIMATOR, test_features, test_labels)

    # Save the best estimator now for future use
    if save_best_estimator:
        iodide_data_dir = get_Oi_file_locations('iodide_data')
        wrk_dir = iodide_data_dir+'/models/'+'/LIVE/OPTIMISED_MODELS/'
        model_savename = "my_model_{}.pkl".format(model_name)
        joblib.dump(BEST_ESTIMATOR, wrk_dir + model_savename)
    else:
        return BEST_ESTIMATOR


def Use_RandomizedSearchCV_to_explore_hyperparams(train_features=None,
                                                  train_labels=None,
                                                  testing_features=None,
                                                  test_features=None,
                                                  test_labels=None,
                                                  scoring='neg_mean_squared_error',
                                                  cv=3):
    """ Intial test of parameter space using RandomizedSearchCV """
    from sklearn.model_selection import RandomizedSearchCV
    from sklearn.ensemble import RandomForestRegressor
    # Number of trees in random forest
    n_estimators = [int(x) for x in np.linspace(start=10, stop=1000, num=10)]
    # Number of features to consider at every split
#    max_features = ['auto', 'sqrt']
    max_features = range(1, 30)
    if not isinstance(testing_features, type(None)):
        max_features = [i for i in max_features if
                        i <= len(testing_features)]
    # Maximum number of levels in tree
    max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
    max_depth.append(None)
    # Minimum number of samples required to split a node
    min_samples_split = [2, 5, 10]
    # Minimum number of samples required at each leaf node
    min_samples_leaf = [1, 2, 4]
    # Method of selecting samples for training each tree
#    bootstrap = [True, False]
    bootstrap = [True]  # Force use of bootstrapping
    # Create the random grid
    random_grid = {'n_estimators': n_estimators,
                   'max_features': max_features,
                   'max_depth': max_depth,
                   'min_samples_split': min_samples_split,
                   'min_samples_leaf': min_samples_leaf,
                   'bootstrap': bootstrap}
    # Use the random grid to search for best hyperparameters
    # First create the base model to tune
    rf = RandomForestRegressor(random_state=42, criterion='mse')
    # Random search of parameters, using 3 fold cross validation,
    # search across 100 different combinations, and use all available cores
    rf_random = RandomizedSearchCV(estimator=rf,
                                   param_distributions=random_grid, n_iter=100, cv=cv,
                                   verbose=2,
                                   random_state=42, n_jobs=-1, scoring=scoring)
    # Fit the random search model
    rf_random.fit(train_features, train_labels)
    return rf_random


def use_GridSearchCV_to_tune_Hyperparameters(param_grid=None,
                                             train_features=None, train_labels=None,
                                             testing_features=None, \
                                             #        test_features=None, test_labels=None
                                             scoring='neg_mean_squared_error', cv=3,
                                             ):
    """ Refine hyperparameters using (GridSearchCV)  """
    from sklearn.model_selection import GridSearchCV
    from sklearn.ensemble import RandomForestRegressor
    # Create a based model
    rf = RandomForestRegressor(random_state=42, criterion='mse')
    # Instantiate the grid search model
    grid_search = GridSearchCV(estimator=rf, param_grid=param_grid,
                               cv=cv, n_jobs=-1, verbose=2, scoring=scoring)
    # Fit the grid search to the data
    grid_search.fit(train_features, train_labels)
    return grid_search


def quick_model_evaluation(model, test_features, test_labels):
    from sklearn.metrics import mean_squared_error
    predictions = model.predict(test_features)
#    mse = np.mean( (predictions - test_labels.values) **2 )
    MSE = mean_squared_error(test_labels, predictions)
    RMSE = np.sqrt(MSE)
    ME = np.mean(abs(predictions - test_labels.values))
    print('Model Performance')
    print('Mean squared error (MAE): {:0.4f} nM'.format(MSE))
    print('Mean absolute error (MAE): {:0.4f} nM'.format(ME))
    print('RMSE = {:0.2f}'.format(RMSE))
    return RMSE


def define_hyperparameter_options2test(testing_features=None,
                                       param_grid_based_on_RandomizedSearchCV=True,
                                       best_params_=None,
                                       param_grid_based_on_intial_guesses=True,
                                       ):
    """ Define a selction of test groups """
    # - Shared variables in grid
    vals2test = {
        'n_estimators': [10, 50, 75, 100, 125, 200, 300, 500],
        'max_features': [1, 2, 3, 4, 5],
        'max_depth': [3, 10, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 3, 10],
        'oob_score':  [True],
        'bootstrap': [True],
    }
    if param_grid_based_on_RandomizedSearchCV:
        if not isinstance(best_params_, type(None)):
            vals2test_ASSUMED = vals2test.copy()
            vals2test = {}
            for key in best_params_:
                value = best_params_[key]
                # 'n_estimators' / trees
                if (key == 'n_estimators'):
                    values = [value+(i*10) for i in range(0, 4)]
                    values += [value+(i*10) for i in range(-4, 0)]
                    # only allow values greater than zero
                    values = [i for i in values if i > 0]
                    # add sorted values
                    vals2test[key] = sorted(values)
                # max depth
                elif (key == 'max_depth'):
                    # value is either a number of "None".
                    if is_number(value):
                        values = [value+(i*5) for i in range(0, 2)]
                        values += [value+(i*5) for i in range(-2, 0)]
                        # only allow values greater than zero
                        values = [i for i in values if i > 0]
                        # add sorted values
                        vals2test[key] = sorted(values)
                    else:  # If None, just use None.
                        vals2test[key] = [value]
                # 'min_samples_split'
                elif (key == 'min_samples_leaf'):
                    if value == 1:
                        values = range(value, value+3)
                    else:
                        values = [value, value+1, value+2]
                    # add sorted values
                    vals2test[key] = list(sorted(values))
                # 'min_samples_split'
                elif (key == 'min_samples_split'):
                    values = [value, value+1, value+2]
                    # add sorted values
                    vals2test[key] = list(sorted(values))
                # Add bootstrap and 'max_features' as recived
                elif (key == 'bootstrap') or (key == 'max_features'):
                    vals2test[key] = [value]
                # Check the key has settings intialised for
                else:
                    print('No settings setup for {}'.format(key))
                    sys.exit()

            # check all the values in best_params_ are in dict
            new_keys = best_params_.keys()
            old_keys = vals2test_ASSUMED.keys()
            extra_keys = [i for i in old_keys if i not in new_keys]
            print('WARNING: adding standard keys for: ', extra_keys)
            for key in extra_keys:
                vals2test[key] = vals2test_ASSUMED[key]
            # check all values in
            all_in_dict = any([i not in vals2test.keys() for i in new_keys])
            assert (not all_in_dict), 'Missing keys from provided best_params_'

        else:
            vals2test = {
                'n_estimators': [80+(i*10) for i in range(8)],
                'max_features': [1, 2, 3, 4, 5],
                'max_depth': [90+(i*5) for i in range(5)],
                'min_samples_split': [4, 5, 6],
                'min_samples_leaf': [1, 2, 3],
                'oob_score':  [True],
                'bootstrap': [True],
            }
    # Check the number of variations being tested

    def prod(iterable):
        import operator
        return reduce(operator.mul, iterable, 1)
    len_of_values = [len(vals2test[i]) for i in vals2test.keys()]
    print('WARNING: # of variations undertest = {}'.format(prod(len_of_values)))
    # Make sure the max features isn't set to more testing_features that known
    if not isinstance(testing_features, type(None)):
        max_features = vals2test['max_features']
        max_features = [i for i in max_features if
                        i <= len(testing_features)]
        vals2test['max_features'] = max_features
    # --- Setup a parameter grid for testings
    param_grid = [
        # - # of trees (“n_estimators”, test=10, 25, 50, 100, 250, 500)
        #     {
        #     'bootstrap': [True],
        #     'n_estimators': vals2test['n_estimators'],
        #     'oob_score': [True],
        #     },
        #     # - # of features/”variables” (“max_features”, test= 2,3,4, None)
        #     {
        #     'bootstrap': [True],
        #     'max_features': vals2test['max_features2test'],
        #     'oob_score': [True],
        #     },
        #     # - both of the above
        #     {
        #     'bootstrap': [True],
        #     'n_estimators': vals2test['n_estimators'],
        #     'max_features': vals2test['max_features'],
        #     'oob_score': [True],
        #     },
        #     # - Minimum samples per leaf
        #     {
        #     'bootstrap': [True],
        #     "min_samples_leaf": vals2test['min_samples_leaf'],
        #     'oob_score': [True],
        #     },
        #     # - Depth
        #     {
        #     'bootstrap': [True],
        #     "max_depth": max_depth2test,
        #     'oob_score': [True],
        #     },
        #     # - Split?
        #     {
        #     'bootstrap': [True],
        #     "min_samples_split": vals2test['min_samples_split'],
        #     'oob_score': [True],
        #     },
        # - all of the above
        {
            'bootstrap': vals2test['bootstrap'],
            'n_estimators': vals2test['n_estimators'],
            'max_features': vals2test['max_features'],
            "min_samples_split": vals2test['min_samples_split'],
            "min_samples_leaf": vals2test['min_samples_leaf'],
            "max_depth": vals2test['max_depth'],
            'oob_score': vals2test['oob_score'],
        },
    ]
    if param_grid_based_on_intial_guesses:
        return param_grid
    elif return_random_informed_grid:
        return param_grid_based_on_RandomizedSearchCV




def mk_predictions_NetCDF_4_many_builds(model2use, res='4x5',
                                        models_dict=None, testing_features_dict=None,
                                        RFR_dict=None,
                                        stats=None, plot2check=False,
                                        rm_Skagerrak_data=False,
                                        debug=False):
    """ Make a NetCDF file of predicted vairables for a given resolution """
    from sklearn.externals import joblib
    import gc
    import glob
    # --- local variables
    # extract the models...
    if isinstance(RFR_dict, type(None)):
        RFR_dict = build_or_get_current_models(
            rm_Skagerrak_data=rm_Skagerrak_data
        )
    # get the variables required here
    if isinstance(testing_features_dict, type(None)):
        testing_features_dict = RFR_dict['testing_features_dict']
    # set the extr_str if rm_Skagerrak_data set to True
    if rm_Skagerrak_data:
        extr_str = '_No_Skagerrak'
    else:
        extr_str = ''
    # Get location to save file and set filename
    iodide_dir = get_Oi_file_locations('iodide_data')
    filename = 'Oi_prj_feature_variables_{}.nc'.format(res)
    dsA = xr.open_dataset(iodide_dir + filename)
    #  location of data
    wrk_dir = get_Oi_file_locations('iodide_data')+'/models/'+'/LIVE/'
    # --- Make a da for each model
    ds_l = []
    # Get list of twenty models built
    loc2use = '{}/{}{}/'.format(wrk_dir, '/ENSEMBLE_REPEAT_BUILD', extr_str)
    models_str = loc2use + '*{}*.pkl'.format(model2use)
    builds4model = glob.glob(models_str)
    print(builds4model, models_str)
    # Print a string to debug the output
    db_str = "Found {} saved models for '{} - glob str:{}'"
#    if debug:
    print(db_str.format(len(builds4model), model2use, models_str))
    # Get the numbers for the models in directory
    b_modelnames = [i.split('my_model_')[-1][:-3] for i in builds4model]
    # Check the number of models selected
    ast_str = "There aren't models for {} in {}"
    assert len(b_modelnames) > 1, ast_str.format(model2use, loc2use)
    # Now loop by model built for ensemble member and predict values
    for n_modelname, b_modelname in enumerate(b_modelnames):
        # Load the model
        model = joblib.load(builds4model[n_modelname])
        # Get testinng features
        testing_features = testing_features_dict[model2use].split('+')
        # Make a DataSet of predicted values
        ds_l += [mk_da_of_predicted_values(model=model, res=res, dsA=dsA,
                                           modelname=b_modelname,
                                           testing_features=testing_features)]
        # Force local tidy of garbage
        gc.collect()
    # Combine datasets
    ds = xr.merge(ds_l)
    # -- Also get values for parameterisations
    # Chance et al (2013)
    param = u'Chance2014_STTxx2_I'
    arr = calc_iodide_chance2014_STTxx2_I(dsA['WOA_TEMP'].values)
    ds[param] = ds[b_modelname]  # use existing array as dummy to fill
    ds[param].values = arr
    # MacDonald et al (2013)
    param = 'MacDonald2014_iodide'
    arr = calc_iodide_MacDonald2014(dsA['WOA_TEMP'].values)
    ds[param] = ds[b_modelname]  # use existing array as dummy to fill
    ds[param].values = arr
    # ---- Do a test diagnostic plot
    if plot2check:
        for var_ in ds.data_vars:
            # Do a quick plot to check
            arr = ds[var_].mean(dim='time')
            AC.map_plot(arr, res=res)
            plt.title(var_)
            plt.show()
    # --- Save to NetCDF
    save_name = 'Oi_prj_predicted_iodide_{}_ENSEMBLE_BUILDS_{}_{}.nc'
    ds.to_netcdf(save_name.format(res, model2use, extr_str))


def get_model_predictions4obs_point(df=None, model_name='TEMP+DEPTH+SAL',
                                    model=None, testing_features=None):
    """ Get model predictions for all observaed points """
    # Model name?
    if isinstance(model, type(None)):
        extr_str = {
            #    'TEMPC+DEPTH+SAL':'tree_X_JUST_TEMP_GEBCO_SALINTY',
            #    'TEMPC+DEPTH+SAL':'tree_X_JUST_TEMP_GEBCO_SALINTY_REPEAT',
            #    'TEMP+DEPTH+SAL (rs)':'tree_X_JUST_TEMP_K_GEBCO_SALINTY',
            #    'TEMP+DEPTH+SAL':'tree_X_STRAT_JUST_TEMP_K_GEBCO_SALINTY',
            'TEMP+DEPTH+SAL': 'FINAL_DATA_tree_X_STRAT_JUST_TEMP_K_GEBCO_SALINTY',
            'TEMP+DEPTH+SAL(N=100)':
            'FINAL_DATA_tree_X_JUST_TEMP_K_GEBCO_SALINTY_100',
        }[model_name]
        # Get the model
        model = get_current_model(extr_str=extr_str)
    # Testing features to use
    if isinstance(testing_features, type(None)):
        #         testing_features_dict = {
        #         'TEMP+DEPTH+SAL' : ['WOA_TEMP_K', 'WOA_Salinity', 'Depth_GEBCO'],
        #         }
        testing_features = get_model_testing_features_dict(model_name)
        target_name = ['Iodide']
    #
    target_predictions = model.predict(df[testing_features])
    return target_predictions


def mk_iodide_ML_testing_and_training_set(df=None, target_name=['Iodide'],
                                          random_strat_split=True, testing_features=None,
                                          random_state=42,
                                          test_plots_of_iodide_dist=False,
                                          random_20_80_split=False,
                                          nsplits=4, verbose=True, debug=False):
    """ Make a test and training dataset for ML algorthims """

    # https://github.com/ageron/handson-ml/blob/master/02_end_to_end_machine_learning_project.ipynb

    #
#     if test_plots_of_iodide_dist:
#         # Save off variables
#         show_plot=False
#         savetitle = 'Oi_prj_iodide_stratified_binning'
#         dpi = 320
#         pdff = AC.plot2pdfmulti( title=savetitle, open=True, dpi=dpi )
#         # Now plot
#         import seaborn as sns
#         Iodide = df[u'Iodide']
#         # ceil of the median divided by
#         ceil_div_med_limited = np.ceil( Iodide / Iodide.median() )
#         ceil_div_med_limited[ceil_div_med_limited> 5] = 5
#         #
#         ceil_ln_limited = np.ceil(  np.log( Iodide) )
#         ceil_ln_limited[ ceil_ln_limited <=2 ] = 2
#         #
#         vars_ = {
#         u'Iodide' : Iodide,
#         u'ln(Iodide)': np.log( Iodide),
#         u'np.ceil( ln(Iodide) )': np.ceil(  np.log( Iodide) ),
#         u'np.ceil( ln(Iodide) ), limited to 2': ceil_ln_limited,
#         u'Iodide / median ': Iodide / Iodide.median(),
#         u'ceil( Iodide / median )': np.ceil( Iodide / Iodide.median() ),
#         u'Iodide / mean': Iodide / Iodide.mean(),
#         u'ceil( Iodide / mean )': np.ceil( Iodide / Iodide.mean() ),
#         u'ceil( Iodide / median ), limited to 5': ceil_div_med_limited,
#         }
#         for key_ in vars_:
#             print('plotting :', key_)
#             sns.distplot(  vars_[key_] )
#             plt.title( 'PDF of {}'.format(key_) )
#             plt.xlabel( key_ )
#
#
#             # if there are less than 8 bins give the populations of bins
#             counts = vars_[key_].value_counts()
#             if len( counts ) < 8:
#                 bins = counts.index
#                 count = counts.values
#                 bins = dict(zip(bins,count))
#                 print( bins )
#                 ax = plt.gca()
#                 bins = ['{} (N={})'.format(i, bins[i]) for i in bins.keys()]
#                 bins = ', '.join(bins[:4])+ '\n'+', '.join(bins[4:])
#                 subtitle='Bins: \n' + bins
#                 print(  subtitle )
#                 plt_txt_x, plt_txt_y = 0.5, 0.85
#                 plt.text(  plt_txt_x, plt_txt_y, \
#                     subtitle, ha='center', va='center', \
#                     transform=ax.transAxes)#, fontsize=f_size*.65)
#
# #            savename = 'Oi_prj_iodide_obs_var_{}'.format( key_ )
# #            plt.savefig( rm_spaces_and_chars_from_str( savename ) )
#             AC.plot2pdfmulti( pdff, savetitle, dpi=dpi )
#             if show_plot: plt.show()
#             plt.close()
#         #  save entire pdf
#         AC.plot2pdfmulti( pdff, savetitle, close=True, dpi=dpi )

    # --- ------ make Test and
    # to make this approach's output identical at every run
    np.random.seed(42)

    # --- Standard random selection:
    if random_20_80_split:
        from sklearn.model_selection import train_test_split
        # Use a standard 20% test set.
        train_set, test_set = train_test_split(df, test_size=0.2,
                                               random_state=random_state)
        # also sub select all vectors for input data
        # ( Making sure to remove the target!!! )
        train_set = df[testing_features].loc[train_set.index]
        test_set = df[testing_features].loc[test_set.index]
        test_set_targets = df[target_name].loc[test_set.index]

    # ---
    if random_strat_split:
        from sklearn.model_selection import StratifiedShuffleSplit
        # Add in "SPLIT_GROUP" metric
        SPLITvar = 'SPLIT_GROUP'
        use_ceil_of_log = False  # This approach was only used
        if use_ceil_of_log:
            # Original approach taken for AGU work etc
            ceil_ln_limited = np.ceil(np.log(df[u'Iodide']))
            # push bottom end values into lower bin
            ceil_ln_limited[ceil_ln_limited <= 2] = 2
            # push top end values in higher bin
            ceil_ln_limited[ceil_ln_limited >= 5] = 5
            df[SPLITvar] = ceil_ln_limited
        else:
            # Use decals and put the bins with high values to together
            # NOTE: use quartile cut! (pd.qcut, not pd.cut)
            #            df[SPLITvar] = pd.cut(df['Iodide'].values,10).codes.astype(int)
            # Combine the lesser populated higher 5 bins into the 5th bin
            #            df.loc[ df[SPLITvar] >= 4, SPLITvar ] = 4
            # qcut will split the data into N ("nsplits") bins (e.g. quintiles)
            #            pd.qcut(df['Iodide'].values,5).value_counts()
            df[SPLITvar] = pd.qcut(df['Iodide'].values, nsplits).codes
            if verbose:
                print(df[SPLITvar].value_counts())
        # setup the split
        split = StratifiedShuffleSplit(n_splits=1, test_size=0.2,
                                       random_state=random_state)
        # Now split
        for train_index, test_index in split.split(df, df[SPLITvar]):
            train_set = df.loc[train_index]
            test_set = df.loc[test_index]
            test_set_targets = df[target_name].loc[test_index]
        # Gotcha for changes in array index
        Na = df[~df.index.isin(train_index.tolist() + test_index.tolist())]
#        assert (Na.shape[0] < 0), 'WARING: thre now NaNs in the arrays! - {}'
        if (Na.shape[0] < 0):
            print('WARNING'*20)
            print(Na)
        # Print out the split of the bins...
        if verbose:
            dfs = {
                'ALL data': df, 'test data': test_set, 'train data': train_set
            }
            for key_ in dfs.keys():
                print('data split in: {}'.format(key_))
                print(dfs[key_][SPLITvar].value_counts() / dfs[key_].shape[0])
        # Now remove the SPLIT group
        for set_ in train_set, test_set:
            #            if (SPLITvar in set_.columns):
            set_.drop(SPLITvar, axis=1, inplace=True)
        # re-name (TODO mak naming consistent!)
#        train_set_full = train_set
#        test_set_full = test_set
#        test_set_targets =test_set_targets

#        print('NOT setup!'*100)
#        sys.exit()
#    else:
#        print('select a method for making the test dataset')
#        sys.exit()
    return train_set, test_set, test_set_targets


def get_current_model(dir=None,
                      extr_str='FINAL_DATA_tree_X_STRAT_JUST_TEMP_K_GEBCO_SALINTY'):
    """ Load the saved model being used by this work """
    from sklearn.externals import joblib
    # Get the location of the saved model and load it
    if isinstance(dir, type(None)):
        dir = get_Oi_file_locations('iodide_data')+'/models/'
    model_savename = "my_model_{}.pkl".format(extr_str)
    return joblib.load(dir+model_savename)




def get_predict_lat_lon_array(res='4x5', testing_features=None, month=9):
    """ Load extracted predictor array """
    # get file of predictor values for res and month
    filename = 'Oi_prj_predictor_values_{}_month_num_{}'.format(res, month)
    if res == '4x5':
        filename += '_TEST'
    filename += '.csv'
    dir = get_Oi_file_locations('iodide_data')
    dir += 'Oi_prj_predictor_files_by_month_{}/'.format(res)
    df = pd.read_csv(dir+filename)
    # make sure the variables have the same names
    rename_dict = {'lat': 'Latitude', 'lon': 'Longitude'}
    df.rename(columns=rename_dict, inplace=True)
    # Make sure the input variables are numeric
    num_params = ['WOA_Nitrate', 'WOA_Salinity', 'WOA_TEMP', 'SeaWIFs_ChlrA']
    for param in num_params:
        df[param] = pd.to_numeric(df[param].values, errors='coerce')

    # add modulus if not in array
    mod_var = 'Latitude (MOD)'
    if not (mod_var in df.columns):
        df[mod_var] = (df[u'Latitude']**2)**0.5
    # add TEMP_K if not in array
    TEMP_var = 'WOA_TEMP'
    if not (TEMP_var+'_K' in df.columns):
        df[TEMP_var+'_K'] = df[TEMP_var].values + 273.15

    # force values to be numerics
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # drop NaNs (e.g. bits over land...
    df_dropped = df.dropna()
    if (df.shape != df_dropped.shape):
        ptr_str = 'WARNING droppped values {} => {}'
        print(ptr_str.format(df.shape, df_dropped.shape))
        df = df_dropped
    # Return DataFrane
    return df
