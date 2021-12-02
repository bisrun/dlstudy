import re
import os
import glob

def getDirList(dir_path, dirlist):
    with os.scandir(dir_path) as entries:
        for entry in entries :
            if entry.is_dir():
                dirlist.append(entry.path)
                dirlist = getDirList(entry.path, dirlist)
        return dirlist

def makedirs(path):
   try:
        os.makedirs(path)
   except OSError:
       if not os.path.isdir(path):
           raise

def getFileList(image_dir):
    filelist = []
    for filename in glob.iglob(image_dir, recursive=True):
        filelist.append(filename)

    return filelist

def make_directory_return_path_for_json( src_base_dir, target_base_dir, src_file_path, target_file_suffix , target_file_ext):
    # json file폴더구조를 image file 과 동일한 폴더구조를 가지도록 한다.
    if src_file_path.find(src_base_dir) != 0:
        return None
    json_file_path = src_file_path.replace(src_base_dir, target_base_dir)
    json_file_path = "{}{}.{}".format(os.path.splitext(json_file_path)[0], target_file_suffix, target_file_ext)
    json_temp_dir = os.path.dirname(json_file_path)
    if os.path.exists(json_temp_dir) == False:
        os.makedirs(json_temp_dir)
    return json_file_path

def getFile_PageImage(gpsFileNameList):
    file_info_list = []
    #p = re.compile(r"CT-(\d+)-(\d+)-(\d+).jpg")
    p = re.compile(r"CT-(\d+)-(\d+)-(\d+).jpg")
    #p = re.compile(r"CT-\w+_(\d+)_(\d+_\d+)_PT.shp")

    for filepath in gpsFileNameList:
        file_name = os.path.basename(filepath)
        ru = p.findall(file_name)
        if len(ru) > 0:
            dir_path = os.path.dirname(filepath)
            file_info = "{}\t{}\t{}\t{}".format(ru[0][0], ru[0][1], ru[0][2],  dir_path)
            file_info_list.append(file_info)

    return file_info_list

def getFile_TaskImage(gpsFileNameList):
    file_info_list = []
    #p = re.compile(r"CT-(\d+)-(\d+)-(\d+).jpg")
    p = re.compile(r"CT-(\d+)-(\d+)-(\d+)_(\d+).jpg")
    #p = re.compile(r"CT-\w+_(\d+)_(\d+_\d+)_PT.shp")

    for filepath in gpsFileNameList:
        file_name = os.path.basename(filepath)
        ru = p.findall(file_name)
        if len(ru) > 0:
            dir_path = os.path.dirname(filepath)
            file_info = "{}\t{}\t{}\t{}\t{}".format(ru[0][0], ru[0][1], ru[0][2], ru[0][3],  dir_path)
            file_info_list.append(file_info)

    return file_info_list