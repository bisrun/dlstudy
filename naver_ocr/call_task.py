from nvconfig import nvconfig
from nvlogger import Logger
import common
import json
import os
import cv2

class task_item:
    def __init__(self):
        self.task_name = ""
        self.task_cost = 0
        self.addr_from = ""
        self.addr_to = ""
        self.reg_time = ""
        self.description = ""
        self.upload_date = "" #당상, 내상
        self.download_date = "" # 당착, 내착
        self.fare_total = 0
        self.fare_delivery = 0
        self.fare_add = 0
        self.car_attr = ""  # 1톤/카
        self.carload_type = "" #독차, 혼차
        self.recv_money_type = "" #인수증, 선/착불 ..



class call_task:
    def __init__(self):
        logManager = Logger.instance()
        self._logger = logManager.getLogger()
        self.config = nvconfig.instance()

    def compare_the_axis_y(self, prior_item, cur_item):
        # print('prior_item : ', prior_item, 'cur_item : ', cur_item)
        thesh_hold = 5

        prior_row_y1 = prior_item['boundingPoly']['vertices'][0]['y']
        prior_row_y2 = prior_item['boundingPoly']['vertices'][3]['y']
        prior_center = (prior_row_y1 + prior_row_y2) / 2
        cur_row_y1 = cur_item['boundingPoly']['vertices'][0]['y']
        cur_row_y2 = cur_item['boundingPoly']['vertices'][3]['y']
        cur_center = (cur_row_y1 + cur_row_y2) / 2

        center_diff = abs(prior_center - cur_center)

        if center_diff <= thesh_hold:
            return True
        else:
            return False


    def get_separate_line(self, ocr_data_list):

        full_line_item_list = []
        line_item_list = []
        index = 0

        for cur_item in ocr_data_list:
            if not cur_item.get('inferText'):
                self._logger.info('문제 있음')
                continue

            if index == 0:
                line_item_list.append(cur_item)
            else:
                prior_item = ocr_data_list[index - 1]
                is_same_line = self.compare_the_axis_y(prior_item, cur_item)

                if is_same_line: # 같은 라인이면
                    line_item_list.append(cur_item)
                else: #다른 라인이면, 기존의 라인을 full_line 에 입력하고, line_item_list를 새로 할당한다.
                    line_item_list  = sorted(line_item_list, key=lambda k: k['boundingPoly']['vertices'][0]['x'], reverse=False)
                    full_line_item_list.append(line_item_list)
                    line_item_list = []
                    line_item_list.append(cur_item)
            index = index + 1

        return full_line_item_list

    def parse_json_files(self,json_file_path_pattern):
        json_file_path_list = common.getFileList(json_file_path_pattern)
        ocr_convert_count = 0
        ocr_convert_success_count = 0

        for json_file_path in json_file_path_list:
            json_fp = open(json_file_path, mode="r", encoding='utf-8')
            ob_ocr_json = json.load(json_fp)

            ocr_data_list = ob_ocr_json['images']
            ocr_data_list = ocr_data_list[0]['fields']

            ocr_data_list = sorted(ocr_data_list, key=lambda k: k['boundingPoly']['vertices'][0]['y'], reverse=False)
            print(len(ocr_data_list))
            lines = self.get_separate_line(ocr_data_list)
            self._logger.info("file : {}".format(json_file_path))

            task_line = 0
            new_task = False
            for i, line in enumerate(lines):
                #self._logger.info(i, line)
                line_string =[]

                #하나의 라인을 그룹핑한다.
                for l, ln in enumerate(line):
                    task_attr = ln['inferText']
                    if task_attr.find("[CT-2021") == 0:
                        new_task = True
                        task_line = 0
                    if task_attr == ">":
                        continue

                    if l > 0 :
                        if ln['boundingPoly']['vertices'][0]['x'] - last_attr['boundingPoly']['vertices'][1]['x'] > 100 :
                            line_string.append(" ++ ")
                        #print(ln['boundingPoly']['vertices'][0]['x'] - last_attr['boundingPoly']['vertices'][1]['x'] )

                    last_attr = ln

                    line_string.append(task_attr)
                    line_string.append(" || ")

                if len(line_string) > 0 :
                    self._logger.info("{} - {}: {}".format(i, task_line, ''.join(line_string)))
                    task_line += 1
