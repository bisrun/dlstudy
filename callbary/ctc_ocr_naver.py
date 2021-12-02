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

def run_step1_ocr(**args):
    image_file_path_pattern = os.path.join(args['config']._IMAGE_DIR_PATH, "**/*.jpg")
    image_count = args['parse_task'].save_ocr_json_from_image(image_file_path_pattern, args['config']._JSON_DIR_PATH)
    logger.info("---- finish run_step1_ocr -----")

def run_step2_json_parsing(**args):
    json_file_path_pattern = os.path.join(args['config']._JSON_DIR_PATH, "**/*.json")
    json_count = args['parse_task'].parse_json_files(json_file_path_pattern)
    logger.info("---- finish run_step2_json_parsing -----")

#addr 이름으로 부터 좌표를 추출한다.
def run_step3_addr_pos(**args):
    task_list = args['parse_task'].read_txt(args['config']._CTC_INFO_01_FILE_PATH)
    ct_pos = add_coord_by_addr(task_list)
    ct_pos.add_coord_attr()
    ct_pos.write_ctc_info()
    logger.info("---- finish run_step3_addr_pos -----")

#출발지 목적지위치로 부터 경로거리, ETA를 계산한다.
def run_step4_route(**args):
    task_list = args['parse_task'].read_txt(args['config']._CTC_INFO_02_FILE_PATH)
    ct_route = add_route_info(task_list)
    ct_route.add_route_result()
    ct_route.write_ctc_info()
    logger.info("---- finish run_step4_route -----")

run_step_function = {
    1: run_step1_ocr,
    2: run_step2_json_parsing,
    3: run_step3_addr_pos,
    4: run_step4_route}

def run():
    try :
        bot = telegram.Bot(token=cc._TELEGRAM_TOKEN)
        valid_step = {1:False, 2:True, 3:True, 4:True}
        step_name = {1:"ocr", 2:"parsing", 3:"addr", 4:"routing"}

        ct = call_task()
        # image 로부터 ocr 정보 json을 얻는다.

        for i in range(len(run_step_function)):
            step_no = i+1
            valid = valid_step.get(step_no)
            if valid :
                info = run_step_function[step_no](parse_task=ct, config=cc)
            else:
                logger.info(f"run step {step_no}:{step_name[step_no]} skip")

    except Exception as e:
        err_msg = "error 1 {}".format(e)
        #bot.sendMessage(chat_id=cc._TELEGRAM_CHAT_ID, text=err_msg)
        logger.info(err_msg)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser()

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