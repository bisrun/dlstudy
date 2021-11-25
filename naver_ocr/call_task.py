from nvconfig import nvconfig
from nvlogger import Logger
import common
import json
import os
import cv2
import requests
import uuid
import time
import re

class TaskItem:
    def __init__(self):
        self.task_name = ""
        self.task_effect = "" #good, bad
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
        self.ocr_unit_separater = "  "
        self.ocr_group_separater = " || "
        self.task_name_template = re.compile(r"\[CT-([-_\.0-9a-zA-Z]*).jpg\]:(\w+):(\d+)s")


    def request_ocr(self, image_file_path):
        api_url = 'https://404f4f52beec4fe69742aba3806550c5.apigw.ntruss.com/custom/v1/11090/734a5dcc37d25a4730bd2c632648e3d484d2343b6a2eff161746eb6322792c22/general'
        secret_key = 'Wm92R09kR1NHSXFvSnhlTFVFSVZvQnd3c3NUUHRhaVE='

        request_json = {
            'images': [
                {
                    'format': 'jpg',
                    'name': 'demo'
                }
            ],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': round(time.time() * 1000)
        }
        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        files = [
            ('file', open(image_file_path, 'rb'))
        ]
        headers = {
            'X-OCR-SECRET': secret_key
        }
        response = requests.request("POST", api_url, headers=headers, data=payload, files=files)
        res = json.loads(response.text.encode('utf8'))
        return res

    def save_ocr_json_from_image(self, image_file_path_pattern, json_dir_path):
        image_file_path_list = common.getFileList(image_file_path_pattern)
        ocr_convert_count = 0
        ocr_convert_success_count = 0

        for image_file_path in image_file_path_list:
            # image_file_path = os.path.join(image_dir, image_file_path)
            image_file_name = os.path.basename(image_file_path)
            #json_file_name = image_file_name.replace('.jpg', '.json')

            #json file폴더구조를 image file 과 동일한 폴더구조를 가지도록 한다.
            json_file_path = image_file_path.replace(self.config._IMAGE_DIR_PATH, self.config._JSON_DIR_PATH)
            #json_file_path = os.path.join(json_dir_path, json_file_name)
            json_file_path = json_file_path.replace('.jpg', '.json')
            json_temp_dir = os.path.dirname( json_file_path)
            if os.path.exists(json_temp_dir) == False :
                common.makedirs(json_temp_dir)


            is_request_succeed = True
            # image로 부터 ocr 정보를 추출한다.

            try:
                ocr_json = self.request_ocr(image_file_path)
            except:
                self._logger.error('exception error: {}'.format(image_file_name))
                is_request_succeed = False

            if is_request_succeed:
                ocr_convert_success_count += 1
                with open(json_file_path, 'w', encoding='utf-8') as outfile:
                    json.dump(ocr_json, outfile, indent=4, ensure_ascii=False)
                    self._logger.info("image proc:{}".format(image_file_name))

            ocr_convert_count += 1

            if ocr_convert_count > 10:
                break;

            time.sleep(1)
        return ocr_convert_success_count

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


    #1개 json or image 파일에 대해, line 분
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

        #마지막 라인을 여기서 담는다.
        if len(line_item_list) > 0:
            line_item_list = sorted(line_item_list, key=lambda k: k['boundingPoly']['vertices'][0]['x'], reverse=False)
            full_line_item_list.append(line_item_list)

        return full_line_item_list


    def parse_json_files(self,json_file_path_pattern):
        json_file_path_list = common.getFileList(json_file_path_pattern)
        #json_file_path_list = sorted(json_file_path_list, key=lambda k: k, reverse=False)
        json_file_path_list.sort()
        ocr_convert_count = 0
        ocr_convert_success_count = 0

        for file_cnt, json_file_path in enumerate(json_file_path_list):
            json_fp = open(json_file_path, mode="r", encoding='utf-8')
            ob_ocr_json = json.load(json_fp)

            ocr_data_list = ob_ocr_json['images']
            ocr_data_list = ocr_data_list[0]['fields']

            ocr_data_list = sorted(ocr_data_list, key=lambda k: k['boundingPoly']['vertices'][0]['y'], reverse=False)
            print(len(ocr_data_list))
            lines = self.get_separate_line(ocr_data_list)
            self._logger.info("file : {}".format(json_file_path))

            task_line = 0
            task_count = 0
            new_task = False
            for i, line in enumerate(lines):
                #self._logger.info(i, line)
                line_string =[]

                #하나의 라인을 그룹핑한다.
                for l, ln in enumerate(line):
                    task_attr = ln['inferText']

                    # task 이름이 있는 곳이 , task 정보의 시작이다.
                    if task_attr.find("[CT-2021") == 0:
                        task_item = TaskItem()

                        if task_attr.find("--") >= 0:
                            #self._logger.debug("{} {}".format(task_attr, task_attr.find("--")) )
                            task_attr = task_attr.replace("--","-") # ocr 오류로 인해 '-' 을 '--' 로 오인식하는 경우가 있다.
                        task_line = 0
                        task_count += 1
                        ru = self.task_name_template.findall(task_attr)
                        task_item.task_name = ru[0][0]
                        task_item.task_effect = ru[0][1]
                        task_item.task_cost = ru[0][2]

                    ret, task_attr_conv = self.task_attr_filter(task_attr, task_line )
                    if ret == -1: #사용하지 않는 속성
                        continue;
                    elif ret == 1:
                        task_attr = task_attr_conv
                    #else
                    #   task_attr 그대로 사용한다.


                    #같은 행에서 , 문장분리 - 문장과 문장이 100px넘으면 분리한다.
                    if l > 0 : #task 이름 다음 행부터 분석
                        if ln['boundingPoly']['vertices'][0]['x'] - last_attr['boundingPoly']['vertices'][1]['x'] > 100 :
                            line_string.append(self.ocr_group_separater)
                        #print(ln['boundingPoly']['vertices'][0]['x'] - last_attr['boundingPoly']['vertices'][1]['x'] )

                    last_attr = ln

                    line_string.append(task_attr)
                    line_string.append(self.ocr_unit_separater)

                if len(line_string) > 0 :
                    self._logger.info("f:{},t:{},r:{} >> {}".format(file_cnt, task_count, task_line, ''.join(line_string)))
                    task_line += 1

    #ret 0: 그냥사용한다. -1: 사용하지 않는다, 1:값이 변경되었다. replace해야한다.
    def task_attr_filter(self, task_attr, task_line):
        # 의미없는 문는 제거한다.
        if task_attr == ">":
            return -1, None
        elif task_attr == ")":
            return -1, None
        return 0, None