import os
import re
import sys
import time
import glob
import json
import shutil
import argparse
import threading
from collections import OrderedDict
from easyocr.easyocr import *
#OpenCV downgrade ************************
#pip uninstall opencv-python
#pip install opencv-python==4.1.2.30

from PIL import Image
from collections import OrderedDict, defaultdict
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, classification_report
import matplotlib.pyplot as plt
sys.path.append("../naver_ocr/")
from nvlogger import Logger
# Unicode for regular expression (ref. https://wazacs.tistory.com/48, https://data-newbie.tistory.com/206)
ENGLISH = "[\u0041-\u005a\u0061-\u007a]"
NUMBER = "[\u0030-\u0039]"
SPECIAL = "[\u0020-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]"
KOREAN = "[\uac00-\ud7a3]"

class OcrProperties():
    def __init__(self):
        self.user_network_path = "/project/dlstudy/easyocr_m/workspace/user_networks"
        self.model_dir_path = "/project/dlstudy/easyocr_m/workspace/user_networks/models"
        self.easyocr_config_file_path = "/project/dlstudy/easyocr_m/workspace/user_networks/config/config.yaml"
        self.image_base_dir_path = "/project/dlstudy/easyocr_m/workspace/data/input"  # 이미지 base directory, 이미지는 이 디렉토리의 하위디렉토리에 있어야 함
        self.json_base_dir_path = "/project/dlstudy/easyocr_m/workspace/data/output"  # Json base directory
        self.model_name = "TPS-ResNet-BiLSTM-Attn"
        self.save_clova = True
        self.merge_bbox = False
        self.gpu = True
        self.use_custom_model = True
        self.recog_network = 'standard'
        self.decoder = 'greedy'
        self.threshold = 0.1
        self.lang_list = []
        self.labels = ""
        self.instance_name = ""
        self.thread_lock = threading.Lock()
        self.image_file_list = []
        self.image_file_count = 0
        self.image_proc_index = -1

        self.gatherImageFilePath(self.image_base_dir_path)

    def gatherImageFilePath(self, image_base_dir_path):
        self.image_file_list  = []
        image_file_path_pattern = os.path.join(image_base_dir_path, "**/*.jpg")
        for filename in glob.iglob(image_file_path_pattern, recursive=True):
            self.image_file_list .append(filename)
        self.image_file_count = len(self.image_file_list)
        return self.image_file_list

    def getTaskImagePath(self):
        self.thread_lock.acquire()
        self.image_proc_index += 1
        self.thread_lock.release()
        if self.image_proc_index < self.image_file_count:
            return self.image_file_list[self.image_proc_index]
        else:
            return None



class MappersOCR():
    def __init__(self, ocr_properties:OcrProperties, logger, instance_name="mappers_ocr"):
        self.properties = ocr_properties
        self.logger = logger
        self.instance_name =instance_name


    def __enter__(self):
        if self.open() == False :
            raise Exception('exception:mappers_ocr open error 1')
        return self
    def __exit__(self,type,value,traceback):
        self.close()
        self.logger.info(f">>> finsih {self.instance_name}")
        pass

    # easy ocr을 사용하기 위한 모델파일을 연다.
    # thread safe 인지 모르겠다. 그래서, 각 thread는 MappersOCR instance를 가지도록한다.
    def open(self):
        with open(os.path.join(self.properties.easyocr_config_file_path)) as file:
            self.easy_config = yaml.load(file, Loader=yaml.FullLoader)
        self.properties.lang_list = self.easy_config['lang_list']
        self.properties.labels = self.easy_config['character_list']

        if self.properties.use_custom_model:
            # Using custom model
            if self.properties.model_name:
                self.logger.info(f"Using model: {self.properties.model_dir_path}/{self.properties.model_name}")
            else:
                self.logger.info(f"Using model: {self.properties.model_dir_path}/{self.properties.recog_network}")

            self.reader = Reader(self.properties.lang_list, gpu=self.properties.gpu,
                            model_storage_directory=self.properties.model_dir_path,
                            user_network_directory=self.properties.user_network_path,
                            recog_network=self.properties.recog_network,
                            config_file=self.properties.easyocr_config_file_path,
                            model_name=self.properties.model_name)
            if self.properties.recog_network.split('-')[-1] == "Attn":
                self.properties.properties.decoder = ""
        else:
            # Using default model
            print(f"Using model: EasyOCR default (None-VGG-BiLSTM-CTC)")
            reader = Reader(self.properties.lang_list, gpu=self.properties.gpu,
                            model_storage_directory=self.properties.model_storage_directory)


        return True

    def close(self):
        pass





    def osr_convert(self, src_image_path ):
        result = self.reader.readtext(src_image_path, decoder=self.properties.decoder, merge_bbox=self.properties.merge_bbox)
        return result

    def osr_convert_file(self, image_file_path , json_file_path):
        result = self.osr_convert(image_file_path)

        with Image.open(image_file_path) as img:
            img_width, img_height = img.size

        # 1. save json file for CLOVA General OCR
        if self.properties.save_clova:
            #json_file_path = self.make_directory_return_path_for_json(self.image_base_dir_path, self.json_base_dir_path,
            #                                         src_image_path, "_naver")
            self.save_json_in_clova( json_file_path,  result, img_width, img_height, self.properties.threshold)

        # 2. save json file for LabelMe
        #if self.save_labelme:
        #    json_file_path = self.make_directory_return_path_for_json(self.input_date_path,
        #                                                              self.output_date_path,
        #                                                              src_image_path, "_label")
        #    self.save_json_for_labelme(input_path,json_file_path,  result, img_width, img_height, self.properties.threshold)
        return

    def save_json_in_clova(self,  output_json_path, data, width, height, threshold=0.1):
        json_temp_dir = os.path.dirname(output_json_path)
        if os.path.exists(json_temp_dir) == False:
            self.logger.error(f"There is no directory for json : {json_temp_dir}")

        json_dict = OrderedDict()
        meta_dict = OrderedDict()
        meta_dict["imageSize"] = {"width": width, "height": height}
        meta_dict["domain"] = "general"
        meta_dict["language"] = "ko"
        json_dict["meta"] = meta_dict

        words = []

        # data - 0:bbox, 1: string, 2: confidence (ref: ./easyocr/utils.py 733 lines)
        for ii, (bbox, string, confidence) in enumerate(data):
            if confidence <= threshold:
                continue

            points = []
            for jj, (x, y) in enumerate(bbox):
                points.append([int(x), int(y)])

            words_dict = OrderedDict()
            words_dict["id"] = ii + 1
            words_dict["boundingBox"] = points
            words_dict["isVertical"] = False
            words_dict["text"] = string
            words_dict["confidence"] = float(f"{confidence:.4f}")
            words.append(words_dict)

        json_dict["words"] = words

        # save json file for CLOVA General OCR
        with open(output_json_path, 'w', encoding='utf-8') as outfile:
            json.dump(json_dict, outfile, ensure_ascii=False, indent="\t")

    def save_json_for_labelme(self, input_path, output_json_path, data, width, height, threshold=0.1):
        json_dict = OrderedDict()
        json_dict["version"] = "4.5.9"
        json_dict["shape_type"] = "rectangle"
        json_dict["flags"] = {}
        shapes = []

        image_file_name = os.path.basename(input_path)
        # data - 0:bbox, 1: string, 2: confidence (ref: ./easyocr/utils.py 733 lines)
        for ii, (bbox, string, confidence) in enumerate(data):
            if confidence <= threshold:
                continue

            left_top = [int(x) for x in bbox[0]]
            right_bottom = [int(x) for x in bbox[2]]

            shapes_dict = OrderedDict()
            shapes_dict["label"] = string
            shapes_dict["points"] = [left_top, right_bottom]
            shapes_dict["group_id"] = None
            shapes_dict["shape_type"] = "rectangle"
            shapes_dict["flags"] = {}
            shapes.append(shapes_dict)

        json_dict["shapes"] = shapes
        json_dict["imagePath"] = image_file_name
        json_dict["imageData"] = None
        json_dict["imageHeight"] = height
        json_dict["imageWidth"] = width

        # save json file for LabelMe
        with open(output_json_path, 'w', encoding='utf-8') as outfile:
            json.dump(json_dict, outfile, ensure_ascii=False, indent="\t")


    def make_directory_return_path_for_json(self, src_base_dir, target_base_dir, src_file_path, suffix ):
        # json file폴더구조를 image file 과 동일한 폴더구조를 가지도록 한다.
        json_file_path = src_file_path.replace(src_base_dir, target_base_dir)
        json_file_path = os.path.splitext(json_file_path)[0] +suffix+".json"
        json_temp_dir = os.path.dirname(json_file_path)
        if os.path.exists(json_temp_dir) == False:
            os.makedirs(json_temp_dir)
        return json_file_path

def one_thread(ocr_properties):
    proc_count = 0
    with MappersOCR(ocr_properties, _logger) as ocr :
    #ocr = MappersOCR(ocr_properties, _logger)
        # use single thread
        #ocr.open()
        while True :
            #image_file_path = "/project/dlstudy/easyocr_m/workspace/data/input/truck/20210913/10/Screenshot_20210913-100202_24.jpg"
            #json_file_path = "/project/dlstudy/easyocr_m/workspace/data/output/truck/20210913/10/Screenshot_20210913-100202_24.json"
            image_file_path = ocr_properties.getTaskImagePath()
            if image_file_path == None:
                return
            proc_count += 1
            json_file_path = ocr.make_directory_return_path_for_json(ocr.properties.image_base_dir_path, ocr.properties.json_base_dir_path, image_file_path,"")
            ocr.osr_convert_file( image_file_path, json_file_path )

            if proc_count > 10 :
                return


def multi_thread(ocr_properties):
    thread_count = os.cpu_count()
    thread_list = []
    for thr in range(thread_count):
        thread = threading.Thread(target=one_thread, args=(ocr_properties, _logger, f"thr_{thr:02d}" ))
        thread.start()
        thread_list.append(thread)

    for jj, thread in enumerate(thread_list):
        thread.join()
        print(f"{jj + 1}-th thread is terminated")



if __name__ == '__main__':
    #properties = ConfigForOCR()
    logManager = Logger.instance()
    logManager.setLogger("log.txt")
    _logger = logManager.getLogger()
    ocr_properties = OcrProperties()
    one_thread(ocr_properties)

    #multi_thread(ocr_properties)





