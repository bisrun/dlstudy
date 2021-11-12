
import pyautogui
import time
import telegram
import datetime
import os

import cv2
import numpy

'''
The mouse scroll wheel can be simulated by calling the scroll() function and passing an integer number of “clicks” to scroll. 
The amount of scrolling in a “click” varies between platforms. 
Optionally, integers can be passed for the the x and y keyword arguments to move the mouse cursor before performing the scroll. 
'''

major=0
minor=0

template = None

def TmMkdir(now):
    tmStampYMD = now.strftime("%Y%m%d")
    tmStampH = now.strftime("%H")
    dir = os.path.join("capture", tmStampYMD, tmStampH)
    os.makedirs(dir, exist_ok=True)

    return dir


def WaitForUpdate(resource):
    time.sleep(1)

    while True:
        more = pyautogui.locateOnScreen(resource, confidence=0.9)
        if more == None:
            break

        time.sleep(0.5)


def SplitByRow(org):
    global template

    print("spliybyrow")

    src0 = cv2.imread(org, cv2.IMREAD_GRAYSCALE)
    src = src0[0:805,0:200].copy()

    w, h = template.shape[::-1]

    result = cv2.matchTemplate(src, template, cv2.TM_CCOEFF_NORMED)

    threshold = 0.8
    loc = numpy.where(result >= threshold)

    base = org.replace(".jpg", "")
    idx = 0

    prev = (0, 0)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(src, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
        
        print(pt[1])
        if prev == None:
            prev = pt
            continue

        tmp = src0[prev[1]:pt[1], 0:1919].copy()
        prev = pt
        splitImgName = '{}_{}.jpg'.format(base, idx)
        idx += 1

        cv2.imwrite(splitImgName, tmp)
        print("take row img: ", splitImgName)
        #cv2.imshow('tmp', tmp)
        #cv2.waitKey(0)

    # 이미지 이름 뒤에다가 번호 매기기

    
def TakeScreenshot(now, dirName):
    global major
    global minor
    
    ux = 0
    uy = 160

    dx = 1919
    dy = 968

    tmStamp = now.strftime("%Y%m%d-%H%M")
    imageName = "{}/CT-{}-{}.jpg".format(dirName, tmStamp, minor)
    minor+=1
    image = pyautogui.screenshot(region=(ux, uy, (dx - ux), (dy - uy)))
    image.save(imageName)

    SplitByRow(imageName)

    return imageName


try:
   template = cv2.imread("resource/line2.png",  cv2.IMREAD_GRAYSCALE)

   while True:
    time.sleep(1)

    # Ready for screenshots data directory
    now = datetime.datetime.now()
    dirName = TmMkdir(now)

    imgName = TakeScreenshot(now, dirName)
    print("take screen shot: ", imgName)
    
    more = pyautogui.locateOnScreen("resource/deo.png", confidence=0.9)
    if more != None:
        print("Found button '+더보기'")
        # Click button "+더보기".
        pyautogui.moveTo(more)
        pyautogui.click()

        WaitForUpdate("resource/deo.png")
       
        for i in range(30):
            pyautogui.scroll(-1000)    
    else:
        print("\tNot found button '+더보기'")
        refresh = pyautogui.locateOnScreen("resource/refresh.jpg", confidence=0.9)
        if refresh == None:
            print("\tNot found button  '자동새로고침'")
            print("\tterminate")
            break
        else:
            print("\tFound button  '자동새로고침'")
            pyautogui.moveTo(refresh)
            pyautogui.click()

            WaitForUpdate("resource/refresh.jpg")
            minor=0
            major+=1

except Exception as e:
    print(e)














