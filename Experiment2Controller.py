from pssh.clients import ParallelSSHClient, SSHClient
from pssh.config import HostConfig
import IPerfParser as Parser
from itertools import combinations_with_replacement
import pandas as pd
from tqdm import tqdm

# Manages config2 settings using config2.txt
configs = {}
with open("config2") as file:
    for line in file:
        try:
            key, value = line.split(":")
            value = value.strip()
        except ValueError:
            key = line.split(":")[0]
            value = None
        configs[key] = value

# Setting up hosts
host_names = ['A', 'B', 'C']
host_ips = [configs['HOST_' + host_name + '_IP'] for host_name in host_names]
host_configs = [HostConfig(port=int(configs['HOST_' + host_name + '_PORT']),
                           user=configs['USERNAME'],
                           password=configs['PASSPHRASE']) for host_name in host_names]
host_client = ParallelSSHClient(host_ips, host_config=host_configs)

# Setting up the delay client
delay_ip = configs['DELAY_IP']
delay_client = SSHClient(delay_ip,
                         port=int(configs['DELAY_PORT']),
                         user=configs['USERNAME'],
                         password=configs['PASSPHRASE'])

# Checks current TCP on each machine
# cmd = 'cat /proc/sys/net/ipv4/tcp_congestion_control'
# output = host_client.run_command(cmd)
# for i, host_out in enumerate(output):
#     for line in host_out.stdout:
#         print(host_names[i] + ":" + line)

# Gets all loaded TCPs on each machine
cmd = 'ls -la /lib/modules/$(uname -r)/kernel/net/ipv4'
hosts_loaded = []
output = host_client.run_command(cmd)
for i, host_out in enumerate(output):
    loaded = []
    for line in host_out.stdout:
        if "tcp_" in line:
            loaded.append(line[line.index("tcp_"):len(line) - 3])

    hosts_loaded.append(loaded)

# Installs all loaded TCPs on each machine
cmds = list(map(lambda loaded: " ".join(list(map(lambda tcp: 'modprobe -a ' + tcp, loaded))), hosts_loaded))
output = host_client.run_command("%s", host_args=cmds, sudo=True)

# Gets all available installed TCPs on each machine
cmd = "/sbin/sysctl net.ipv4.tcp_available_congestion_control"
output = host_client.run_command(cmd)
hosts_installed = []
for i, host_out in enumerate(output):
    for line in host_out.stdout:
        hosts_installed.append(set(line[line.index("=") + 2:].split(" ")))

# Contains a list of common tcp congestion controls across the four machines
installed = set.intersection(*hosts_installed)

# print(installed)

# Runs the experiment with the given control on each respective host
# and the switch
def run_experiment(controls):
    # Setting controls for each host
    cmds = ['sysctl net.ipv4.tcp_congestion_control=' + controls['A'],
            '',
            'sysctl net.ipv4.tcp_congestion_control=' + controls['C']]
    host_client.run_command('%s', host_args=cmds, sudo=True)

    # Setting up send/receive window size
    window_size = "'10000 80000 7500000'" #Minimum, default, maximum (in bytes)
    cmds = ["sysctl -w net.ipv4.tcp_wmem=" + window_size,
            "sysctl -w net.ipv4.tcp_rmem=" + window_size,
            "sysctl -w net.ipv4.tcp_wmem=" + window_size]
    # Add switch commands here using delay_client
    delay_client.run_command("tc qdisc add dev eth1 root netem rate 1gbps delay 30ms loss 0.1%", sudo=True)
    delay_client.run_command("tc qdisc add dev eth2 root netem rate 1gbps delay 30ms loss 0.1%", sudo=True)

    # Setting up iperf server on B and D:
    cmds = ['',
            'iperf -s',
            '']
    host_client.run_command('%s', host_args=cmds)

    # Running iperf on A and C
    cmds = ['iperf -c ' + "b " + '-i 1 -t 20',
            '',
            'iperf -c ' + "b " + '-i 1 -t 20']
    output = host_client.run_command('%s', host_args=cmds)

    results = Parser.parseIPerf(output, controls)

    # Cleaning up run
    cmds = ['',
            'ps -ef | grep iperf',
            '']
    PIDs = []
    output = host_client.run_command('%s', host_args=cmds)
    for i, host_out in enumerate(output):
        for line in host_out.stdout:
            if "iperf -s" in line:
                PIDs.append(line.split()[1])

    cmds = ['',
            'kill ' + PIDs[0],
            '']
    host_client.run_command('%s', host_args=cmds)

    delay_client.run_command("tc qdisc del dev eth1 root netem", sudo=True)
    delay_client.run_command("tc qdisc del dev eth2 root netem", sudo=True)
    return results


congestion_controls = ["reno", "westwood", "illinois"]
combinations = list(combinations_with_replacement(congestion_controls, 2))
experiment_results = []
experiments = []

for combination in tqdm(combinations):
    for i in range(5):
        experiments.append(combination[0] + "/" + combination[1] + ":" + str(i))
        controls = {"A": combination[0], "B": combination[0], "C": combination[1]}
        experiment_results.append(run_experiment(controls))

results = pd.concat(experiment_results, keys=experiments)
results.to_csv("LongHaulInternet2.csv")
