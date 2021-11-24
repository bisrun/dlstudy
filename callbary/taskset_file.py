import cv2
import numpy as np
import os
import common

image_dir = '/data1/ctc_images/20211117/**/*.jpg'
filelist = common.getFileList(image_dir)
#print(filelist)

#page_nfos = common.getFile_PageImage(filelist)
task_infos =common.getFile_TaskImage(filelist)
f = open("task_stat_20211117.txt", 'w')
for i, task in enumerate(task_infos):
    line = "{}\t{}\n".format(i, task)
    f.write(line)
f.close()