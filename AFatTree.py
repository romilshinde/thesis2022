import math
from mininet.topo import Topo as NetworkTopology


class FatTree(NetworkTopology):
    def build(self, k=2):
        switches_dict = {i: self.addSwitch(f's{i}') for i in range(1, 5 * k + 1)}
        hosts_dict = {i: self.addHost(f'h{i}') for i in range(1, 4 * k + 1)}

        for i in range(1, 4 * k + 1):
            j = int(math.ceil(i / 2))
            self.addLink(hosts_dict[i], switches_dict[j])
        for i in range(1, 2 * k + 1):
            j = i + 4
            l = j + 1 if i % 2 == 1 else j - 1
            self.addLink(switches_dict[i], switches_dict[j])
            self.addLink(switches_dict[i], switches_dict[l])

        for i in range(2 * k + 1, 4 * k + 1):
            self.addLink(switches_dict[i], switches_dict[5 * k - 1])
            self.addLink(switches_dict[i], switches_dict[5 * k])


class FatTreeTopology(NetworkTopology):
    core_switches_list = []
    aggregation_switches_list = []
    edge_switches_list = []
    servers_list = []

    def __init__(self, k):
        NetworkTopology.__init__(self)
        self.no_of_pods = k
        self.no_of_core_swicthes = int((k / 2) ** 2)
        self.no_of_aggregation_swicthes = int(self.no_of_pods * k / 2)
        self.no_of_edge_switches = int(self.no_of_pods * k / 2)
        self.no_of_servers = int((k ** 3) / 4)
        print(self.no_of_core_swicthes, self.no_of_aggregation_swicthes, self.no_of_edge_switches, self.no_of_servers)

    def create_fat_tree_topology(self):
        self.create_core_layer_switches(self.no_of_core_swicthes)
        self.create_aggregation_layer_switches(self.no_of_aggregation_swicthes)
        self.create_edge_layer_switches(self.no_of_edge_switches)
        self.create_servers(self.no_of_servers)

    def _add_switch_to_layer(self, count, layer, switch_list):
        for x in range(1, count + 1):
            layer_name = layer
            '''layer_name = layer + "00"
            if x >= int(10):
                layer_name = str(layer) + "0"
                '''
            switch_list.append(self.addSwitch('s' + layer_name + str(x)))
        print(switch_list)

    def create_core_layer_switches(self, count):
        self._add_switch_to_layer(count, 'c', self.core_switches_list)

    def create_aggregation_layer_switches(self, count):
        self._add_switch_to_layer(count, "a", self.aggregation_switches_list)

    def create_edge_layer_switches(self, count):
        self._add_switch_to_layer(count, "e", self.edge_switches_list)

    def create_servers(self, count):
        for x in range(1, count + 1):
            layer_name = 'h'
            '''layer_name = "h00"
            if x >= int(10):
                layer_name = "h0"
            elif x >= int(100):
                layer_name = "h"
            '''
            self.servers_list.append(self.addHost(layer_name + str(x)))
        print(self.servers_list)

    def create_link_between_devices(self, bandwidth_core_to_aggregation=0.45, bandwidth_aggregation_to_edge=0.6,
                                    bandwidth_host_to_aggregation=0.8):
        end = int(self.no_of_pods / 2)
        for x in range(0, self.no_of_aggregation_swicthes, end):
            for i in range(0, end):
                for j in range(0, end):
                    self.addLink(self.core_switches_list[i * end + j], self.aggregation_switches_list[x + i],
                                 bw=bandwidth_core_to_aggregation)

        for x in range(0, self.no_of_aggregation_swicthes, end):
            for i in range(0, end):
                for j in range(0, end):
                    self.addLink(self.aggregation_switches_list[x + i], self.edge_switches_list[x + j],
                                 bw=bandwidth_aggregation_to_edge)

        tmp = 0
        for x in range(0, self.no_of_edge_switches):
            if x != 0:
                tmp = tmp + 2
            for i in range(0, 2):
                print(self.edge_switches_list[x], self.servers_list[tmp + i])
                self.addLink(self.edge_switches_list[x], self.servers_list[tmp + i], bw=bandwidth_host_to_aggregation)

    def set_ovs_protocol_13(self, ):
        self._set_ovs_protocol_13(self.core_switches_list)
        self._set_ovs_protocol_13(self.aggregation_switches_list)
        self._set_ovs_protocol_13(self.edge_switches_list)

    def _set_ovs_protocol_13(self, sw_list):
        for sw in sw_list:
            cmd = "sudo ovs-vsctl set bridge %s protocols=OpenFlow13" % sw
            os.system(cmd)