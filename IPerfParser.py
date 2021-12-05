import pandas as pd
from io import StringIO
from functools import reduce

# Given the output of an IPerf run, converts it to a table.
# Host conditions should be a tuple of the hosts and their tcp congestion algorithm
# e.g. ('A', 'reno')
def parseIPerf(output, host_conditions):
    # Filters transcript to just contain the pertinent rows
    hosts = list(host_conditions.keys())
    filtered_lines = []
    for i, host_out in enumerate(output):
        filtered = ''
        for line in host_out.stdout:
            if "sec" in line:
                filtered += hosts[i] + ': ' + line + '\n'
        if len(filtered) > 0:
            filtered_lines.append(filtered)

    tables = [pd.read_fwf(StringIO(filtered), colspecs=[(0, 1), (3, 8), (9, 22), (24, 35), (37, 51)],
                        header=None, names=["Host", "ID", "Interval",
                                            "Transfer - " + filtered[0],
                                            "Bandwidth - " + filtered[0]])
              for filtered in filtered_lines]
    hosts = []
    for table in tables:
        #Cleaning up the table
        #table['Control'] = table.apply(lambda row: host_conditions[row.Host], axis=1)
        host = table.iloc[0]["Host"]
        hosts.append(host)
        table.drop(["Host", 'ID'], axis=1, inplace=True)
        table[["Transfer - " + host, "Transfer Unit - " + host]] = table["Transfer - " + host].str.split(" ", expand=True)
        table[["Bandwidth - " + host, "Bandwidth Unit - " + host]] = table["Bandwidth - " + host].str.split(" ", expand=True)

    result = reduce(lambda left, right: pd.merge(tables[0], tables[1], on="Interval"), tables)

    rearranged_columns = ["Interval"]
    for host in hosts:
        rearranged_columns.append("Transfer - " + host)
        rearranged_columns.append("Transfer Unit - " + host)
        rearranged_columns.append("Bandwidth - " + host)
        rearranged_columns.append("Bandwidth Unit - " + host)

    return result.reindex(columns=rearranged_columns)
