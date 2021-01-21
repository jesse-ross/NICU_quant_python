import numpy
import pandas
import altair
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from NICU_offline.pqm import power_frame, find_sags, find_surges, find_impulses, find_hf

def read_hobo_csv(filename):
    hobo = pandas.read_csv(filename, header=1, usecols=[1,2])
    hobo = hobo.dropna()
    hobo.columns = ['date', 'amps']
        #if (pqm['start_time'].str.match(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}").all()):
    if hobo['date'].str.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}").all():
        hobo['date'] = pandas.to_datetime(
                hobo['date'], format="%m/%d/%Y %I:%M:%S %p")
    elif hobo['date'].str.match(r"\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}").all():
        hobo['date'] = pandas.to_datetime(
                hobo['date'], format="%m/%d/%y %I:%M:%S %p")
    else:
        raise Exception("uh oh")
    hobo = hobo.set_index(['date'])

    hobo.index = hobo.index.tz_localize(tz="Asia/Kolkata")
#    first_time = numpy.min(hobo.index)
#    last_time = numpy.max(hobo.index)
#    edge_period = pandas.to_timedelta(60, unit="minute")
#    hobo = hobo.loc[hobo.index > first_time + edge_period]
#    hobo = hobo.loc[hobo.index < last_time - edge_period]
    return hobo

# TODO: overlay power availability AND other power events
def hobo_plot(hobo, title=""):
    hobo = hobo.reset_index()
    p = altair.Chart(hobo).mark_line().encode(
        x='date:T',
        y='amps')
#        y=altair.Y('amps',
#            scale=altair.Scale(domain=(0, 5))
#           ))
    p = p.properties(width=800)
    if len(title) > 0:
        p = p.properties(title=title)
    return p


def power_plot(outages):
    new_frame = pandas.DataFrame()
    outages = outages.reset_index()
    outages = outages.assign(power=0)
    for i in range(len(outages)):
        my_row = outages.iloc[[i]]
        begin_row = my_row.assign(power=1)
        end_row = my_row.assign(date=my_row['end'])
        end_row_1 = end_row.assign(power=0)
        end_row_2= end_row.assign(power=1)
        new_frame = pandas.concat([new_frame, begin_row, my_row,
            end_row_1, end_row_2])
    new_frame = new_frame.drop(['end'], axis=1)
    return altair.Chart(new_frame).mark_line().encode(x='date:T',y='power:Q')


def enriched_hobo_plot(hobo, o, non_o, title="", threshold_y=None, etype=None):
    sags = find_sags(non_o)
    impulses = find_impulses(non_o)
    surges = find_surges(non_o)
    hf = find_hf(non_o)

    axis_ranges = {
            "Radiant Warmer": [0, 4],
            "Pulse Oximeter": [0, 0.04],
            "Infusion Pump": [0, 0.07],
            "Bubble CPAP Unit": [0, 0.06],
            "Phototherapy Unit (LED type)": [0, 1],
            "Phototherapy Unit": [0, 1],
            "Oxygen Concentrator": [0, 2.3],
            "Suction Pump/Aspirator": [0, 3]}

    o2 = power_frame(o)
    
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1
#        x_title="Date",
#        subplot_titles=['Power Consumption (Amps)', 'Power Availability'],
    )
    
    fig.add_trace(go.Scatter(x=hobo.index, y=hobo['amps'], showlegend=False),
                  row=1, col=1)
    if threshold_y is not None:
	    fig.add_trace(go.Scatter(x=hobo.index,
	        y=numpy.repeat(threshold_y, len(hobo.index)), showlegend=False,
                line=dict(dash="dash")),
	        row=1, col=1)
    
    fig.add_trace(go.Scatter(x=o2['date'], y=o2['power'], showlegend=False),
                  row=2, col=1)
    
    fig.add_trace(
            go.Scatter(x=sags.index, y=numpy.repeat(0.8, len(sags.index)),
                       mode="markers", name="Sags"),
            row=2, col=1)
    fig.add_trace(
            go.Scatter(x=surges.index, y=numpy.repeat(0.6, len(surges.index)),
                       mode="markers", name="Surges"),
            row=2, col=1)
    fig.add_trace(
            go.Scatter(x=impulses.index,
                       y=numpy.repeat(0.4, len(impulses.index)),
                       mode="markers", name="Impulses"),
            row=2, col=1)
    fig.add_trace(
            go.Scatter(x=hf.index, y=numpy.repeat(0.2, len(hf.index)),
                mode="markers", name="High Frequency"),
            row=2, col=1)
    fig.update_layout(title=title, font=dict(size=20))

# This is on hold for now - attempt to add rectangles to show nightly 
# planned disuse periods.
#    starts = pandas.date_range(numpy.min(hobo.index).ceil(freq="D"),
#            end=numpy.max(hobo.index), freq="D")
#    ends = starts + pandas.Timedelta("7 hours")

    fig.update_yaxes(title="Power Consumption (Amps)", row=1, col=1)
    if etype is not None:
        fig.update_yaxes(range=axis_ranges[etype], row=1, col=1)
    fig.update_yaxes(title="Power Availability (On/Off)",
            tickvals=[0, 1], ticktext=["Off", "On"], row=2, col=1)
    return fig


def enriched_hobo_plot_2(hobo, o, non_o, title="", threshold_y=None, etype=None):
    sags = find_sags(non_o)
    impulses = find_impulses(non_o)
    surges = find_surges(non_o)
    hf = find_hf(non_o)

    axis_ranges = {
            "Radiant Warmer": [0, 4],
            "Pulse Oximeter": [0, 0.04],
            "Infusion Pump": [0, 0.07],
            "Bubble CPAP Unit": [0, 0.06],
            "Phototherapy Unit (LED type)": [0, 1],
            "Phototherapy Unit": [0, 1],
            "Oxygen Concentrator": [0, 2.3],
            "Suction Pump/Aspirator": [0, 3]}

    o2 = power_frame(o)
    
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.45, 0.1, 0.45]
#        x_title="Date",
#        subplot_titles=['Power Consumption (Amps)', 'Power Availability'],
    )
    
    fig.add_trace(go.Scatter(x=hobo.index, y=hobo['amps'], showlegend=False),
                  row=1, col=1)
    if threshold_y is not None:
	    fig.add_trace(go.Scatter(x=hobo.index,
	        y=numpy.repeat(threshold_y, len(hobo.index)), showlegend=False,
                line=dict(dash="dash")),
	        row=1, col=1)

    fig.add_trace(go.Scatter(x=o2['date'], y=o2['power'], showlegend=False),
                  row=2, col=1)
    
    fig.add_trace(go.Histogram(x=sags.index, name="Sags", xbins=go.histogram.XBins(size=1000*60*60*24)), row=3, col=1)
    fig.add_trace(go.Histogram(x=impulses.index, name="Impulses", xbins=go.histogram.XBins(size=1000*60*60*24)), row=3, col=1)
    fig.add_trace(go.Histogram(x=surges.index, name="Surges", xbins=go.histogram.XBins(size=1000*60*60*24)), row=3, col=1)
    fig.add_trace(go.Histogram(x=hf.index, name="High Frequency", xbins=go.histogram.XBins(size=1000*60*60*24)), row=3, col=1)
    
    fig.update_layout(title=title, font=dict(size=20))

# This is on hold for now - attempt to add rectangles to show nightly 
# planned disuse periods.
#    starts = pandas.date_range(numpy.min(hobo.index).ceil(freq="D"),
#            end=numpy.max(hobo.index), freq="D")
#    ends = starts + pandas.Timedelta("7 hours")

    fig.update_yaxes(title="Current (Amps)", row=1, col=1)
    if etype is not None:
        fig.update_yaxes(range=axis_ranges[etype], row=1, col=1)
    #fig.update_yaxes(title="Power Availability (On/Off)",
    fig.update_yaxes(title="Power (On/Off)",
            tickvals=[0, 1], ticktext=["Off", "On"], row=2, col=1)
    fig.update_yaxes(title="Power Events", row=3, col=1)
    return fig
