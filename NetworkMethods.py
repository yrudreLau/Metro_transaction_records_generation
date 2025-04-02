# -*- coding: utf-8 -*-

from collections import deque
import datetime
import pandas as pd
import numpy as np

from NetworkMethod import Network

class NetworkMethods:
    def __init__(self, afc_date='2022-06-01', data_dir='./data'):
        self.networks = Network(afc_date, data_dir)  # Network 
    
    
    def find_existed_path(self, ori_acc_id, des_acc_id, xfer_num, only_common_line=True):
        """
        MAX_TRANSFER_COUNT = 3
        :param ori_acc_id: origin acc_id
        :param des_acc_id: destination acc_id
        :return: key_station_paths 
        """
        key_station_paths = []
        line_in_paths = []

        common_line = self.networks.get_common_line(ori_acc_id, des_acc_id)
        if common_line:  
            # multipaths condition
            for line in common_line:
                key_station_paths.append([ori_acc_id, des_acc_id])
                line_in_paths.append([line])
            if only_common_line: return key_station_paths, line_in_paths
        
        # Breadth Fisrt Search
        MAX_TRANSFER_COUNT = xfer_num
        transfer_count = 0
        queue = deque() 
        queue.append(ori_acc_id)
        path_record = deque()
        path_record.append([ori_acc_id])
        line_record = deque()
        line_record.append([])
        while queue:
            transfer_count += 1
            # print('transfer_count: ', transfer_count)
            if transfer_count > MAX_TRANSFER_COUNT:  
                break
            else:
                for _ in range(len(queue)): 
                    # get key node
                    cur_id = queue.popleft()
                    cur_path = path_record.popleft()
                    cur_line = line_record.popleft()
                   
                    next_transfer_stations, next_lines = self.networks.get_near_transfer_info(cur_id)
                    # print('cur: {}, path:{}, line:{}, next: {}'.
                    #     format(cur_id, cur_path, cur_line, next_transfer_stations))
                    for (next_station, line) in zip(next_transfer_stations, next_lines):
                        if next_station == des_acc_id: continue
                        if line not in cur_line: 
                            # print(next_station, des_acc_id)
                            common_line = self.networks.get_common_line(next_station, des_acc_id)
                            if common_line:
                                # common_line 
                                for c_line in common_line:
                                    if line == c_line: continue
                                    # 储存路径关键点
                                    _cur_path = cur_path.copy()
                                    _cur_path.append(next_station)
                                    _cur_path.append(des_acc_id)
                                    key_station_paths.append(_cur_path.copy())
                                    # 储存经过的线路
                                    _cur_line = cur_line.copy()
                                    _cur_line.append(line)
                                    _cur_line.append(c_line)
                                    # print('save, path:{}, line:{}'.format(_cur_path, _cur_line))
                                    line_in_paths.append(_cur_line.copy())
                            elif next_station not in cur_path:
                                queue.append(next_station)
                                # update key node
                                _cur_path = cur_path.copy()
                                _cur_path.append(next_station)
                                path_record.append(_cur_path)
                                # update line records
                                _cur_line = cur_line.copy()
                                _cur_line.append(line)
                                line_record.append(_cur_line)
        return key_station_paths, line_in_paths

    def key_station_with_line_toStr(self, key_station_paths, line_in_paths, model='name'):
        """
        :param key_station_paths: list consists of key station acc_ids
        :param line_in_paths: line ids corresponding to the feasible path
        :param model: 
        :return: None
        """
        str_list = []
        if model == 'name':
            for (paths, lines) in zip(key_station_paths, line_in_paths):
                path_str = ''
                for i, line in enumerate(lines):
                    path_str += self.networks.acc_id2name(paths[i]) + ' -> '
                    path_str += line + ' -> '
                path_str += self.networks.acc_id2name(paths[-1])
                str_list.append(path_str)
        elif model == 'id':
            for (paths, lines) in zip(key_station_paths, line_in_paths):
                path_str = ''
                for i, line in enumerate(lines):
                    path_str += paths[i] + ' -> '
                    path_str += line + ' -> '
                path_str += paths[-1]
                str_list.append(path_str)

        return str_list

    def print_key_station_with_line(self, key_station_paths, line_in_paths, start_str=None):
        """
        :param key_station_paths: list consists of key station acc_ids
        :param line_in_paths: line ids corresponding to the feasible path
        :param start_str: str default value: None
        :return: None
        """
        print('check：{} check: {}'.format(key_station_paths, line_in_paths))
        if start_str:
            print(start_str, end = ' ')
        for i, line in enumerate(line_in_paths):
            print(self.networks.acc_id2name(key_station_paths[i]), end=' -> ')
            print(line, end=' -> ')
        print(self.networks.acc_id2name(key_station_paths[-1]))

    def get_full_path(self, key_station_paths, line_in_paths):
        """
        :param key_station_paths: list consists of key station acc_ids
        :param line_in_paths: line ids corresponding to the feasible path
        :return: full_paths: list of full nodes of the paths
        """
        full_paths = []
        for (paths, lines) in zip(key_station_paths, line_in_paths):
            one_full_path = []  
            for i, line in enumerate(lines):
                one_full_path.extend(self.networks.get_stations_between_2stations_in_line(paths[i], paths[i + 1], line))
                
            one_full_path.append(paths[-1])
            full_paths.append(one_full_path)
        return full_paths

    def find_effective_path(self, key_station_paths, line_in_paths): # unused
        """
        get feasible paths
        i.e.: n(path) < MAX_STATION_COUNT_DIFF + shortest_path_count
        :param key_station_paths: ***
        :param line_in_paths: ***
        :return: filtered key_station_paths line_in_paths
        """
        new_key_station_paths = []
        new_line_in_paths = []
        if len(key_station_paths) <= 1:
            return key_station_paths, line_in_paths
        else:
            full_paths = self.get_full_path(key_station_paths, line_in_paths)
            shortest_path_index = self.get_index_shortest_path(full_paths)
            shortest_path_count = len(full_paths[shortest_path_index])
            MAX_STATION_COUNT_DIFF = 5
            max_station_count = MAX_STATION_COUNT_DIFF + shortest_path_count
            effective_index_list = []  
            for index, full_path in enumerate(full_paths):
                if len(full_path) < max_station_count:
                    effective_index_list.append((index))
                    new_key_station_paths.append(key_station_paths[index].copy())
                    new_line_in_paths.append(line_in_paths[index].copy())

            return new_key_station_paths, new_line_in_paths

    def find_shortest_path(self, key_station_paths, line_in_paths):
        """
        get shortest path
        :param key_station_paths: ***
        :param line_in_paths: ***
        :return: ***
        """
        new_key_station_paths = []
        new_line_in_paths = []
        if len(key_station_paths) <= 1:
            return key_station_paths, line_in_paths
        else:
            full_paths = self.get_full_path(key_station_paths, line_in_paths)
            shortest_path_index = self.get_index_shortest_path(full_paths)
            new_key_station_paths.append(key_station_paths[shortest_path_index].copy())
            new_line_in_paths.append(line_in_paths[shortest_path_index].copy())

            return new_key_station_paths, new_line_in_paths
    
    def get_index_shortest_path(self, full_paths):
        """
        get shortest path's index
        if exist more than one shortest path, return the first one's index
        :param full_paths: ***
        :return: index of the shortest path
        """
        station_count = 9999  
        index = -1
        for i in range(len(full_paths)):
            if station_count > len(full_paths[i]):
                station_count = len(full_paths[i])
                index = i
        return index
