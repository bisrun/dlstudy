import os
import re
import sys
import time
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


class MappersOCR():
    def __init__(self, logger):
        #self.properties = ocr_properties
        self.logger = logger
        self.user_network_path =        "/project/dlstudy/easyocr_m/workspace/user_networks"
        self.model_dir_path =           "/project/dlstudy/easyocr_m/workspace/user_networks/models/"
        self.easyocr_config_file_path = "/project/dlstudy/easyocr_m/workspace/user_networks/config/config.yaml"
        self.image_base_dir_path =          "/project/dlstudy/easyocr_m/workspace/data/input/" #이미지 base directory
        self.json_base_dir_path =         "/project/dlstudy/easyocr_m/workspace/data/output/" #Json base directory

        self.model_name = "TPS-ResNet-BiLSTM-Attn"
        self.save_clova = True
        self.merge_bbox = False
        self.gpu = True
        self.use_custom_model = True
        self.recog_network = 'standard'
        self.decoder = 'greedy'
        self.threshold = 0.1


    def open(self):
        with open(os.path.join(self.easyocr_config_file_path)) as file:
            self.easy_config = yaml.load(file, Loader=yaml.FullLoader)
        self.lang_list = self.easy_config['lang_list']
        self.labels = self.easy_config['character_list']

        if self.use_custom_model:
            # Using custom model
            if self.model_name:
                self.logger.info(f"Using model: {self.model_dir_path}/{self.model_name}")
            else:
                self.logger.info(f"Using model: {self.model_dir_path}/{self.recog_network}")

            self.reader = Reader(self.lang_list, gpu=self.gpu,
                            model_storage_directory=self.model_dir_path,
                            user_network_directory=self.user_network_path,
                            recog_network=self.recog_network,
                            config_file=self.easyocr_config_file_path,
                            model_name=self.model_name)
            if self.recog_network.split('-')[-1] == "Attn":
                self.properties.decoder = ""
        else:
            # Using default model
            print(f"Using model: EasyOCR default (None-VGG-BiLSTM-CTC)")
            reader = Reader(self.properties.lang_list, gpu=self.properties.gpu,
                            model_storage_directory=self.properties.model_storage_directory)


    def close(self):
        pass
    def osr_convert(self, src_image_path ):
        result = self.reader.readtext(src_image_path, decoder=self.decoder, merge_bbox=self.merge_bbox)
        return result
    def osr_convert_file(self, image_file_path , json_file_path):
        result = self.osr_convert(image_file_path)

        with Image.open(image_file_path) as img:
            img_width, img_height = img.size

        # 1. save json file for CLOVA General OCR
        if self.save_clova:
            #json_file_path = self.make_directory_return_path_for_json(self.image_base_dir_path, self.json_base_dir_path,
            #                                         src_image_path, "_naver")
            self.save_json_in_clova( json_file_path,  result, img_width, img_height, self.threshold)

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


if __name__ == '__main__':

    #properties = ConfigForOCR()
    logManager = Logger.instance()
    logManager.setLogger("log.txt")
    _logger = logManager.getLogger()
    ocr = MappersOCR( _logger)

    # use single thread
    ocr.open()
    image_file_path = "/project/dlstudy/easyocr_m/workspace/data/input/truck/20210913/10/Screenshot_20210913-100202_24.jpg"
    json_file_path = "/project/dlstudy/easyocr_m/workspace/data/output/truck/20210913/10/Screenshot_20210913-100202_24.json"
    ocr.osr_convert_file( image_file_path, json_file_path )
