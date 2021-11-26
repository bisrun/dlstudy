import os,fnmatch
import easyocr

#reader = easyocr.Reader(['en'], detection='DB', recognition = 'ReXNet_LSTM_Attention', gpu=True) # need to run only once to load model into memory
reader = easyocr.Reader(['ko','en'] , gpu=True) # need to run only once to load model into memory
#image_path ="/project/callbary/imageset/CT-20211115-163759-01_01.jpg"
image_path ="/project/callbary/imageset/CT-20211112-165021-3_3.jpg"
image_dir_path ="/project/callbary/imageset"

file_names = os.listdir(image_dir_path)
for i, file_name in enumerate(file_names):
    print("{}) {}".format(i, file_name))
    image_path = os.path.join(image_dir_path, file_name)
    result = reader.readtext(image_path, detail=0)
    print(result)

