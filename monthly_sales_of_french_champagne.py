# -*- coding: utf-8 -*-
"""Monthly Sales of French Champagne.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/10bE6u1nb8mgNjXpiMqqkB4mqMoUp96CJ

# **Project: Monthly Sales of French Champagne**

**Statement**:

  In this problem we will try to prdict the number of monthly sales of champagne for the well-known French champagne company ***Perrin Frères***.
  The dataset is credited to **Makridakis** & **Wheelwrigt**, 1989. It describes the number of month sales of champagne from January 1964-September 1972.

The steps of this project that we will through are as follows.

* The steps:
      1. Problem Description.
      2. Test Harness.
      3. Persistence.
      4. Data Analysis.
      5. ARIMA Models.
      6. Model Validation.
"""

!pip install -U mxnet-cu101==1.7.0

!nvidia-smi

from mxnet import np, npx
from mxnet.gluon import nn

npx.set_np()

npx.cpu(), npx.gpu(), npx.gpu(1)

npx.num_gpus() #Query the number of available gpu

"""# Test Harness"""

from pandas import read_csv

series  = read_csv('https://raw.githubusercontent.com/jbrownlee/Datasets/master/monthly_champagne_sales.csv', header=0, index_col=0, parse_dates=True, squeeze=True)
split_point = len(series) - 12
dataset, validation = series[0:split_point], series[split_point:]
print('Dataset %d, Validation %d' % (len(dataset), len(validation)))
dataset.to_csv('dataset.csv', header=False)
validation.to_csv('validation.csv', header=False)

"""**The specific contents of these files are:**

    1. dataset.csv: Observations from January 1964 to September 1971 (93 obs)
    2. validation.csv: Observations from October 1971 to September 1972 (12 obs)

## **Model Evaluation**
"""

# evaluate persistence model on time series
from pandas import read_csv
from sklearn.metrics import mean_squared_error
from math import sqrt
# load data
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
# prepare data
X = series.values
X = X.astype('float32')
train_size = int(len(X) * 0.50)
train, test = X[0:train_size], X[train_size:]
# walk-forward validation
history = [x for x in train]
predictions = list()
for i in range(len(test)):
  # predict
  yhat = history[-1]
  predictions.append(yhat)
  # observation
  obs = test[i]
  history.append(obs)
  print( ' >Predicted=%.3f, Expected=%3.f ' % (yhat, obs))
# report performance
rmse = sqrt(mean_squared_error(test, predictions))
print( ' RMSE: %.3f ' % rmse)

"""*We can see that the persistence model achieved an **RMSE of 3186.501**. This means that on average, the model was wrong by about 3,186 million sales for each prediction made.*
We now a baseline prediction method and performance.

## **Data Analysis**
"""

series.describe()

# Line Plot
from matplotlib import pyplot
series.plot()
pyplot.show()

"""The plot shows an increase trend of sales over time and appears to be systematic seasonality to the sales for each year. Therefore the seasonal signal appears to be growing over time. However we do not notice any outliers and its certainly a non-stationary series."""

# Seasonal Line Plots - Multiple line plots of time series
from pandas import read_csv
from pandas import DataFrame
from pandas import Grouper
from matplotlib import pyplot
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
groups = series['1964' : '1970'].groupby(Grouper(freq='A'))
years = DataFrame()
pyplot.figure()
i = 1
n_groups = len(groups)
for name, group in groups:
  pyplot.subplot((n_groups*100) + 10 + i)
  i += 1
  pyplot.plot(group)
pyplot.show()

# density plots of time series
from pandas import read_csv
from matplotlib import pyplot
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
pyplot.figure(1)
pyplot.subplot(211)
series.hist()
pyplot.subplot(212)
series.plot(kind='kde')
pyplot.show()

# boxplots of time series
from pandas import read_csv
from pandas import DataFrame
from pandas import Grouper
from matplotlib import pyplot
series = read_csv('dataset.csv' , header=None, index_col=0, parse_dates=True, squeeze=True)
groups = series['1964' : '1970'].groupby(Grouper(freq= 'A' ))
years = DataFrame()
for name, group in groups:
  years[name.year] = group.values
years.boxplot()
pyplot.show()

"""# ARIMA Models

1. Manually Configure the ARIMA.
2. Automatically Configure the ARIMA.
3. Review Residual Errors.32.6. ARIMA Models
"""

# create and summarize stationary version of time series - Manual Configuration
from pandas import read_csv
from pandas import Series
from statsmodels.tsa.stattools import adfuller
from matplotlib import pyplot

# create a differenced series
def difference(dataset, interval=1):
  diff = list()
  for i in range(interval, len(dataset)):
    value = dataset[i] - dataset[i - interval]
    diff.append(value)
  return Series(diff)
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
X = series.values
X = X.astype('float32')
# difference data
months_in_year = 12
stationary = difference(X, months_in_year)
stationary.index = series.index[months_in_year:]
# check if stationary
result = adfuller(stationary)
print( 'ADF Statistic: %f' % result[0])
print( 'p-value: %f' % result[1])
print( 'Critical Values:' )
for key, value in result[4].items():
  print( '\t%s: %.3f' % (key, value))
# save the deseasonalized version of the series
stationary.to_csv('stationary.csv', header=False)
# plot
stationary.plot()
pyplot.show()

"""The results show that the test statistic value -7.134898 is smaller than the critical value at 1% of -3.515. This suggests that we can reject the null hypothesis H0 with a significance level of less than 1%. Meaning a
low probability that the result is a statistical fluke. Rejecting the null hypothesis means that the process has no unit root, and in turn that the time series is stationary or does not have time-dependent structure.
"""

# ACF and PACF plots of time series
from pandas import read_csv
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf
from matplotlib import pyplot

series = read_csv('stationary.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
pyplot.figure()
pyplot.subplot(211)
plot_acf(series, lags=25, ax=pyplot.gca())
pyplot.subplot(212)

plot_pacf(series, lags=25, ax=pyplot.gca())
pyplot.show()

# evaluate manually configured ARIMA model
from pandas import read_csv
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.arima_model import ARIMA
from math import sqrt

# create a differenced series
def difference(dataset, interval=1):
  diff = list()
  for i in range(interval, len(dataset)):
    value = dataset[i] - dataset[i - interval]
    diff.append(value)
  return diff

# invert differenced value
def inverse_difference(history, yhat, interval=1):
  return yhat + history[-interval]

# load data
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
# prepare data
X = series.values
X = X.astype('float32')
train_size = int(len(X) * 0.50)
train, test = X[0:train_size], X[train_size:]
# walk-forward validation
history = [x for x in train]
predictions = list()
for i in range(len(test)):
  # difference data
  months_in_year = 12
  diff = difference(history, months_in_year)
  # predict
  model = ARIMA(diff, order=(1,1,1)) # The model can be extended to ARIMA(1,1,1)
  model_fit = model.fit(trend= 'nc', disp=0) # The trend arguments to nc
  yhat = model_fit.forecast()[0]
  yhat = inverse_difference(history, yhat, months_in_year)
  predictions.append(yhat)
  # observation
  obs = test[i]
  history.append(obs)
  print( '>Predicted=%.3f, Expected=%.3f' % (yhat, obs))
# report performance
rmse = sqrt(mean_squared_error(test, predictions))
print( 'RMSE: %.3f' % rmse)

"""Note: This result in an **RMSE of 956.960** show a better improvement than the persistence RMSE of 3186.501

## Grid Search ARIMA Hyperparameters

We will search all
combinations of the following parameters:
 * p: 0 to 6
 * d: 0 to 2
 * q: 0 to 6
"""

# grid search ARIMA parameters for time series
import warnings
from pandas import read_csv
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error
from math import sqrt
import numpy

# create a differenced series
def difference(dataset, interval=1):
  diff = list()
  for i in range(interval, len(dataset)):
    value = dataset[i] - dataset[i - interval]
    diff.append(value)
  return numpy.array(diff)

# invert differenced value
def inverse_difference(history, yhat, interval=1):
  return yhat + history[-interval]

# evaluate an ARIMA model for a given order (p,d,q) and return RMSE
def evaluate_arima_model(X, arima_order):
  # prepare training dataset
  X = X.astype('float32')
  train_size = int(len(X) * 0.50)
  train, test = X[0:train_size], X[train_size:]
  history = [x for x in train]
  # make predictions
  predictions = list()
  for t in range(len(test)):
    # difference data
    months_in_year = 12
    diff = difference(history, months_in_year)
    model = ARIMA(diff, order=arima_order)
    model_fit = model.fit(trend= 'nc', disp=0)
    yhat = model_fit.forecast()[0]
    yhat = inverse_difference(history, yhat, months_in_year)
    predictions.append(yhat)
    history.append(test[t])
  # calculate out of sample error
  rmse = sqrt(mean_squared_error(test, predictions))
  return rmse

# evaluate combinations of p, d and q values for an ARIMA model
def evaluate_models(dataset, p_values, d_values, q_values):
  dataset = dataset.astype('float32')
  best_score, best_cfg = float("inf"), None
  for p in p_values:
    for d in d_values:
      for q in q_values:
        order = (p,d,q)
        try:
          rmse = evaluate_arima_model(dataset, order)
          if rmse < best_score:
            best_score, best_cfg = rmse, order
          print('ARIMA%s RMSE=%.3f' % (order,rmse))
        except:
          continue
  print( 'Best ARIMA%s RMSE=%.3f' % (best_cfg, best_score))
# load dataset
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
# evaluate parameters
p_values = range(0, 7)
d_values = range(0, 3)
q_values = range(0, 7)
warnings.filterwarnings("ignore")
evaluate_models(series.values, p_values, d_values, q_values)

"""**We will select this ARIMA(4, 0, 1) model going forward.**

## Review Residual Errors
"""

# summarize ARIMA forecast residuals
from pandas import read_csv
from pandas import DataFrame
from statsmodels.tsa.arima_model import ARIMA
from matplotlib import pyplot

# create a differenced series
def difference(dataset, interval=1):
  diff = list()
  for i in range(interval, len(dataset)):
    value = dataset[i] - dataset[i - interval]
    diff.append(value)
  return diff

# invert differenced value
def inverse_difference(history, yhat, interval=1):
  return yhat + history[-interval]

# load data
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
# prepare data
X = series.values
X = X.astype('float32')
train_size = int(len(X) * 0.50)
train, test = X[0:train_size], X[train_size:]
# walk-forward validation
history = [x for x in train]
predictions = list()
for i in range(len(test)):
  # difference data
  months_in_year = 12
  diff = difference(history, months_in_year)
  # predict
  model = ARIMA(diff, order=(4,0,1))
  model_fit = model.fit(trend= 'nc', disp=0)
  yhat = model_fit.forecast()[0]
  yhat = inverse_difference(history, yhat, months_in_year)
  predictions.append(yhat)
  # observation
  obs = test[i]
  history.append(obs)
# errors
residuals = [test[i]-predictions[i] for i in range(len(test))]
residuals = DataFrame(residuals)
print(residuals.describe())
# plot
pyplot.figure()
pyplot.subplot(211)
residuals.hist(ax=pyplot.gca())
pyplot.subplot(212)
residuals.plot(kind= 'kde', ax=pyplot.gca())
pyplot.show()

"""The distribution of residual errors is also plotted. The graphs suggest a Gaussian-like distribution with a bumpy left tail, providing further evidence that perhaps a power transform might be worth exploring."""

# Plots of residual errors of bias corrected forecasts
from pandas import read_csv
from pandas import DataFrame
from statsmodels.tsa.arima_model import ARIMA
from matplotlib import pyplot
from sklearn.metrics import mean_squared_error
from math import sqrt

# create a differenced series
def difference(dataset, interval=1):
  diff = list()
  for i in range(interval, len(dataset)):
    value = dataset[i] - dataset[i - interval]
    diff.append(value)
  return diff

# invert differenced value
def inverse_difference(history, yhat, interval=1):
  return yhat + history[-interval]

# load data
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)

# prepare data
X = series.values
X = X.astype('float32')
train_size = int(len(X) * 0.50)
train, test = X[0:train_size], X[train_size:]

# walk-forward validation
history = [x for x in train]
predictions = list()
bias = 146.401198
for i in range(len(test)):
  # difference data
  months_in_year = 12
  diff = difference(history, months_in_year)
  # predict
  model = ARIMA(diff, order=(4,0,1))
  model_fit = model.fit(trend='nc', disp=0)
  yhat = model_fit.forecast()[0]
  yhat = bias + inverse_difference(history, yhat, months_in_year)
  predictions.append(yhat)
  # observation
  obs = test[i]
  history.append(obs)
# report performance
rmse = sqrt(mean_squared_error(test, predictions))
print('RMSE: %.3f' % rmse)
# errors
residuals = [test[i]-predictions[i] for i in range(len(test))]
residuals = DataFrame(residuals)
print(residuals.describe())
# plot
pyplot.figure()
pyplot.subplot(211)
residuals.hist(ax=pyplot.gca())
pyplot.subplot(212)
residuals.plot(kind= 'kde', ax=pyplot.gca())
pyplot.show()

"""The performance of the predictions is improved very slightly from 911.526 to 899.693, which may or may not be significant. The summary of the forecast residual errors shows that the mean was indeed moved to a value very close to zero."""

# ACF and PACF plots of residual errors of bias corrected forecasts
from pandas import read_csv
from pandas import DataFrame
from statsmodels.tsa.arima_model import ARIMA
from matplotlib import pyplot
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf

# create a differenced series
def difference(dataset, interval=1):
  diff = list()
  for i in range(interval, len(dataset)):
    value = dataset[i] - dataset[i - interval]
    diff.append(value)
  return diff

# invert differenced value
def inverse_difference(history, yhat, interval=1):
  return yhat + history[-interval]

# load data
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)

# prepare data
X = series.values
X = X.astype('float32')
train_size = int(len(X) * 0.50)
train, test = X[0:train_size], X[train_size:]
# walk-forward validation
history = [x for x in train]
predictions = list()
for i in range(len(test)):
  # difference data
  months_in_year = 12
  diff = difference(history, months_in_year)
  # predict
  model = ARIMA(diff, order=(4,0,1))
  model_fit = model.fit(trend= 'nc' , disp=0)
  yhat = model_fit.forecast()[0]
  yhat = inverse_difference(history, yhat, months_in_year)
  predictions.append(yhat)
  # observation
  obs = test[i]
  history.append(obs)
# errors
residuals = [test[i]-predictions[i] for i in range(len(test))]
residuals = DataFrame(residuals)
print(residuals.describe())
# plot
pyplot.figure()
pyplot.subplot(211)
plot_acf(residuals, ax=pyplot.gca())
pyplot.subplot(212)
plot_pacf(residuals, ax=pyplot.gca())
pyplot.show()

"""* ACF and PACF plots of residual errors on the bias corrected ARIMA model.

# Model Validation

  * Finalize Model: Train and save the final model.
  * Make Prediction: Load the finalized model and make a prediction.
  * Validate Model: Load and validate the final model.

  ## Finalize Model
"""

# save finalized model
from pandas import read_csv
from statsmodels.tsa.arima_model import ARIMA
import numpy

# monkey patch around bug in ARIMA class
def __getnewargs__(self):
  return ((self.endog),(self.k_lags, self.k_diff, self.k_ma))
ARIMA.__getnewargs__ = __getnewargs__

# create a differenced series
def difference(dataset, interval=1):
  diff = list()
  for i in range(interval, len(dataset)):
    value = dataset[i] - dataset[i - interval]
    diff.append(value)
  return diff

# load data
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)

# prepare data
X = series.values
X = X.astype('float32')
# difference data
months_in_year = 12
diff = difference(X, months_in_year)
# fit model
model = ARIMA(diff, order=(4,0,1))
model_fit = model.fit(trend= 'nc', disp=0)
# bias constant, could be calculated from in-sample mean residual
bias = 146.401198
# save model
model_fit.save( 'model.pkl' )
numpy.save('model_bias.npy' , [bias])

"""   ### Make Prediction"""

# load finalized model and make a prediction
from pandas import read_csv
from statsmodels.tsa.arima_model import ARIMAResults
import numpy

# invert differenced value
def inverse_difference(history, yhat, interval=1):
  return yhat + history[-interval]
series = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
months_in_year = 12
model_fit = ARIMAResults.load('model.pkl')
bias = numpy.load('model_bias.npy')
yhat = float(model_fit.forecast()[0])
yhat = bias + inverse_difference(series.values, yhat, months_in_year)
print('Predicted: %.3f' % yhat)

"""## Model Validation"""

# load and evaluate the finalized model on the validation dataset
from pandas import read_csv
from matplotlib import pyplot
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.arima_model import ARIMAResults
from sklearn.metrics import mean_squared_error
from math import sqrt
import numpy

# load and prepare datasets
dataset = read_csv('dataset.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
X = dataset.values.astype('float32')
history = [x for x in X]
months_in_year = 12
validation = read_csv('validation.csv', header=None, index_col=0, parse_dates=True, squeeze=True)
y = validation.values.astype('float32')

# load model
model_fit = ARIMAResults.load('model.pkl')
bias = numpy.load('model_bias.npy')

# make first prediction
predictions = list()
yhat = float(model_fit.forecast()[0])
yhat = bias + inverse_difference(history, yhat, months_in_year)
predictions.append(yhat)
history.append(y[0])
print('>Predicted=%.3f, Expected=%.3f' % (yhat, y[0]))

# rolling forecasts
for i in range(1, len(y)):
  # difference data
  months_in_year = 12
  diff = difference(history, months_in_year)
  # predict
  model = ARIMA(diff, order=(4,0,1))
  model_fit = model.fit(trend= 'nc', disp=0)
  yhat = model_fit.forecast()[0]
  yhat = bias + inverse_difference(history, yhat, months_in_year)
  predictions.append(yhat)
  # observation
  obs = y[i]
  history.append(obs)
  print( '>Predicted=%.3f, Expected=%.3f' % (yhat, obs))
# report performance
rmse = sqrt(mean_squared_error(y, predictions))
print('RMSE: %.3f' % rmse)
pyplot.plot(y)
pyplot.plot(predictions, color= 'red')
pyplot.show()

"""* Loading and validating the finalized model over the 12 months of forecast sales graph looks satistying.
* Therefore the plot of the expected values is represented in Blue and the predictions in Red for the validation dataset.

![images.jpeg](data:image/jpeg;base64,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)
"""