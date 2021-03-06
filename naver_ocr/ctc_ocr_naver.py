
import json
import os
import cv2
import csv

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
from ctc_add_info import add_coord_by_addr ,add_route_info
import sys



def run():
    try :
        bot = telegram.Bot(token=cc._TELEGRAM_TOKEN)
        json_file_path_pattern = os.path.join(cc._JSON_DIR_PATH, "**/*.json")
        image_file_path_pattern = os.path.join(cc._IMAGE_DIR_PATH, "**/*.jpg")

        ct = call_task()
        # image 로부터 ocr 정보 json을 얻는다.

        #image_count = ct.save_ocr_json_from_image(image_file_path_pattern, cc._JSON_DIR_PATH)

        json_count = ct.parse_json_files(json_file_path_pattern)

        #addr 이름으로 부터 좌표를 추출한다.
        task_list = ct.read_txt(cc._CTC_INFO_01_FILE_PATH )
        ct_pos = add_coord_by_addr(task_list)
        ct_pos.add_coord_attr()
        ct_pos.write_ctc_info()

        task_list2 = ct.read_txt(cc._CTC_INFO_02_FILE_PATH )
        ct_route = add_route_info(task_list2)
        ct_route.add_route_result()
        ct_route.write_ctc_info()


    except Exception as e:
        err_msg = "error 1 {}".format(e)
        #bot.sendMessage(chat_id=cc._TELEGRAM_CHAT_ID, text=err_msg)
        logger.info(err_msg)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    #image_file_path_pattern = "/project/callbary/goodnbad/good_image/**/*.jpg"
    #image_dir_path = "/project/callbary/goodnbad/GroupCount/"

    #json_dir_path = "/project/callbary/goodnbad/test_json/"
    #json_dir_path = "/project/callbary/goodnbad/good_json/"

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