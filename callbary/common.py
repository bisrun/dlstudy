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


def getFileList(image_dir):
    filelist = []
    for filename in glob.iglob(image_dir, recursive=True):
        filelist.append(filename)

    return filelist


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