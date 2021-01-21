import pandas
import numpy

def read_pqm_csv(filename):
    pqm = pandas.read_csv(filename, skiprows=20, skip_blank_lines=False)
    if (len(pqm.columns) == 6):
        pqm.columns = ['event_number', 'start_time', 'description', 'extreme',
                'end_time_duration_degree', 'drop_me']
        pqm = pqm.drop(['drop_me'], axis=1)
    else:
        pqm.columns = ['event_number', 'start_time', 'description', 'extreme',
                'end_time_duration_degree']
    if (pqm['start_time'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}:\d{2}").all()):
        pqm['start_time'] = pandas.to_datetime(
            pqm['start_time'], format="%d-%m-%Y %H:%M:%S")
    elif (pqm['start_time'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}").all()):
        pqm['start_time'] = pandas.to_datetime(
            pqm['start_time'], format="%d-%m-%Y %H:%M")
    else:
        print(pqm['start_time'].loc[~ pqm['start_time'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}")])
        raise Exception("uh oh")
    pqm = pqm.set_index(['start_time'])
    pqm.index = pqm.index.tz_localize(tz="Asia/Kolkata")
    pqm.index.name = "date"
    pqm = pqm.sort_values(by=['date', 'event_number'])
    pqm = pqm.dropna(how="all") # mitigate presumed excel damage
    return pqm

def find_outages(pqm):
    outages = pqm[pqm['description'] == "Outage"]
    outages = outages.drop(['event_number', 'description', 'extreme'], axis=1)
    outages.columns = ['end']
    outages = outages.loc[~ outages['end'].str.contains('Open Event')]

    # this format sometimes gives a full datetime as the end,
    # and sometimes a duration expressed as hh:mm:ss :'(
    # AND SOMETIMES A NUMBER OF CYCLES :-(   :'(
    # AND SOMETIMES A DURATION EXPRESSED AS e.g. "1.5 seconds" :'(  :'(  :'(
    cycles = outages.loc[outages['end'].str.contains('cycles')]
    cycle_endings = cycles['end'].str.replace(" cycles", "")
    cycle_endings = cycle_endings.astype(float) / 50
    cycle_endings = pandas.to_timedelta(cycle_endings, unit="seconds")
    cycle_endings = cycle_endings.index + cycle_endings
    cycles = cycles.assign(end=cycle_endings)
    outages = outages.loc[~ outages['end'].str.contains('cycles')]

    durations_decimal = outages.loc[outages['end'].str.contains('seconds')]
    durations_decimal_endings = durations_decimal['end'].str.replace(" seconds", "")
    outages = outages.loc[~ outages['end'].str.contains('seconds')]

    endings_1 = outages.loc[outages['end'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}:\d{2}")]
    end_dts_1 = pandas.to_datetime(
            endings_1.loc[:, 'end'], format="%d-%m-%Y %H:%M:%S")
    end_dts_1 = [pandas.Timestamp(x, tz="Asia/Kolkata") for x in end_dts_1]
    endings_1 = endings_1.assign(end=end_dts_1)
    outages = outages.loc[~ outages['end'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}:\d{2}")]

    endings_2 = outages.loc[outages['end'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}$")]
    end_dts_2 = pandas.to_datetime(
            endings_2.loc[:, 'end'], format="%d-%m-%Y %H:%M")
    end_dts_2 = [pandas.Timestamp(x, tz="Asia/Kolkata") for x in end_dts_2]
    endings_2 = endings_2.assign(end=end_dts_2)

    durations = outages.loc[~ outages['end'].str.contains('-')]
    deltas = [pandas.Timedelta(x) for x in durations['end']]
    endpoints = [a + b for a, b in zip(durations.index, deltas)]
    durations = durations.assign(end=endpoints)
    outages = pandas.concat([endings_1, endings_2, durations, cycles])
    outages = outages.sort_index()
    outages['end'] = pandas.to_datetime(outages['end'])
    return outages


def find_non_outages(pqm):
    non_outages = pqm[pqm['description'] != "Outage"]
    non_outages = non_outages.replace(to_replace="\d+ [HNG]-[HNG] Impulses?",
            value="Impulse", regex=True)
    non_outages = non_outages.replace(to_replace="[HNG]-[HNG] Sag",
            value="Sag", regex=True)
    non_outages = non_outages.replace(to_replace="[HNG]-[HNG] Surge",
            value="Surge", regex=True)
    non_outages.columns = ['event_number', 'description', 'extreme', 'end']
    non_outages = non_outages.loc[~ non_outages['end'].str.contains('Open Event').astype('boolean')]

    # this format sometimes gives a full datetime as the end,
    # and sometimes a duration expressed as hh:mm:ss :'(
    # AND SOMETIMES A NUMBER OF CYCLES :-(   :'(
    # AND SOMETIMES A DURATION EXPRESSED AS e.g. "1.5 seconds" :'(  :'(  :'(
    cycles = non_outages.loc[non_outages['end'].str.contains('cycles')]
    cycle_endings = cycles['end'].str.replace(" cycles", "")
    cycle_endings = cycle_endings.astype(float) / 50
    cycle_endings = pandas.to_timedelta(cycle_endings, unit="seconds")
    cycle_endings = cycle_endings.index + cycle_endings
    cycles = cycles.assign(end=cycle_endings)
    non_outages = non_outages.loc[~ non_outages['end'].str.contains('cycles')]

    durations_decimal = non_outages.loc[non_outages['end'].str.contains('seconds')]
    durations_decimal_endings = durations_decimal['end'].str.replace(" seconds", "")
    non_outages = non_outages.loc[~ non_outages['end'].str.contains('seconds')]

    endings_1 = non_outages.loc[non_outages['end'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}:\d{2}")]
    end_dts_1 = pandas.to_datetime(
            endings_1.loc[:, 'end'], format="%d-%m-%Y %H:%M:%S")
    end_dts_1 = [pandas.Timestamp(x, tz="Asia/Kolkata") for x in end_dts_1]
    endings_1 = endings_1.assign(end=end_dts_1)
    non_outages = non_outages.loc[~ non_outages['end'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}:\d{2}")]

    endings_2 = non_outages.loc[non_outages['end'].str.match(r"\d{2}-\d{2}-\d{4} \d\d?:\d{2}$")]
    end_dts_2 = pandas.to_datetime(
            endings_2.loc[:, 'end'], format="%d-%m-%Y %H:%M")
    end_dts_2 = [pandas.Timestamp(x, tz="Asia/Kolkata") for x in end_dts_2]
    endings_2 = endings_2.assign(end=end_dts_2)

    durations = non_outages.loc[~ non_outages['end'].str.contains('-')]
    durations = non_outages.loc[~ non_outages['end'].str.contains('°')]
    deltas = [pandas.Timedelta(x) for x in durations['end']]
    endpoints = [a + b for a, b in zip(durations.index, deltas)]
    durations = durations.assign(end=endpoints)

    degrees = non_outages.loc[non_outages['end'].str.contains('°')]
    degree_endings = degrees['end']
    print(degree_endings)
    #degree_endings = degrees['end'].str.replace("°", "")
    # Less than one cycle will be reported as position on the sine wave. (for example, 200°)
    #degree_endings = numpy.repeat(1. / 50 / 360, len(degrees))
    #degree_endings.assign(numpy.repeat(1. / 50 / 360, len(degrees)))
    degree_endings[:] = numpy.repeat(1. / 50 / 360, len(degrees))
    #degree_endings = degree_endings.astype(float) / 50 / 360
    print(degree_endings)
    degree_endings = pandas.to_timedelta(degree_endings, unit="seconds")
    degree_endings = degree_endings.index + degree_endings
    degrees = degrees.assign(end=degree_endings)

    non_outages = pandas.concat([endings_1, endings_2, durations, cycles, degrees])
    non_outages = non_outages.sort_index()
    non_outages['end'] = pandas.to_datetime(non_outages['end'])
    return non_outages


def find_sags(non_outages):
    sags = non_outages[non_outages['description'].str.contains("Sag")]
    return sags


def find_impulses(non_outages):
    impulses = non_outages[non_outages['description'].str.contains("Impulse")]
    return impulses


def find_surges(non_outages):
    surges = non_outages[non_outages['description'].str.contains("Surge")]
    return surges


def find_hf(non_outages):
    hf = non_outages[non_outages['description'].str.contains("High Frequency")]
    return hf


def power_frame(outages):
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
    return new_frame
