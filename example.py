from tng.algorithm_backtest.tng import TNG
from datetime import datetime
from time import time
import pandas as pd
import matplotlib.pyplot as plt
from bokeh.plotting import figure, show, output_file
import datetime as dt
from bokeh.models import ColumnDataSource, CustomJS, Div, Button, Band
from bokeh.layouts import column, row
from bokeh.models.markers import Triangle
from bokeh.models.tools import HoverTool
import tng.backtest_statistics.backtest_statistics as bs
from bokeh import events
from bokeh.core import properties
import numpy as np

name = "my_name"
regime = "SP"

start_date = datetime(2018, 1, 1)
end_date = datetime(2018, 1, 3)

timeframe = 5
alg = TNG(name, regime, start_date, end_date)

alg.addInstrument("btcusd")
alg.addTimeframe("btcusd", timeframe)

entry = 0
signal = 0




def plot_bars(alg, timeframe):
  
    def update_triangle(source):
        return CustomJS(args=dict(source=source, xr=p.x_range), code="""
        console.log(xr.start, xr.end)
        var data = source.data;
        var x = data["size"]
        var range = data["range"]
        var cond = range[0] / (xr.end - xr.start)
        if (Math.abs(cond - 1) > 0.001)
            for (var i = 0; i < x.length; i++) {
                x[i] = x[i] * cond;
                range[i] = xr.end - xr.start
            }
        console.log(x[0])
        console.log(range[0])
        console.log(cond)
        source.change.emit();
        """)

    close_df = pd.DataFrame()
    open_df = pd.DataFrame()

    for i in range(len(alg.positions)):
        if (alg.positions[i].closed):
            pos_trades = alg.positions[i].trades
            for j in range(len(pos_trades)):

                if  j < len(pos_trades) - 1:
                    close_df = close_df.append([[pos_trades[j].close_time, pos_trades[j].close_price[0], pos_trades[j].side, 0, 0]])
                elif(pos_trades[j].close_time > 0):
                    close_df = close_df.append([[pos_trades[j].close_time, pos_trades[j].close_price[0], pos_trades[j].side, 1, alg.positions[i].profit[0]]])
                if  j > 0:
                    open_df = open_df.append([[pos_trades[j].open_time, pos_trades[j].open_price[0], pos_trades[j].side, 0]])
                else:
                    open_df = open_df.append([[pos_trades[j].open_time, pos_trades[j].open_price[0], pos_trades[j].side, 1]])

    df = list(alg.instruments)[0].rates
    df = pd.DataFrame(df[1:(len(df) - 50)])
    df['size'] = 12.0
    rad = []
    rad.append(12.0)
    size = properties.Int()
    size = 12
    rad.append(int(rad[0]))
    close_df.columns = ['time', 'close_price', 'close_side', 'last_indic', 'profit']
    open_df.columns = ['time', 'open_price', 'open_side', 'first_indic']
    
    df["date"] = pd.to_datetime(df["time"].astype(str), format='%Y%m%d%H%M%S%f')
    df = df.drop(['time'], axis = 1)
    close_df["date"] = pd.to_datetime(close_df["time"].astype(str), format='%Y%m%d%H%M%S%f')
    close_df = close_df.drop(['time'], axis = 1)
    open_df["date"] = pd.to_datetime(open_df["time"].astype(str), format='%Y%m%d%H%M%S%f')
    open_df = open_df.drop(['time'], axis = 1)

    df = pd.merge(df, close_df, how = 'left', on ='date')
    df = pd.merge(df, open_df, how = 'left', on ='date')

    w = (timeframe / 2) * 60 * 1000
    

    output_file("candlestick.html", title="candlestick.py example")
    TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

    inc = df.close > df.open
    dec = df.open > df.close
    ind_close = df["last_indic"] == 1
    ind_open = df["first_indic"] == 1
    ind_close_pos = df['close_side'] == -1
    ind_open_pos = df['open_side'] == -1
    
    max_range = (df['high'] - df['low']).max()
    min_low_range = df['low'][(len(df)-31):(len(df)-1)].min()

    max_high_range = df['high'][(len(df)-31):(len(df)-1)].max()

    p = figure(x_axis_type="datetime", tools=TOOLS, plot_width=1000, toolbar_location="left",
    x_range=(df["date"].min() - dt.timedelta(minutes = timeframe) , df["date"].min() + dt.timedelta(minutes = timeframe * 30)),
    y_range = (min_low_range - max_range / 2, max_high_range + max_range / 2))

    df['range'] = p.x_range.end - p.x_range.start
    mysource1 = ColumnDataSource(df[inc])
    mysource2 = ColumnDataSource(df[dec])
  
    source1 = ColumnDataSource(df[ind_open & (df['open_side'] == -1)])
    source2 = ColumnDataSource(df[ind_open & (df['open_side'] == 1)])
    source3  = ColumnDataSource(df[ind_close & (df['close_side'] == 1)])
    source4  = ColumnDataSource(df[ind_close & (df['close_side'] == -1)])

    p.segment(df.date, df.high, df.date, df.low, color="black")

    p.vbar(source = mysource1, x="date", width = w, bottom="open", top="close", fill_color="honeydew", line_color="black")
    p.vbar(source = mysource2, x="date", width = w, bottom="close", top="open", fill_color="deepskyblue", line_color="black")

    hover = HoverTool(tooltips = [('high', '@high'),
                                  ('low', '@low'),
                                  ('open', '@open'),
                                  ('close', '@close')])
    p.add_tools(hover)

    p.triangle(x="date", y="open_price", size="size", fill_alpha=0.9, source = source1, fill_color="green")
    p.triangle(x="date", y="open_price", size="size", fill_alpha=0.9, source = source2, fill_color="yellow")

    p.inverted_triangle(x="date", y="close_price", size="size", fill_alpha=0.9, source = source3, fill_color="yellow")
    p.inverted_triangle(x="date", y="close_price", size="size", fill_alpha=0.9, source = source4, fill_color="green")

    p.x_range.js_on_change('start', update_triangle(source1))
    p.x_range.js_on_change('start', update_triangle(source2))
    p.x_range.js_on_change('start', update_triangle(source3))
    p.x_range.js_on_change('start', update_triangle(source4))

    p.xaxis.major_label_orientation = 3.14/4
    p.grid.grid_line_alpha = 0.5
    point_attributes = ['x','y','sx','sy']                     # Point events
    wheel_attributes = point_attributes+['delta']

    show(p)

    df['profit'][np.isnan(df['profit'])] = 0.0
    df['cumsum'] = df['profit'].cumsum(skipna=True)

    plot_prof = figure(x_axis_type="datetime", tools=TOOLS, plot_width=1000, toolbar_location="left",
    x_range=(df["date"].min(), df["date"].max()),
    y_range =(df['cumsum'].min() * 1.5, df['cumsum'].max() * 1.5))
    df['pos'] = 0.0
    df['pos'] = df['cumsum'][df['cumsum'] > 0]
    df['pos'][np.isnan(df['pos'])] = 0
    df['neg'] = 0.0
    df['neg'] = df['cumsum'][df['cumsum'] < 0]
    df['neg'][np.isnan(df['neg'])] = 0

    df['zeros'] = 0.0
    print(df['pos'])
    print(df['zeros'])
    source = ColumnDataSource(df)

    band = Band(base='date', lower='zeros', upper='pos', source = source, fill_alpha=0.7, fill_color="green")
    plot_prof.add_layout(band)
    band = Band(base='date', lower='zeros', upper='neg', source = source, fill_alpha=0.7, fill_color="red")
    plot_prof.add_layout(band)
    hover2 = HoverTool(tooltips = [('pos', '@pos')])
    plot_prof.add_tools(hover2)
    show(plot_prof)

def on_bar(instrument):
  #  print(instrument.time)
    global entry
    global signal
    if entry == 0:
        if (instrument.high[1] / instrument.high[2] < 1
                and instrument.low[1] / instrument.low[2] < 1):
            alg.sell()
            entry = -1
            return
        elif (instrument.high[1] / instrument.high[2] > 1
              and instrument.low[1] / instrument.low[2] > 1):
            alg.buy()
            entry = 1
            return
    ############################### old version ################################
    elif entry == 1:
        if (instrument.high[1] / instrument.high[2] < 1
                and instrument.low[1] / instrument.low[2] < 1):
            #alg.closePosition()
            alg.sell()
            entry = -1
            return
    elif entry == -1:
        if (instrument.high[1] / instrument.high[2] > 1
                and instrument.low[1] / instrument.low[2] > 1):
            #alg.closePosition()
            alg.buy()
            entry = 1
            return


  #  update_triangle = CustomJS(args=dict(size=size), code="""
 #   // JavaScript code goes here
  #  size = size + 1
  #  size.change.emit();
# """)

    
alg.run_backtest(on_bar)

#for pos in alg.positions:
#    for trade in pos.trades:
#        print(trade.open_time, trade.open_price, trade.close_time,
#              trade.close_price)

new_stat = bs.BacktestStatistics(alg.positions)
new_stat.backtest_results()

plot_bars(alg, timeframe)
