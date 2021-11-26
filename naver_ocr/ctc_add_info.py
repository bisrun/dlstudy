from nvconfig import nvconfig
from nvlogger import Logger
import common
import json
import os

import requests
import re
from call_task import TaskItem, call_task

class add_coord_by_addr():
    def __init__(self, task_list):
        self._logger = Logger.instance().getLogger()
        self.task_list = task_list
        self.config = nvconfig.instance()

    def parse_data(self, data_json):
        tmp_data_json = json.loads(data_json)

        poi_str = ''
        lcode_nm = ''
        epoi_x = ''
        epoi_y = ''
        poi_x = ''
        poi_y = ''

        if tmp_data_json['ItemCnt'] == '1':
            item = tmp_data_json['Item'][0]
            poi_str = item['PoiStr']
            lcode_nm = item['LCodeNm']
            epoi_x = item['EPoiX']
            epoi_y = item['EPoiY']
            poi_x = item['PoiX']
            poi_y = item['PoiY']

        return poi_str, lcode_nm, epoi_x, epoi_y, poi_x, poi_y


    def get_coordinate(self, loc):
        url = 'http://searchtest.atlan.co.kr/geocode.jsp'
        params = {'SchString': loc, 'SchType' : 20, 'ResPerPage': 1, 'IsTest': '1'}
        res = requests.get(url, params=params, timeout=10, headers={'Connection':'close'})
        if res.status_code == 200:
            return res.text
        else:
            return None

    def add_coord_attr(self):
        for i, task_item in enumerate(self.task_list):
            from_json = self.get_coordinate(task_item.addr_from)
            if from_json is not None:
                poi_str, lcode_nm, epoi_x, epoi_y, poi_x, poi_y = self.parse_data(from_json)
                task_item.pos_from_x = epoi_x
                task_item.pos_from_y = epoi_y

            to_json = self.get_coordinate(task_item.addr_to)
            if to_json is not None:
                poi_str, lcode_nm, epoi_x, epoi_y, poi_x, poi_y  = self.parse_data(to_json)
                task_item.pos_to_x = epoi_x
                task_item.pos_to_y = epoi_y

            self._logger.info("{}) {} {},{}, {},{}".format(i, task_item.task_name, task_item.pos_from_x, task_item.pos_from_y, task_item.pos_to_x, task_item.pos_to_y))
            #if i >10:
            #    break

    def write_ctc_info(self):
        ctc_info_fd = open(self.config._CTC_INFO_02_FILE_PATH, 'w')
        TaskItem.write_task_header(ctc_info_fd)
        for task in self.task_list:
            task.write_task_to_file(ctc_info_fd)

        ctc_info_fd.close()



class add_route_info():
    def __init__(self, task_list):
        self._logger = Logger.instance().getLogger()
        self.task_list = task_list
        self.config = nvconfig.instance()

    def add_route_result(self):
        for i, task_item in enumerate(self.task_list):
            if i == 0 :
                continue
            if  task_item.pos_from_x == None or task_item.pos_to_x == None or task_item.pos_from_x == '' or task_item.pos_to_x == '':
                continue

            task_item.distance , task_item.eta = self.get_route_result(task_item.pos_from_x, task_item.pos_from_y, task_item.pos_to_x, task_item.pos_to_y, None)
            if task_item.distance == None:
                self._logger.error("error  {} {} :[{}] --> [{}]".format(i, task_item.task_name, task_item.addr_from, task_item.addr_to))
            self._logger.info("{}) {} {},{}".format(i, task_item.task_name,task_item.distance,  task_item.eta))
            #if i >10:
            #    break

    def get_route_result(self, sx: float, sy: float, ex: float, ey: float, opt: dict):
        query = ("http://apis.atlan.co.kr/maps/searchRoute.json?"
                 "rpType=5&coordType=0&rpOpt=1&carType=0&carType2=1&authKey=1385472743fb2b42e80da1e85ab4e721ecf55520d5&privateKey=&version=&"
                 "origPosX={0}&origPosY={1}&destPosX={2}&destPosY={3}"
                 "&viaCnt=0&trafficOpt=0&dirAngle=-1&carSpeed=0"
                 ).format(sx, sy, ex, ey)

        #print(query)
        res = requests.get(query)

        if res.status_code != 200:
            return None, None

        try:
            response = res.json()
            rpresults = response['rpresults']
            items = rpresults['items']
            item = items[0]

            distance = item['distance']
            time = item['time']

            return int(distance), int(time)

        except Exception as e:
            self._logger.error("error route 10:{} , ({}, {}) ({}, {})".format(e,  sx, sy, ex, ey))
            return None, None


    def write_ctc_info(self):
        ctc_info_fd = open(self.config._CTC_INFO_03_FILE_PATH, 'w')
        TaskItem.write_task_header(ctc_info_fd)
        for task in self.task_list:
            task.write_task_to_file(ctc_info_fd)

        ctc_info_fd.close()
