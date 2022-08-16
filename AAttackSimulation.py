import os
import csv
from subprocess import Popen
from time import sleep, time



from AFatTree import FatTree
from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
import datetime as dt
import math
import matplotlib
import matplotlib.pyplot as plt


from matplotlib.ticker import FuncFormatter





def format_time(n, pos):
    t = dt.datetime.fromtimestamp(n)
    return t.strftime("%H:%M:%S")


def format_y_axis(n, pos):
    if n >= 1e6:
        return '%1.0fM' % (n * 1e-6)
    if n >= 1e3:
        return '%1.0fK' % (n * 1e-3)
    return '%1.0f' % n


def display_ddos_attack(network_info, attack_range, interfaces=[]):
    if len(interfaces) == 0 or len(interfaces) >= 8:
        cols = 3
        r_span = 2
        h_sm = 3.0
    else:
        cols = 1
        r_span = 1
        h_sm = 5.0

    if len(interfaces) == 0:
        rows = math.ceil(len(network_info) / cols) + r_span
    else:
        rows = math.ceil(len(interfaces) / cols) + r_span

    plt_w = 13.0
    plt_h = h_sm * rows
    index = cols * r_span

    plt.figure(1)
    i = index + 1
    for k in sorted(network_info):
        if len(interfaces) > 0 and k not in interfaces:
            continue

        plt.subplot(rows, cols, i)
        y = network_info[k]['load']
        x = network_info[k]['time']
        plt.plot(x, y)
        plt.title(k)
        plt.ylabel('bits/s')

        plt.axvspan(*attack_range, color='red', alpha=0.1)

        ax = plt.gca()
        ax.xaxis.set_major_formatter(FuncFormatter(format_time))
        ax.yaxis.set_major_formatter(FuncFormatter(format_y_axis))
        plt.setp(ax.get_xticklabels(), rotation=30,
                 horizontalalignment='right')

        i += 1

    fig = plt.gcf()
    fig.set_size_inches(plt_w, plt_h)
    fig.tight_layout()
    plt.savefig("plot.png")
    plt.show()

    

class EmulationNetwork:
    def __init__(self, option_1='--flood', option_2='--udp', interfaces=[]):
        self.idle_duration = 5
        self.attack_duration = 5
        self.log = 'log.txt'
        self.option_1 = option_1
        self.option_2 = option_2
        self.interfaces = interfaces
        self.network_data = {}

    def execute(self):
        self.delete_log()
        self.clean_mininet_emulation()
        self.begin_emulation_network()
        self.begin_attack_track()
        sleep(self.idle_duration)
        self.begin_ddos_attack()
        self.ast = time()
        sleep(self.attack_duration)
        self.terminate_ddos_attack()
        self.aet = time()
        sleep(self.idle_duration)
        self.terminate_attack_track()
        self.store_network_info()
        self.delete_log()
        self.terminate_mininet_network()
        self.plot()

    def clean_mininet_emulation(self):
        info('*** Clean Mininet Emulation\n')
        cmd = "mn -c"
        Popen(cmd, shell=True).wait()

    def begin_emulation_network(self):
        self.net = Mininet(topo=FatTree())
        self.net.start()
        for i in range(1, 11):
            s = self.net.get(f's{i}')
            s.cmd(f'ovs-vsctl set bridge s{i} stp-enable=true')
        print("Dumping host connections")

        dumpNodeConnections(self.net.hosts)
        print("Testing network connectivity")
        self.net.pingAll()
        self.net.pingAll()

    def terminate_mininet_network(self):
        self.net.stop()

    def begin_attack_track(self):
        info('*** Begin Attack Track\n')
        cmd = f"bwm-ng -o csv -T rate -C ',' > {self.log} &"
        Popen(cmd, shell=True).wait()

    def terminate_attack_track(self):
        info('*** Terminate Attack Track\n')
        cmd = "killall bwm-ng"
        Popen(cmd, shell=True).wait()

    def begin_ddos_attack(self):
        info('*** Begin DDoS Attack\n')
        h1 = self.net.get('h1')
        h5 = self.net.get('h5')
        ip2 = self.net.get('h2').IP()
        ip3 = self.net.get('h3').IP()
        ip7 = self.net.get('h7').IP()
        ip8 = self.net.get('h8').IP()

        h1.cmd(f"hping3 --traceroute -V {self.option_1} {self.option_2} {ip2} &")
        h1.cmd(f"hping3 --traceroute -V {self.option_1} {self.option_2} {ip3} &")
        h5.cmd(f"hping3 --traceroute -V {self.option_1} {self.option_2} {ip7} &")
        h5.cmd(f"hping3 --traceroute -V {self.option_1} {self.option_2} {ip8} &")

    def terminate_ddos_attack(self):
        info('*** Terminate DDoS Attack\n')
        cmd = "killall hping3"
        Popen(cmd, shell=True).wait()

    def store_network_info(self):
        with open(self.log) as csvf:
            csvr = csv.reader(csvf, delimiter=',')
            for row in csvr:
                key = row[1]
                tme = float(row[0])
                load = float(row[4]) * 8
                if key in self.network_data:
                    self.network_data[key]['time'].append(tme)
                    self.network_data[key]['load'].append(load)
                else:
                    self.network_data[key] = {}
                    self.network_data[key]['time'] = []
                    self.network_data[key]['load'] = []

    def plot(self):
        info('*** Plot the DDoS Attack\n')
        self.interfaces = [t for t in self.interfaces if t in self.network_data]
        display_ddos_attack(self.network_data, (self.ast, self.aet), self.interfaces)

    def delete_log(self):
        if os.path.exists(self.log):
            os.remove(self.log)

    def terminate_network(self):
        try:
            self.terminate_ddos_attack()
            self.terminate_attack_track()
            self.delete_log()
            self.stop_net()
        except Exception as e:
            pass


def main():
    setLogLevel('info')
    option_1 = '--flood'
    option_2 = "--udp"
    simul_network = EmulationNetwork(option_1, option_2)
    try:
        simul_network.execute()
    except KeyboardInterrupt:
        simul_network.terminate_network()


if __name__ == '__main__':
    main()