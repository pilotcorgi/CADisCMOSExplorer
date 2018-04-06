#!/usr/bin/env python3

from Circuit.Transistor import *
import itertools


class Node:
    def __init__(self, name):
        self.name_ = name
        self.terminals = set()

    def __repr__(self):
        ret = f'<{self.__class__.__name__}>'+self.name_ + "\n"
        for terminal in self.terminals:
            ret += "\t" + repr(terminal) + "\n"
        return ret

    def __str__(self):
        return self.get_name()

    def set_name(self, name):
        self.name_ = name

    def get_name(self):
        return self.name_

    def remove_terminal(self, terminal):
        if terminal in self.terminals:
            self.terminals.remove(terminal)

    def add_terminal(self, terminal):
        self.terminals.add(terminal)


class Netlist:
    def __init__(self):
        self.p_transistors_ = list()
        self.n_transistors_ = list()
        self.node_dicts_ = dict()
        self.node_dicts_['in'] = dict()
        self.node_dicts_['out'] = dict()
        self.node_dicts_['internal'] = dict()
        self.node_dicts_['supply'] = dict()

    def __str__(self):
        ret = ''
        for tx in self.n_transistors_:
            ret += str(tx)
        for tx in self.p_transistors_:
            ret += str(tx)
        return ret

    def __repr__(self):
        """
        Basic assumption:
        Within one cell, the NMOS transistors always have smaller IDs compared to PMOS transistors
        :return:
        """
        ret = f'<{self.__class__.__name__}>'
        for tx in self.n_transistors_:
            ret += repr(tx)
        for tx in self.p_transistors_:
            ret += repr(tx)
        return ret

    @staticmethod
    def get_set_name_for_node(node_name):
        if node_name[0] == 'I':
            return 'in'
        elif node_name[0] == 'O':
            return 'out'
        elif node_name[0] == 'N':
            return 'internal'
        else:
            return 'supply'

    def get_node(self, name, node_dict):
        if name not in self.node_dicts_[node_dict]:
            self.node_dicts_[node_dict][name] = Node(name)
        return self.node_dicts_[node_dict][name]

    def reset_netlist(self):
        self.p_transistors_.clear()
        self.n_transistors_.clear()
        self.node_dicts_.clear()
        self.node_dicts_['in'] = dict()
        self.node_dicts_['out'] = dict()
        self.node_dicts_['internal'] = dict()
        self.node_dicts_['supply'] = dict()

    def set_netlist(self, str_netlist):
        self.reset_netlist()
        str_transistors = str_netlist.rstrip().split("\n")
        for str_transistor in str_transistors:
            items = str_transistor.rstrip().split(' ')
            temp_transistor = Transistor(items[0], items[5])
            if temp_transistor.t_type_ == 'PMOS':
                self.p_transistors_.append(temp_transistor)
            else:
                self.n_transistors_.append(temp_transistor)

            # In CADis data structure, index 0 is gate, 1 and 2 are diffusion
            # In SPICE data structure, index 1 is gate, 0 and 2 are diffusion
            items[1], items[2] = items[2], items[1]
            for i in range(1, 4):
                temp_node = self.get_node(items[i], self.get_set_name_for_node(items[i]))
                temp_transistor.get_terminal(i-1).set_node(temp_node)

    @staticmethod
    def update_names_for_obj(name_list, obj_list):
        for i in range(len(obj_list)):
            obj_list[i].set_name(name_list[i])

    def get_equ_netlists(self):
        """
        Generates all equivalent netlists
        :return: generator of netlist strings
        """
        p_transistor_names = [x.get_name() for x in self.p_transistors_]
        n_transistor_names = [x.get_name() for x in self.n_transistors_]
        in_nodes = [v for k, v in self.node_dicts_['in'].items()]
        out_nodes = [v for k, v in self.node_dicts_['out'].items()]
        internal_nodes = [v for k, v in self.node_dicts_['internal'].items()]
        in_names = [x.get_name() for x in in_nodes]
        out_names = [x.get_name() for x in out_nodes]
        internal_names = [x.get_name() for x in internal_nodes]

        for p_t_new_names in itertools.permutations(p_transistor_names):
            for n_t_new_names in itertools.permutations(n_transistor_names):
                for in_new_names in itertools.permutations(in_names):
                    for internal_new_names in itertools.permutations(internal_names):
                        for out_new_names in itertools.permutations(out_names):
                            self.update_names_for_obj(p_t_new_names, self.p_transistors_)
                            self.update_names_for_obj(n_t_new_names, self.n_transistors_)
                            self.update_names_for_obj(in_new_names, in_nodes)
                            self.update_names_for_obj(internal_new_names, internal_nodes)
                            self.update_names_for_obj(out_new_names, out_nodes)

                            transistors = self.n_transistors_ + self.p_transistors_
                            transistors.sort(key=lambda x: x.get_name())

                            for rev_diff in itertools.product([False, True], repeat=len(transistors)):
                                ret_netlist = ''
                                for i in range(len(transistors)):
                                    ret_netlist += transistors[i].get_description(rev_diff[i])
                                yield ret_netlist

        # restore netlist to original state
        self.update_names_for_obj(p_transistor_names, self.p_transistors_)
        self.update_names_for_obj(n_transistor_names, self.n_transistors_)
        self.update_names_for_obj(in_names, in_nodes)
        self.update_names_for_obj(internal_names, internal_nodes)
        self.update_names_for_obj(out_names, out_nodes)