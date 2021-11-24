
import json
import os
import cv2
import csv
import requests
import uuid
import time


def request_ocr(image_file_path):

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

def get_layout_check(ocr_data_list):
    type = 0
    is_exist_max = False
    for item in ocr_data_list:
        if item['inferText'].find("최대") != -1:
            is_exist_max = True
            type = 1


    if not is_exist_max:
        for item in ocr_data_list:
            if (item['boundingPoly']['vertices'][3]['y'] < 400) & (item['inferText'].find("원") != -1):
                type = 2

    return type

def data_filter(ocr_data_list, type):

    #is_round_trip = False
    tmp_ocr_data_list = []

    round_trip_bbox = None

    if type == 1:
        for item in ocr_data_list:
            if not item.get('inferText'):
                print('간혹 inferText가 없다.')
                continue

            #if item['inferText'] == '왕복':
            #    round_trip_bbox = item['boundingPoly']['vertices']

            if item['boundingPoly']['vertices'][3]['y'] < 450:
                continue

            if item['boundingPoly']['vertices'][3]['y'] > 1750:
            #if item['boundingPoly']['vertices'][3]['y'] > 1450:
                continue

            if item['inferText'].find("최대") != -1:
                continue

            if item['inferText'].find("10건") != -1:
                continue

            if item['inferText'].find("잔액") != -1:
                continue

            if item['inferText'] == '#':
                continue

            #> 예외처리
            if item['inferText'] == '>':
                continue

            if item['inferText'] == 'N':
                continue

            tmp_ocr_data_list.append(item)
    elif(type == 2):
        for item in ocr_data_list:
            if not item.get('inferText'):
                print('간혹 inferText가 없다.')
                continue

            #if item['inferText'] == '왕복':
            #    round_trip_bbox = item['boundingPoly']['vertices']

            #if (item['boundingPoly']['vertices'][3]['y'] < 400):
            #    continue

            #if (item['boundingPoly']['vertices'][3]['y'] > 1650):
            #    continue

            #if item['inferText'].find("잔액") != -1:
            #    continue

            #if item['inferText'] == '#':
            #    continue

            # > 예외처리
            if item['inferText'] == '>':
                continue

            if item['inferText'] == 'N':
                continue

            tmp_ocr_data_list.append(item)
            #print(item['inferText'])

    return tmp_ocr_data_list

def compare_the_axis_y(prior_item, cur_item):
    #print('prior_item : ', prior_item, 'cur_item : ', cur_item)

    thesh_hold = 15
    #thesh_hold = 25

    prior_low_y1 = prior_item['boundingPoly']['vertices'][2]['y']
    prior_low_y2 = prior_item['boundingPoly']['vertices'][3]['y']
    cur_low_y1 = cur_item['boundingPoly']['vertices'][2]['y']
    cur_low_y2 = cur_item['boundingPoly']['vertices'][3]['y']

    diff1 = abs(cur_low_y1 - prior_low_y1)
    diff2 = abs(cur_low_y2 - prior_low_y2)

    if  (diff1 < thesh_hold) or (diff2 < thesh_hold):
        return True
    else:
        return False

def get_separate_line(ocr_data_list):

    full_line_item_list = []
    line_item_list = []
    index = 0

    for cur_item in ocr_data_list:
        if not cur_item.get('inferText'):
            print('문제 있음')
            continue

        length = len(line_item_list)

        if length == 0:
            line_item_list.append(cur_item)
        else:
            prior_item = ocr_data_list[index - 1]
            is_same_line = compare_the_axis_y(prior_item, cur_item)

            if is_same_line:
                line_item_list.append(cur_item)
            else:
                full_line_item_list.append(line_item_list)
                line_item_list = []
                line_item_list.append(cur_item)

        index = index + 1

    return full_line_item_list

def get_separate_axis_x(line_seperate_item_list):

    full_axis_x_seperate_item_list = []

    for line_items in line_seperate_item_list:
        #y축으로 분리된 id list의 길이 1
        if len(line_items) == 1:
            full_axis_x_seperate_item_list.append(line_items)
            continue

        axis_x_seperate_item_list = []
        for cur_item in line_items:

            axis_x_seperate_item_length = len(axis_x_seperate_item_list)

            if len(axis_x_seperate_item_list) == 0:
                axis_x_seperate_item_list.append(cur_item)
            else:
                prior_item = axis_x_seperate_item_list[axis_x_seperate_item_length - 1]
                is_same_axis_x = compare_the_axis_x(prior_item, cur_item)

                if is_same_axis_x:
                    axis_x_seperate_item_list.append(cur_item)
                else:
                    full_axis_x_seperate_item_list.append(axis_x_seperate_item_list)
                    axis_x_seperate_item_list = []
                    axis_x_seperate_item_list.append(cur_item)

        #로직이 끝난 뒤에 남은 게 있으면
        if len(axis_x_seperate_item_list) > 0:
            full_axis_x_seperate_item_list.append(axis_x_seperate_item_list)

    return full_axis_x_seperate_item_list

def compare_the_axis_x(prior_item, cur_item):


    thesh_hold = 130

    #prior이란 cur의 bbox index를 다르게 해야 된다. 왜냐 하면
    prior_low_x2 = prior_item['boundingPoly']['vertices'][2]['x']
    cur_low_x2 = cur_item['boundingPoly']['vertices'][0]['x']

    diff = abs(cur_low_x2 - prior_low_x2)

    if (diff > thesh_hold):
        return False
    else:
        return True


#def int(param):
#    pass


if __name__ == "__main__":

    dir_image_path = "./image"
    dif_box_image_path = "./box_image"
    image_ext = r".jpg"
    image_file_path_list = [file for file in os.listdir(dir_image_path) if file.endswith(image_ext)]

    for image_file_name in image_file_path_list:
        image_file_path = os.path.join(dir_image_path, image_file_name)
        box_image_file_path = os.path.join(dif_box_image_path, image_file_name)

        json_file_path = image_file_path.replace('.jpg', '.json')

        is_request_succeed = True

        try:
            ocr_json = request_ocr(image_file_path)
        except:
            print('exception')
            is_request_succeed = False

        #
        if is_request_succeed:
            with open(json_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(ocr_json, outfile, indent=4, ensure_ascii=False)

        #json_file_path = "./image/bad_truck_group_20211116-160632_0.json"
        #json_file_path = "/project/callbary/goodnbad/good/good_truck_group_20211122-172633_1.jpg"
        image = cv2.imread(image_file_path, cv2.IMREAD_COLOR)
        height, width, ch = image.shape

        json_fp = open(json_file_path, mode="r", encoding='utf-8')
        ob_ocr_json = json.load(json_fp)

        ocr_data_list = ob_ocr_json['images']
        ocr_data_list = ocr_data_list[0]['fields']

        #layout에 "최대" 텍스트 라인 없는 경우가 있어서 type를 나눈
        img_type = get_layout_check(ocr_data_list)
        ocr_data_list = data_filter(ocr_data_list, img_type)
        ocr_data_list = sorted(ocr_data_list, key=lambda k: k['boundingPoly']['vertices'][0]['y'], reverse=False)

        line_seperate_item_list = get_separate_line(ocr_data_list)

        line_sorted_separate_item_list = []
        for lines in line_seperate_item_list:
            sort_lines = sorted(lines, key=lambda k: k['boundingPoly']['vertices'][0]['x'], reverse=False)
            line_sorted_separate_item_list.append(sort_lines)

        full_axis_x_seperate_item_list = get_separate_axis_x(line_sorted_separate_item_list)

        for line_items in full_axis_x_seperate_item_list:

            full_box_list_x = []
            full_box_list_y = []

            for item in line_items:
                bbox = item['boundingPoly']['vertices']

                for box in bbox:
                    full_box_list_x.append(box['x'])
                    full_box_list_y.append(box['y'])

            min_x = round(min(tuple(full_box_list_x)))
            min_y = round(min(tuple(full_box_list_y)))
            max_x = round(max(tuple(full_box_list_x)))
            max_y = round(max(tuple(full_box_list_y)))

            cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 0, 0), 2)

        cv2.imwrite(box_image_file_path, image)
        #cv2.imshow('test', image)
        #cv2.waitKey(0)
