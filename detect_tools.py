# encoding:utf-8
import cv2
from PyQt5.QtGui import QPixmap, QImage
import face_recognition
import numpy as np
import json
import os
from PIL import Image,ImageDraw,ImageFont
import csv
import pandas as pd

def img_cvread(path):
    # img = cv2.imread(path)
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    return img

def info_entry_face_detect(img):
    """
    人脸录入时的人脸检测，每次只录入一张人脸，取面积最大的一张人脸
    :param img:
    :return:
    """
    img = img.copy()
    face_locations = face_recognition.face_locations(img)
    max_area = 0
    location = [0,0,0,0]
    if len(face_locations) == 0:
        return img, None
    # 解析,取面积最大的一张人脸进行录入
    for top, right, bottom, left in face_locations:
        width = right - left
        height = bottom - top
        area = width * height
        if area > max_area:
            max_area = area
            location = [top, right, bottom, left]

    top, right, bottom, left = location
    cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 3)
    return img, location


def face_rec_face_detect(img):
    """
    人脸识别检测
    :param img:
    :return:
    """
    img = img.copy()
    face_locations = face_recognition.face_locations(img)
    # max_area = 0
    # location = [0,0,0,0]
    # if len(face_locations) == 0:
    #     return img, None
    # # 解析,取面积最大的一张人脸进行录入
    # for top, right, bottom, left in face_locations:
    #     width = right - left
    #     height = bottom - top
    #     area = width * height
    #     if area > max_area:
    #         max_area = area
    #         location = [top, right, bottom, left]

    # top, right, bottom, left = location
    for top, right, bottom, left in face_locations:
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 3)
    return img, face_locations

def cvimg_to_qpiximg(cvimg):

    height, width, depth = cvimg.shape
    cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
    qimg = QImage(cvimg.data, width, height, width * depth, QImage.Format_RGB888)
    qpix_img = QPixmap(qimg)
    return qpix_img





def get_img_encode(img, location):
    """
    对人脸进行编码,可一次编码多张人脸
    :param img: 图片
    :param location: 人脸坐标位置[[top, right, bottom, left]]
    :return:
    """
    face_encodings = face_recognition.face_encodings(img, location)
    return face_encodings


def read_json(path):
    """
    读取存储的用户信息文件
    :return:
    """
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as user_file:
        data = json.load(user_file)
    return data

def save_json(path,data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def save_img(img, location, path):
    """
    裁剪并保存人脸区域的照片
    :param img: 原始照片
    :param location: 人脸位置信息top, right, bottom, left
    :param path: 保存路径
    :return:
    """
    top, right, bottom, left = location
    # 存储人像照片，将人脸区域扩大一倍进行存储
    width = right - left
    height = bottom - top
    img_height, img_width, depth = img.shape
    save_face_img = img[max(top - int(height / 2), 0):min(bottom + int(height / 2), img_height),
                    max(left - int(width / 2), 0):min(right + int(width / 2), img_width)]
    cv2.imencode('.jpg', save_face_img)[1].tofile(path)



def get_database_faces(path):
    """
    返回数据库中的人脸id及名称与人脸编码列表
    :param path:
    :return:
    """
    data = read_json(path)
    res = []
    for each in data:
        id = each
        face_encoder = data[each]['face_encoder']
        name = data[each]['name']
        res.append([id,name,face_encoder])
    return res

# 封装函数:图片上显示中文
def cv2AddChineseText(img, text, position, textColor=(0, 255, 0), textSize=50):
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)
    # 字体的格式
    fontStyle = ImageFont.truetype(
        "simsun.ttc", textSize, encoding="utf-8")
    # 绘制文本
    draw.text(position, text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def insert_rows(path, lines):
    """
    将n行数据写入csv文件
    :param path:
    :param lines:
    :return:
    """
    no_header = False
    if not os.path.exists(path):
        no_header = True
        start_num = 1
    else:
        start_num = len(open(path).readlines())

    csv_head = ['序号', '姓名', '个人ID', '检测日期']
    with open(path, 'a', newline='') as f:
        csv_write = csv.writer(f)
        if no_header:
            csv_write.writerow(csv_head)  # 写入表头

        for each_list in lines:
            # 添加序号
            each_list = [start_num] + each_list
            csv_write.writerow(each_list)
            # 序号 + 1
            start_num += 1

def read_csv(path):
    """
    读取人脸识别记录的csv文件
    :param path:
    :return:
    """
    data = pd.read_csv(path, sep=',', encoding='gbk', converters={'个人ID': str})
    return data

def save_csv_data(df, path):
    """
    保存修改后的人脸识别数据
    :param df:
    :param path:
    :return:
    """
    df['序号'] = range(1, len(df) + 1)
    df.to_csv(path, index=False,encoding='gbk')
