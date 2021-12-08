# TCP-Fairness
Mini GENI project for BU CS655

In order to run the experiments, first reserve the necessary resources on GENI using the provided Rspec file. The Rspec reserves five machines: four machines A, B, C, and D which will communicate and the delay node which controls network conditions.

Then, note down the username, IP address, and port number of each machine. Fill out the respective config file with this information (config1 for Experiment 1, config2 for Experiment 2). If your private SSH key has a passphrase also include it here to allow your machine to SSH into the reserved machines.

We outline how to run Experiment 1 below, and will describe the differences for running Experiment 2 afterwards:

Open Experiment1Controller.py and edit lines 82 (window_size = "'...'"), 89 (delay_client.run_command(tc qdisc ...), and 90 (delay_client.run_command(tc qdisc ...) in order to change the experiment conditions. Also change line 146 (results.to_csv("...")) to change where it has been saved.

Line 82 changes the buffer size, provide three integer values separated by spaces to set the minimum, default, and maximum buffer sizes for the machines A B C and D. We use the following settings for our three investigated conditions:

1990's Internet: 1000 25000 64000
2020's Internet: 1000 50000 100000
Long Haul: 10000 80000 75000000

Line 89 and 90 change the network conditions (capacity, delay, packet loss rate). Here are the settings we used:

1990's Internet: 32 kbps delay 10ms loss 0.001%
2020's Internet: 100 mbps delay 1ms loss 1%
Long Haul: 1 gbps delay 30ms loss 0.1%

Then run the file. The file will run every combination of tcp reno, tcp illinois, and tcp westwood on the machines (for 20 seconds each run), a total of five times each. This will take approximately 10 minutes and it will save the results to the csv named in line 146 (in the same folder that the python script is in).

From there, to process the data into plots, open data_wrangling.py in the same folder and edit line 137 (data = pd.read_csv("..."), putting in the name of the csv file. You can then run it to generate the plots. If you want to plot a specific run edit line 152 with the name of the run (e.g. "reno/illionois:4" plots the fourth run of reno v illinois)

___

Experiment 2 runs similarly, but instead you will first edit config2.txt with the necessary arguments and then edit lines 81, 86 and 87 to run the experiment with your desired network conditions.
