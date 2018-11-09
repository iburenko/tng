from datetime import datetime
from tradingene.data.load import import_data
from tradingene.algorithm_backtest.tng import TNG
import tradingene.backtest_statistics.backtest_statistics as bs
from sklearn.preprocessing import StandardScaler
from keras.models import Sequential
from keras.layers import Dense
from keras.initializers import he_normal, he_uniform
from keras.layers.normalization import BatchNormalization
import numpy as np

LOOKBACK = 5 # How many prior candle bars each train sample embraces.
NUM_FEATURES = LOOKBACK*2 # The number of features. This depends on how you implement the "calculate_input()" function. 
    # This time the number of features equals the "lookback" period.   
LOOKFORWARD = 1 # How far in the future the algorithm "looks" and foresees.
NUM_EPOCHS = 100 # The number of epochs to train your model through.
TIMEFRAME = 60 # The time frame.
TICKER = "btcusd" # The ticker.
START_TRAIN_DATE = datetime(2017, 6, 1) # When a train period starts...
END_TRAIN_DATE = datetime(2017, 7, 1) # When the train period ends and the test starts...
END_TEST_DATE = datetime(2017, 7, 6) # When the test ends...

alg = None # An instance of the "TNG" class used for simulated trading

scaler = None # An instance of the "StandardScaler" class used to normalize data

def prepare_model():
    global scaler

    data = import_data(
        TICKER, TIMEFRAME, START_TRAIN_DATE, END_TRAIN_DATE, 
        calculate_input, LOOKBACK, calculate_output, LOOKFORWARD,
        split = (100, 0, 0) # This time we need only a train set (100% for train set, 0% for test and validation ones)
    )
    scaler = StandardScaler() # Creating an instance of a scaler.
    scaler.fit( data['train_input'] ) # Fitting the scaler.
    data_scaled = scaler.transform( data['train_input'] ) # Normalizing data

    # Creating a model...
    m = Sequential() # Creating a model class instance.
    # The number of nodes in the first hidden layer equals the number of features.
    m.add(Dense(units=NUM_FEATURES, activation='tanh', input_dim=NUM_FEATURES, kernel_initializer=he_uniform(1)))
    # Adding another hidden layer 
    m.add(Dense(NUM_FEATURES, activation='tanh'))
    # Adding an output layer
    m.add(Dense(1, activation='linear'))
    # Compiling the model
    m.compile(loss='mean_squared_error', optimizer='sgd', metrics=['accuracy'])

    m.fit(data_scaled, data['train_output'], epochs=NUM_EPOCHS) # Training the model
    return m
# end of load_data


def calculate_input(data):
    input_vec = np.zeros(NUM_FEATURES) # A vector to store inputs 
    for i in range(LOOKBACK):  
        input_vec[i*2] = np.log(data['open'][i] / data['close'][0])
        input_vec[i*2+1] = data['vol'][i]
    return np.array([input_vec])


def calculate_output(data):
    return (data['close'][LOOKFORWARD-1] - data['open'][0]) /  data['open'][0]


def onBar(instrument):
    inp = calculate_input( instrument.rates[1:LOOKBACK+1] ) # Calculating inputs
    inp = scaler.transform( inp ) # Scaling...

    prognosis = model.predict([inp]) # Making prediction
    if prognosis > 0:    # If market rising is predicted...
        alg.buy()       # ...trading long.
    elif prognosis < 0:  # If market falling is predicted...
        alg.sell()      # ... trading short.

model = prepare_model() # Creating a network (an ML-model).
alg = TNG(END_TRAIN_DATE, END_TEST_DATE) # Creating an instance of TNG class to run algorithm within.
alg.addInstrument(TICKER) # Adding an instrument.
alg.addTimeframe(TICKER, TIMEFRAME) # Adding a time frame. 
alg.run_backtest(onBar) # Backtesting...

stat = bs.BacktestStatistics(alg) # Retrieving statistics of the backtest

pnl = stat.calculate_PnL() # Retrieving the PnL.
num_positions = stat.calculate_number_of_trades() # Retrieving the number of trades done.
print("pnl=%f, num_positions=%d" % (pnl, num_positions) )

stat.backtest_results() # Displaying the backtest statistics
