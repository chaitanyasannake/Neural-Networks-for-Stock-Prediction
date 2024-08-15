# Created by Lena
import pandas as pd
import math
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
import warnings
warnings.filterwarnings('ignore')

import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

PATH = "plots/lena/"

df = pd.read_csv("data/sequences/1.csv", index_col=0, parse_dates=True)
df.head(10)

# take first 4 predictor variables
dataset = df.iloc[:, 0:4]
dataset.head(5)

values = dataset.values.astype('float32')


# split a multivariate sequence into samples
def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
    """
	Frame a time series as a supervised learning dataset.
	Arguments:
    :param data: Sequence of observations as a list or NumPy array.
    :param n_in: Number of lag observations as input (X).
    :param n_out: Number of observations as output (y).
    :param dropnan: Boolean whether or not to drop rows with NaN values.
    :return: Pandas DataFrame of series framed for supervised learning.
    """

    n_vars = 1 if type(data) is list else data.shape[1]
    dataframe = pd.DataFrame(data)
    cols, names = list(), list()
    # input sequence (t-n, ... t-1)
    for i in range(n_in, 0, -1):
        cols.append(dataframe.shift(i))
        names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
    # forecast sequence (t, t+1, ... t+n)
    for i in range(0, n_out):
        cols.append(dataframe.shift(-i))
        if i == 0:
            names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
        else:
            names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
    # put it all together
    agg = pd.concat(cols, axis=1)
    agg.columns = names
    # drop rows with NaN values
    if dropnan:
        agg.dropna(inplace=True)
    return agg


# transform values with 1 step back and predicting 5 observations (t, t+1, t+2, t+3, t+4)
reframed = series_to_supervised(values, 1, 5)
print(reframed.head(5))

# split into train and test sets
transformed_values = reframed.values
train = transformed_values[:25, :]
test = transformed_values[25:, :]

# split into input and outputs
train_X, train_y = train[:, :4], train[:, 4:]
test_X, test_y = test[:, :4], test[:, 4:]

# reshape input to be 3D (samples, timesteps, features)
train_X = train_X.reshape((train_X.shape[0], 1, train_X.shape[1]))
test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))
print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)

n_timesteps = 1
n_features = 4

# Build LSTM model with 2 layers and 50 nodes each
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(n_timesteps, n_features)))  # (1,4)
model.add(Dropout(0.2))
model.add(LSTM(units=50))
model.add(Dense(20, activation='relu'))

# we need to predict 4x5=20 outputs
model.compile(loss='mean_squared_error', optimizer='adam')

# fit network
history = model.fit(train_X, train_y, epochs=50, batch_size=5, validation_data=(test_X, test_y),
                    verbose=2, shuffle=False)

# plot history
plt.plot(history.history['loss'], label='train')
plt.plot(history.history['val_loss'], label='test')
plt.legend()
plt.show()

# make a prediction
# trainPredict = model.predict(train_X)
testPredict = model.predict(test_X)

testScore = math.sqrt(mean_squared_error(test_y, testPredict))
print('Test Score: %.2f RMSE' % (testScore))
