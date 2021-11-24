
import json
import os
import cv2
import csv
import requests
import uuid
import time
import re
import os
import glob
import argparse
from datetime import datetime
import telegram
from nvconfig import nvconfig
from nvlogger import Logger
from call_task import call_task
import common
import sys

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







def getFileList(image_dir):
    filelist = []
    for filename in glob.iglob(image_dir, recursive=True):
        filelist.append(filename)

    return filelist

#def int(param):
#    pass
def save_ocr_json_from_image(image_file_path_pattern , json_dir_path):
    image_file_path_list = getFileList(image_file_path_pattern)
    ocr_convert_count = 0
    ocr_convert_success_count = 0

    for image_file_path in image_file_path_list:
        #image_file_path = os.path.join(image_dir, image_file_path)
        image_file_name = os.path.basename(image_file_path)
        json_file_name = image_file_name.replace('.jpg', '.json')
        json_file_path = os.path.join( json_dir_path, json_file_name)
        is_request_succeed = True
        # image로 부터 ocr 정보를 추출한다.

        try:
            ocr_json = request_ocr(image_file_path)
        except:
            print('exception error: {}'.format(image_file_name))
            is_request_succeed = False

        if is_request_succeed:
            ocr_convert_success_count += 1
            with open(json_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(ocr_json, outfile, indent=4, ensure_ascii=False)

        ocr_convert_count += 1

        if ocr_convert_count > 10:
            break;

        time.sleep(1)

    return ocr_convert_success_count



def run():
    try :
        bot = telegram.Bot(token=cc._TELEGRAM_TOKEN)
        json_file_path_pattern = os.path.join(json_dir_path, "**/*.json")

        # image 로부터 ocr 정보 json을 얻는다.
        # image_count = save_ocr_json_from_image(image_file_path_pattern, json_dir_path)
        ct = call_task()
        json_count = ct.parse_json_files(json_file_path_pattern)

    except Exception as e:
        err_msg = "exception {}".format(e)
        #bot.sendMessage(chat_id=cc._TELEGRAM_CHAT_ID, text=err_msg)
        print("exception ", e)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    image_file_path_pattern = "/project/callbary/goodnbad/good_image/**/*.jpg"
    json_dir_path = "/project/callbary/goodnbad/good_json/"

    try :
        args = argParser.parse_args()
        cc = nvconfig.instance()
        cc.setInit(None)
        ret = cc.load_file()
        logManager = Logger.instance()
        logManager.setLogger(cc._logFilePath)
        logger = logManager.getLogger()
        logger.info("-------------start--------------")
        run()

    except Exception as e:
        logger.info("main func error :  %s", e)

    sys.exit()