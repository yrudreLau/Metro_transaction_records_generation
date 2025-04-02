class Network:

    def __init__(self, afc_date='2021-06-01', data_dir='./data'):
        self._afc_date = afc_date 
        self._station_path = os.path.join(data_dir, 'station.csv')  
        self._section_path = os.path.join(data_dir, 'sections.csv')  
        self._time_table_path = os.path.join(data_dir, 'timetable') 
        self.save_flag = False  
        """
        self._line_nets = line_nets  
        self._acc_station_id_name_dict = acc_station_id_name_dict 
        self._acc_station_name_id_dict = acc_station_name_id_dict 
        self._station_id_name_dict = station_id_name_dict 
        self._stations = stations  
        self._section_info = section_info 
        self._time_table_lists = time_table_lists 
        """
        self._read_stations_sections()
        self._read_time_table()


    def _read_stations_sections(self):
        """
        :return:  None
        """
        station_columns = ["STATION_ID",  
                           "STATION_NAME",  
                           "LINE_ID",  
                           "ACC_STATION_ID",  
                           "START_TERMINAL_STATION_IND", 
                           "TRANSFER_FLAG",  
                           "XFER_STATION_ID",  
                           "STATION_STATUS_CD", 
                           "LONGITUDE",  
                           "LATITUDE", 
                           "ACC_LINE_ID",  
                           "ID_INLINE"  
                           ]

        section_columns = ["SECTION_ID",  
                           "LINE_ID", 
                           "TRIP_DRCT_CD", 
                           # "SECTION_RUN_DISTANCE",
                           "SECTION_START_STATION_ID",
                           "SECTION_END_STATION_ID", 
                           ]

        station_info = pd.read_csv(self._station_path, usecols=station_columns) 
        station_info = station_info[station_info["STATION_STATUS_CD"] == 10]
        station_info = station_info[station_info["LINE_ID"] != '00']  
        # print(station_info)
        station_info['LINE_ID'] = station_info['LINE_ID'].astype(str)
        station_info['ACC_STATION_ID'] = station_info['ACC_STATION_ID'].astype(str)
        acc_station_id_name_dict = dict(
            zip(station_info['ACC_STATION_ID'], station_info['STATION_NAME'])) 
        acc_station_name_id_dict = dict(
            zip(station_info['STATION_NAME'], station_info['ACC_STATION_ID']))  
        station_id_name_dict = dict(zip(station_info['STATION_ID'], station_info['STATION_NAME'])) 

        section_info = pd.read_csv(self._section_path, usecols=section_columns) 
        # print('station_info:', station_info.info())
        # print('section_info:', section_info)
        # print('station_id_name_dict:', station_id_name_dict)
        section_info['SECTION_START_STATION_NAME'] = section_info['SECTION_START_STATION_ID'].apply(
            lambda x: station_id_name_dict[x])
        section_info['SECTION_END_STATION_NAME'] = section_info['SECTION_END_STATION_ID'].apply(
            lambda x: station_id_name_dict[x])

        line_ids = list(set(station_info['LINE_ID']))
        line_ids.sort()
        # print(line_ids)  # ['01', '02', '03', '04', '10', 'S1', 'S3', 'S7', 'S8', 'S9']
        line_nets = {}
        for key in line_ids:
            line_nets[key] = {'station': []}

      
        stations = {}
        for acc_id, name in acc_station_id_name_dict.items():
            station = {'name': name, 'transfer': False,
                       'line_id': [],  
                       'station_id': [], 
                       'id_inline': [],  
                       'next_transfer_stations': [], 
                       'next_transfer_lines': []  
                       }
            stations[acc_id] = station

        for index, row in station_info.iterrows():
           
            acc_id = row['ACC_STATION_ID']
            line_id = row['LINE_ID']
            station_id = row['STATION_ID']
            id_inline = row['ID_INLINE']
            station = stations[acc_id]
            name = station['name']
            transfer = False
            if row['TRANSFER_FLAG'] == 1:
                transfer = True
            station['line_id'].append(line_id)
            station['station_id'].append(station_id)
            station['id_inline'].append(id_inline)
            station['transfer'] = transfer
            # station['next_transfer_stations'].append(row['LINE_ID'])
            # station['next_transfer_lines'].append(row['LINE_ID'])
            stations[acc_id] = station
            line_station = {'acc_id': acc_id, 'name': name, 'line_id': line_id,
                            'station_id': station_id, 'id_inline': id_inline, 'transfer': transfer}
            line_nets[line_id]['station'].append(line_station)

        for line in line_nets.keys():
            line_nets[line]['station'].sort(key=lambda obj: obj.get('id_inline'), reverse=False)

        for acc_id in stations.keys():
            for line in stations[acc_id]['line_id']:
                for line_station in line_nets[line]['station']:
                    if line_station['transfer'] and line_station['acc_id'] != acc_id:
                        # if line_station['acc_id'] not in stations[acc_id]['next_transfer_stations']:
                        stations[acc_id]['next_transfer_stations'].append(line_station['acc_id'])
                        stations[acc_id]['next_transfer_lines'].append(line)

        self._line_nets = line_nets  
        self._acc_station_id_name_dict = acc_station_id_name_dict 
        self._acc_station_name_id_dict = acc_station_name_id_dict 
        self._station_id_name_dict = station_id_name_dict  
        self._stations = stations  
        self._section_info = section_info  

        if self.save_flag:
            df = pd.DataFrame.from_dict(stations, orient='index')
            df.to_csv('data/output/stations.csv', encoding='GB2312')

    def _read_time_table(self, mode=1):
        """
        :param mode:  train timetable loading mode
        :return: None
        """
        
        time_table_csv_lists = []
        time_table_lists = {}

        for root, dirs, files in os.walk(self._time_table_path):
            for file in files:
                file_extension = os.path.splitext(file)[1] 
                if file_extension == '.csv':
                    time_table_csv_lists.append(file)                    
        time_format_str = '%Y-%m-%d %H:%M:%S'
        split_str = self._afc_date + ' 03:00:00' 
        split_datetime = datetime.datetime.strptime(split_str, time_format_str) 
        try:

            for file in time_table_csv_lists:
                file_path = os.path.join(self._time_table_path, file)  
                file_name = os.path.splitext(file)[0]  

                df = pd.read_csv(file_path, encoding='GB2312', index_col=0)

                if mode == 1:  
                    df.fillna('03:00:00', inplace=True)
                    for col in df.columns:
                        # print(col)
                        df[col] = df[col].str.strip()
                    df = self._afc_date + ' ' + df
                    for time in df.columns:
                        df[time] = pd.to_datetime(df[time], format=time_format_str)
                    data_index = df < split_datetime
                    df[data_index] = df[data_index] + pd.Timedelta(days=1)
                    for time in df.columns:
                        data_index = df[time] == split_datetime
                        df.loc[data_index, time] = ''
                elif mode == 2:  
                    for station in df.index:
                        for time in df.columns:
                            if not pd.isna(df.loc[station, time]):  
                                # print(file, station, time)
                                df.loc[station, time] = self._afc_date + ' ' + df.loc[station, time]
                                df.loc[station, time] = pd.to_datetime(df.loc[station, time],
                                                                        format=time_format_str)

                                if df.loc[station, time] < split_datetime:
                                    df.loc[station, time] = df.loc[station, time] + pd.Timedelta(days=1)
                    df.fillna('', inplace=True)
                df.insert(0, 'station_name', '')
                df['station_name'] = df.index
                df.rename(index=self._acc_station_name_id_dict, inplace=True)
                time_table_lists[file_name] = df
                if self.save_flag:
                    new_file_path = os.path.join('data/output/timetable', file)
                    df.to_csv(new_file_path, encoding='GB2312')
        except ValueError as e:
            print('Problem emerged')
            print('loc：', file)
            if mode == 1:
                print('loc：', file)
            else:
                print('loc：', file, station, time)
            print('log info：', e)
            print('The values in the timetable cannot have extra spaces')
            traceback.print_exc()

        except Exception as e:
            print('Problem emerged')
            print('log info：', e)
            print('error info: ', file, col)
            traceback.print_exc()
        finally:
            self._time_table_lists = time_table_lists 
   
    def get_stations_id_list(self):
        return [k for k,v in self._stations.items()]

    def get_acc_id2name_dict(self):
        return self._acc_station_id_name_dict

    def acc_id2name(self, acc_id):
        return self._acc_station_id_name_dict[acc_id]

    def name2acc_id(self, name):
        return self._acc_station_name_id_dict[name]

    def acc_id_list2name(self, acc_id_list):
        name_list = []
        for acc_id in acc_id_list:
            name_list.append(self._acc_station_id_name_dict[acc_id])
        return name_list

    def name_list2acc_id(self, name_list):
        acc_id_list = []
        for name in name_list:
            acc_id_list.append(self._acc_station_name_id_dict[name])
        return acc_id_list

    def get_near_transfer_info(self, acc_id):
        return self._stations[acc_id]['next_transfer_stations'], self._stations[acc_id]['next_transfer_lines']

    def is_in_same_line(self, acc_id1, acc_id2):
        """
        :param acc_id1: first station's acc_id
        :param acc_id2: second station's acc_id
        :return: Bool
        """
        lines1 = self._stations[acc_id1]['line_id']
        lines2 = self._stations[acc_id2]['line_id']
        common_line = [x for x in lines1 if x in lines2]
        if len(common_line) > 0:
            return True
        return False

    def get_common_line(self, acc_id1, acc_id2):
        """
        :param acc_id1: first station's acc_id
        :param acc_id2: second station's acc_id
        :return: common_line index
        """

        lines1 = self._stations[acc_id1]['line_id']
        # print('###lines1### :', lines1)
        lines2 = self._stations[acc_id2]['line_id']
        # print('###lines2### :', lines2)
        common_line = [x for x in lines1 if x in lines2]
        return common_line


    def get_stations_between_2stations_in_line(self, acc_id1, acc_id2, line_id):
        """
        :param acc_id1:  origin acc_id
        :param acc_id2:  destination acc_id
        :param line_id: line index
        :return: stations
        """
        stations = []
        common_line = self.get_common_line(acc_id1, acc_id2)
        if line_id in common_line:
            index1 = self._stations[acc_id1]['line_id'].index(line_id) 
            index2 = self._stations[acc_id2]['line_id'].index(line_id)
            id1_inline = self._stations[acc_id1]['id_inline'][index1] 
            id2_inline = self._stations[acc_id2]['id_inline'][index2]
            min_id_inline = min(id1_inline, id2_inline)
            max_id_inline = max(id1_inline, id2_inline)
            flag = False 
            for station in self._line_nets[line_id]['station']:
                id_inline = station['id_inline']
                if flag:
                    stations.append(station['acc_id'])
                    if id_inline == max_id_inline:
                        break
                elif id_inline == min_id_inline:
                    flag = True
                    stations.append(station['acc_id'])

            if stations and stations[0] != acc_id1:
                stations.reverse()
            if stations:
                stations.pop()
        else:
            pass
        return stations

    def get_time_arrive_station(self, acc_id1, acc_id2, line_id, start_time):
        """
        :param acc_id1: origin acc_id
        :param acc_id2: destination acc_id
        :param line_id: line index
        :param start_time:  passenger's arrival time at origin platform
        :return: passenger's arrival time at destination platform
        """
        # print(line_id, acc_id1, acc_id2)
        index1 = self._stations[acc_id1]['line_id'].index(line_id)
        id1_inline = self._stations[acc_id1]['id_inline'][index1] 
        index2 = self._stations[acc_id2]['line_id'].index(line_id) 
        id2_inline = self._stations[acc_id2]['id_inline'][index2]

        time_table_key = 'line_' + line_id  # 例 line_01_down_arrive 或 line_01_down_start
        # print(id1_inline, id2_inline)
        if id1_inline > id2_inline:  # down
            time_table_key += '_down'
        else:  # up
            time_table_key += '_up'

        
        train_number = '-' 
        # if line_id == '07':
        #     if acc_id1 in line_07_south_acc:
        #         df_start = self._time_table_lists[time_table_key2 + '_departure']
        #         df_arrive = self._time_table_lists[time_table_key2 + '_arrival']
        #     else:
        #         df_start = self._time_table_lists[time_table_key1 + '_departure']
        #         df_arrive = self._time_table_lists[time_table_key1 + '_arrival']
        # else:
        df_start = self._time_table_lists[time_table_key + '_departure']
        df_arrive = self._time_table_lists[time_table_key + '_arrival']

        for col in df_start.columns[1:].tolist():
            # print(line_id)
            # print(df_start[df_start.columns[0]])
            # print(self.acc_id2name(acc_id1), self.acc_id2name(acc_id2))
            # print(acc_id1, acc_id2)
            # print(df_start.loc[acc_id1, col], df_start.loc[acc_id2, col],\
            #       isinstance(df_start.loc[acc_id1, col], datetime.date), \
            #       isinstance(df_start.loc[acc_id2, col], datetime.date))

            if isinstance(df_start.loc[acc_id1, col], datetime.date) \
                    and isinstance(df_start.loc[acc_id2, col], datetime.date):

                if start_time < df_start.loc[acc_id1, col]: # and df_arrive.loc[acc_id2, col] < end_time:  # 到站时间小于开车即可  and df_arrive.loc[acc_id2, col] < end_time , end_time
                    train_number = col
                    break
  
        if train_number == '-':

            return None, None, None
        else:
            arrive_time = df_arrive.loc[acc_id2, train_number]
            departure_time = df_start.loc[acc_id1, train_number]

            if isinstance(arrive_time, datetime.date) & isinstance(departure_time, datetime.date):
                return departure_time, arrive_time, train_number
            else:
                print(' --', time_table_key, self.acc_id2name(acc_id2), acc_id2, train_number, '未找到对应的下车时间')
                return None, None, None
