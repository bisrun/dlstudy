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

re_task_name_template = re.compile(r"\[CT-([-_\.0-9a-zA-Z]*).jpg\]:(\w+):(\d+)s")
re_dist_and_time = re.compile(r"(\d+Km).* (\d+:\d+)")
re_update = re.compile(r"([가-힣0-9a-zA-Z]+상)")
re_downdate = re.compile(r"([가-힣0-9a-zA-Z]+착)")
re_updowndate = re.compile(r"([가-힣0-9a-zA-Z]+상).* ([가-힣0-9a-zA-Z]+착)")
re_fare = re.compile(r'((-)?\d{1,3}(,\d{3})*(\.\d+)?)원')
re_truck_ton = re.compile(r'(\d+(\.\d{1,2})?)톤')

ocr_unit_separater = " "
ocr_group_separater = " || "



class TaskItem:
    def __init__(self):

        self._logger = Logger.instance().getLogger()
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
        self.car_limit_weight= 0.0
        self.fare_delivery = 0
        self.fare_add = 0
        self.car_attr = ""  # 1톤/카
        self.up_carry =""
        self.down_carry = ""
        self.carload_type = "" #독차, 혼차
        self.recv_money_type = "" #인수증, 선/착불 ..
        self.task_line_list = [] #image로부터 ocr을 통해 분석한 task line, 일반적으로 5개 라인으로 구성된다.
        self.task_line_parsing_func = {
                    0: self.task_line0_parsing,
                    1: self.task_line1_parsing,
                     2: self.task_line2_parsing,
                     3: self.task_line3_parsing,
                     4: self.task_line4_parsing,
                     5: self.task_line_invalid}

    # 출발지주소, 목적지 주소
    def task_line0_parsing(self, line):
        if line.find("--") >= 0:
            line = line.replace("--", "-")  # ocr 오류로 인해 '-' 을 '--' 로 오인식하는 경우가 있다.
        if line.find("_.") >= 0:
            line = line.replace("_.", "_")  # ocr 오류로 인해 '_' 을 '_.' 로 오인식하는 경우가 있다.
        if line.find(" ") >= 0:
            line = line.replace(" ", "")  # 첫번째 라인에는 띄어쓰기 없다.

        ru = re_task_name_template.findall(line)
        if ru is not None and len(ru) > 0 and len(ru[0]) >= 3:
            self.task_name = ru[0][0]
            self.task_effect = ru[0][1]
            self.task_cost = ru[0][2]
        else:
            self._logger.error("error: task name attr {}".format(line))

        return line
    def task_line1_parsing(self, line):
        addr = line.split(ocr_group_separater)
        if len(addr) == 2:
            self.addr_from = addr[0]
            self.addr_to = addr[1]
        return line

    def task_line2_parsing(self, line):
        # 당상  지 8Km   || 14:06 지  내착
        ru = re_dist_and_time.findall(line)
        if self.task_name.find("20211116-085425-00_02") >=0 :
            print(line)

        if ru is not None and len(ru) > 0 and len(ru[0]) == 2:
            self.reg_time = ru[0][1]
            line2 = re.sub(ru[0][0], "", line)
            line2 = re.sub(ru[0][1], "", line2)

            ru2 = re_update.findall(line2)
            if ru2 is not None and len(ru2) > 0 :
                self.upload_date = ru2[0]
                line2 = re.sub(ru2[0], "", line2)

            ru3 = re_downdate.findall(line2)
            if ru3 is not None and len(ru3) > 0 :
                self.download_date = ru3[0]
                line2 = re.sub(ru3[0], "", line2)

            lines = line2.split(ocr_group_separater)
            if len(lines) == 2:
                self.up_carry = lines[0]
                self.down_carry = lines[1]

        else:
            self._logger.error("error: 2nd line attr {}".format(line))

        return line

    def task_line3_parsing(self, line):
        self.description = line
        ru = re_truck_ton.findall(line)
        if ru is not None and len(ru) > 0 :
            self.car_limit_weight = ru[0][0]
        else:
            self._logger.error("error: 4th line attr {}".format(line))
        return line
    def task_line4_parsing(self, line):
        ru = re_fare.findall(line)
        if ru is not None and len(ru) > 0 :
            self.fare_total = ru[0][0]
        else:
            self._logger.error("error: 4th line attr {}".format(line))
        return line

    def task_line_invalid(self, line, line_no):
        self._logger.info("invalid task_line {}, {} -{}".format(line_no, line, self.task_name))

    def write_task(self, ctc_info_fd):
        #ctc_info_fd.write("{}\t{}\t{}\t".format(self.task_name, self.task_effect, self.task_cost))
        for i, line in enumerate(self.task_line_list):
            if i < 5:
                info = self.task_line_parsing_func[i](line)
                #ctc_info_fd.write(info)
                #ctc_info_fd.write("$$")
            else:
                self.task_line_invalid(line, i)

        desc = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(self.task_name, self.task_effect, self.task_cost,
                                                              self.addr_from, self.addr_to, self.fare_total,
                                                              self.reg_time, self.upload_date,
                                                              self.download_date, self.up_carry, self.down_carry, self.car_limit_weight, self.description)
        ctc_info_fd.write(desc)

        self._logger.info(desc)
        #if self.task_name.find("CT-20211116-132418-00_04") >= 0 :
        #    print(self.task_name)



class call_task:
    def __init__(self):
        logManager = Logger.instance()
        self._logger = logManager.getLogger()
        self.config = nvconfig.instance()




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
        image_file_path_list.sort()

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
                self._logger.error('exception error 3: {}'.format(image_file_name))
                is_request_succeed = False

            if is_request_succeed:
                ocr_convert_success_count += 1
                with open(json_file_path, 'w', encoding='utf-8') as outfile:
                    json.dump(ocr_json, outfile, indent=4, ensure_ascii=False)
                    self._logger.info("{} image to json:{}".format(ocr_convert_count, image_file_name))

            ocr_convert_count += 1

            #if ocr_convert_count > 10:
            #    break;

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
                self._logger.info('json parsing error -2')
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
        ctc_info_fd = open("ctc_info.txt", 'w')
        ctc_info_fd.write("{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format("task_name", "task_effect", "task_cost",
                                                              "addr_from", "addr_to", "fare_total",
                                                              "reg_time", "upload_date",
                                                              "download_date", "up_carry", "down_carry", "car_limit_weight", "description"))

        task_item = None

        for file_cnt, json_file_path in enumerate(json_file_path_list):
            self._logger.info("file start:{}".format(json_file_path))
            json_fp = open(json_file_path, mode="r", encoding='utf-8')
            ob_ocr_json = json.load(json_fp)


            if ob_ocr_json.get('images') is None:
                self._logger.info("error:There is no images tag in jsonfile:{}".format(json_file_path))
                continue
            ocr_data_list = ob_ocr_json['images']

            if ocr_data_list[0].get('fields') is None:
                self._logger.info("error:There is no fields tag in jsonfile:{}".format(json_file_path))
                continue
            ocr_data_list = ocr_data_list[0]['fields']

            ocr_data_list = sorted(ocr_data_list, key=lambda k: k['boundingPoly']['vertices'][0]['y'], reverse=False)
            print(len(ocr_data_list))
            lines = self.get_separate_line(ocr_data_list)


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
                        self._logger.info("start:{}".format(task_attr))
                        #if task_attr.find("[CT-20211116-155031-00_02.jpg]") >= 0:
                        #    print(task_attr)
                        #**중요하다. 여기서 결과파일을 쓴다.
                        if task_item is not None:
                            task_item.write_task(ctc_info_fd)
                            #이전에 입력한 task_item이 있다. file 출력을 한다.
                        task_item = TaskItem()
                        task_line = 0
                        task_count += 1



                    ret, task_attr_conv = self.task_attr_filter(task_attr, task_line )
                    if ret == -1: #사용하지 않는 속성
                        continue
                    elif ret == 1: #변형된 속성, 예를 들면 오타를 수정한 결과
                        task_attr = task_attr_conv
                    #else
                    #   task_attr 그대로 사용한다.


                    #같은 행에서 , 문장분리 - 문장과 문장이 100px넘으면 분리한다.
                    if l > 0 : #task 이름 다음 행부터 분석
                        if ln['boundingPoly']['vertices'][0]['x'] - last_attr['boundingPoly']['vertices'][1]['x'] > 100 :
                            line_string.append(ocr_group_separater)

                        #print(ln['boundingPoly']['vertices'][0]['x'] - last_attr['boundingPoly']['vertices'][1]['x'] )

                    last_attr = ln
                    line_string.append(task_attr)
                    line_string.append(ocr_unit_separater)

                if len(line_string) > 0 :
                    self._logger.info("f:{},t:{},r:{} >> {}".format(file_cnt, task_count, task_line, ''.join(line_string)))
                    task_line += 1
                    task_item.task_line_list.append(''.join(line_string))

            #end of parsing one json file.

        #end of parsing all json files
        if task_item != None:
            # 이전에 입력한 task_item이 있다. file 출력을 한다.
            task_item.write_task(ctc_info_fd)

        #file close
        ctc_info_fd.close()


    #ret 0: 그냥사용한다. -1: 사용하지 않는다, 1:값이 변경되었다. replace해야한다.
    def task_attr_filter(self, task_attr, task_line):
        # 의미없는 문는 제거한다.
        if task_attr == ">":
            return -1, None
        elif task_attr == ")":
            return -1, None
        return 0, None