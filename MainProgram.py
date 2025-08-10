# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication , QMainWindow, QFileDialog, \
    QMessageBox, QWidget, QHeaderView, QTableWidgetItem, QAbstractItemView, QHBoxLayout, QStackedLayout
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
import sys
import json
import os
sys.path.append('UIProgram')
from UIProgram.FaceRec import Ui_MainWindow
from UIProgram.FaceRecWidget import Ui_FaceRecForm
from UIProgram.InfoEntry import Ui_InfoEntryForm
from UIProgram.recRecordWidget import Ui_recRecordFrom
from UIProgram.DataManageWidget import Ui_DataManageForm
import sys, csv
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QSize
import detect_tools as tools
import cv2
import Config
import datetime
import face_recognition
import numpy as np
import dlib
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# 加载新的人脸识别模型和人脸标志预测模型
face_rec_model_path = "model/dlib_face_recognition_resnet_model_v1.dat"
predictor_model_path = "model/shape_predictor_68_face_landmarks.dat"

face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)
shape_predictor = dlib.shape_predictor(predictor_model_path)

class FaceRecPage(QWidget, Ui_FaceRecForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

class InfoEntryPage(QWidget, Ui_InfoEntryForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

class DataManagePage(QWidget, Ui_DataManageForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

class RecRecordPage(QWidget, Ui_recRecordFrom):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.initMain()
        self.signalconnect()

    def signalconnect(self):
        self.info_entry_page.PicBtn.clicked.connect(self.face_entry_open_img)
        self.info_entry_page.cameraOpenBtn.clicked.connect(self.camera_show)
        self.info_entry_page.photoBtn.clicked.connect(self.photo_img)
        self.info_entry_page.cameraCloseBtn.clicked.connect(self.video_stop)
        self.info_entry_page.saveBtn.clicked.connect(self.save_data)

        self.face_rec_page.PicBtn.clicked.connect(self.face_rec_open_img)
        self.face_rec_page.comboBox.activated.connect(self.combox_change)
        self.face_rec_page.cameraOpenBtn.clicked.connect(self.face_rec_camera_show)
        self.face_rec_page.cameraCloseBtn.clicked.connect(self.video_stop)

        self.data_manage_page.searchBtn.clicked.connect(self.data_search)
        self.data_manage_page.showAllBtn.clicked.connect(self.show_all_person_dada)
        self.data_manage_page.delBtn.clicked.connect(self.del_row_data)
        self.data_manage_page.saveBtn.clicked.connect(self.save_data_change)
        self.data_manage_page.changeBtn.clicked.connect(self.change_data)

        self.rec_record_page.searchBtn.clicked.connect(self.record_search)
        self.rec_record_page.showAllBtn.clicked.connect(self.show_all_rec_dada)
        self.rec_record_page.delBtn.clicked.connect(self.del_row_rec_data)
        self.rec_record_page.saveBtn.clicked.connect(self.save_rec_data_change)

        self.ui.exitBtn.clicked.connect(QCoreApplication.quit)

    def initMain(self):
        self.data_path = Config.data_path

        self.show_width = 500
        self.show_height = 350

        self.crop_img_width = 150
        self.crop_img_height = 150

        self.is_camera_open = False

        self.cap = None

        self.timeshow_timer = QTimer()

        # 更新视频图像
        self.timer_camera = QTimer()
        self.face_rec_time_camera = QTimer()

        # 更新人脸识别的结果信息
        self.face_rec_info_timer = QTimer()

        self.face_encode = None
        self.save_boxes = None
        self.face_names = []

        self.tolerance = 0.5  # 人脸匹配容忍度，越小要求越高

        self.face_rec_page = FaceRecPage()
        self.info_entry_page = InfoEntryPage()
        self.data_manage_page = DataManagePage()
        self.rec_record_page = RecRecordPage()

        self.qls = QStackedLayout(self.ui.show_frame)
        self.qls.addWidget(self.face_rec_page)
        self.qls.addWidget(self.info_entry_page)
        self.qls.addWidget(self.data_manage_page)
        self.qls.addWidget(self.rec_record_page)

        # 绑定按钮点击事件（页面切换和样式更新）
        self.ui.faceRecBtn.clicked.connect(self.buttonIsClicked)
        self.ui.infoEntryBtn.clicked.connect(self.buttonIsClicked)
        self.ui.dataManageBtn.clicked.connect(self.buttonIsClicked)
        self.ui.recRecordBtn.clicked.connect(self.buttonIsClicked)
        
        self.ui.faceRecBtn.clicked.connect(self.btn_click)
        self.ui.infoEntryBtn.clicked.connect(self.btn_click)
        self.ui.dataManageBtn.clicked.connect(self.btn_click)
        self.ui.recRecordBtn.clicked.connect(self.btn_click)
        
        self.qls.setCurrentIndex(1)
        self.ui.infoEntryBtn.setStyleSheet("background-color: lawngreen")
        self.ui.faceRecBtn.setStyleSheet("background-color: lightgray")
        self.ui.dataManageBtn.setStyleSheet("background-color: lightgray")
        self.ui.recRecordBtn.setStyleSheet("background-color: lightgray")
        self.ui.exitBtn.setStyleSheet("background-color: lightgray")

        # 显示时间
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.ui.lcdNumber.display(now_time)
        self.timeshow_timer.start(1000)
        self.timeshow_timer.timeout.connect(self.time_show_fun)

        # 打卡信息表格设置
        self.rec_record_page.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 表格铺满
        self.rec_record_page.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.rec_record_page.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 设置表格不可编辑
        self.rec_record_page.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置表格整行选中
        self.rec_record_page.tableWidget.verticalHeader().setVisible(False)  # 隐藏列标题
        self.rec_record_page.tableWidget.setAlternatingRowColors(True)  # 表格背景交替

        # 人脸数据管理表格设置
        # 设置固定行高为120
        self.data_manage_page.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.data_manage_page.tableWidget.verticalHeader().setDefaultSectionSize(120)
        self.data_manage_page.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置表格整行选中
        self.data_manage_page.tableWidget.verticalHeader().setVisible(False)  # 隐藏列标题
        self.data_manage_page.tableWidget.setAlternatingRowColors(True)  # 表格背景交替

        # 设置主页背景图片
        self.setObjectName("MainWindow")
        self.setStyleSheet(f"#MainWindow{{background-image:url({Config.mainwin_bg_img})}}")

    def time_show_fun(self):
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.ui.lcdNumber.display(now_time)

    def buttonIsClicked(self):
        sender  = self.sender().objectName()
        dic = {
            "faceRecBtn": 0,
            "infoEntryBtn": 1,
            "dataManageBtn": 2,
            "recRecordBtn": 3,
            'aboutBtn': 4
        }
        index = dic[sender]
        self.qls.setCurrentIndex(index)

        self.clear_rec_show_info()
        self.face_rec_page.PiclineEdit.clear()
        self.face_rec_page.show_label.clear()

        self.clear_entry_show_info()
        self.info_entry_page.PiclineEdit.clear()
        self.info_entry_page.show_label.clear()

        if index in [0, 1, 2]:
            # 需重新读取数据库
            self.database_data = tools.read_json(Config.data_path)

        if index == 2:
            self.facedata_tabel_info_show(self.database_data)

        if index == 3:
            path = Config.clock_on_records_file
            # 如果不存在文件，则创建文件
            if not os.path.exists(path):
                csv_head = ['序号', '姓名', '个人ID', '检测日期']
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(csv_head)

            self.csv_data = tools.read_csv(path)
            self.Records_tabel_info_show(self.csv_data)

        if self.is_camera_open is True:
            self.video_stop()

    def btn_click(self):
        """
        将激活的按钮颜色变为绿色
        :return:
        """
        sender = self.sender()
        btns = [self.ui.faceRecBtn, self.ui.infoEntryBtn, self.ui.dataManageBtn, self.ui.recRecordBtn, self.ui.exitBtn]
        for btn in btns:
            if btn == sender:
                btn.setStyleSheet("background-color: lawngreen")
            else:
                btn.setStyleSheet("background-color: lightgray")

    def Records_tabel_info_show(self, pd_dada):
        # 删除表格所有行
        self.rec_record_page.tableWidget.setRowCount(0)
        self.rec_record_page.tableWidget.clearContents()

        for index, row in pd_dada.iterrows():
            row_count = self.rec_record_page.tableWidget.rowCount()  # 返回当前行数(尾部)
            self.rec_record_page.tableWidget.insertRow(row_count)  # 尾部插入一行

            item_num = QTableWidgetItem(str(row['序号']))  # 序号
            item_num.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中

            item_name = QTableWidgetItem(row["姓名"])  # 姓名
            item_name.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中

            item_id = QTableWidgetItem(str(row['个人ID']))  # id
            item_id.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

            item_time = QTableWidgetItem(row['检测日期'])
            item_time.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中

            self.rec_record_page.tableWidget.setItem(row_count, 0, item_num)
            self.rec_record_page.tableWidget.setItem(row_count, 1, item_name)
            self.rec_record_page.tableWidget.setItem(row_count, 2, item_id)
            self.rec_record_page.tableWidget.setItem(row_count, 3, item_time)

    def facedata_tabel_info_show(self, json_data):
        # 删除表格所有行
        self.data_manage_page.tableWidget.setRowCount(0)
        self.data_manage_page.tableWidget.clearContents()

        person_list_id = sorted(json_data.keys())
        self.data_manage_page.tableWidget.setIconSize(QSize(120, 120)) # 设置图片大小
        for each_id in person_list_id:
            row = json_data[each_id]
            row_count = self.data_manage_page.tableWidget.rowCount()  # 返回当前行数(尾部)
            self.data_manage_page.tableWidget.insertRow(row_count)  # 尾部插入一行

            item_xuhao = QTableWidgetItem(str(row_count + 1))  # 序号
            item_xuhao.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中
            item_xuhao.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # 设置不可编辑

            item_name = QTableWidgetItem(row['name'])  # 姓名
            item_name.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中

            item_pic = QTableWidgetItem()
            icon = QIcon(row['img_path'])
            item_pic.setIcon(QIcon(icon))
            item_pic.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中
            item_pic.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # 设置不可编辑

            item_id = QTableWidgetItem(str(row['id']))  # id
            item_id.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            item_id.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # 设置不可编辑

            item_sex = QTableWidgetItem(row['sex'])
            item_sex.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中

            item_age = QTableWidgetItem(row['age'])
            item_age.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中

            item_company = QTableWidgetItem(row['company'])
            item_company.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中

            item_savetime = QTableWidgetItem(str(row['save_time']))
            item_savetime.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置文本居中

            self.data_manage_page.tableWidget.setItem(row_count, 0, item_xuhao)
            self.data_manage_page.tableWidget.setItem(row_count, 1, item_name)
            self.data_manage_page.tableWidget.setItem(row_count, 2, item_pic)
            self.data_manage_page.tableWidget.setItem(row_count, 3, item_id)
            self.data_manage_page.tableWidget.setItem(row_count, 4, item_sex)
            self.data_manage_page.tableWidget.setItem(row_count, 5, item_age)
            self.data_manage_page.tableWidget.setItem(row_count, 6, item_company)
            self.data_manage_page.tableWidget.setItem(row_count, 7, item_savetime)

    def face_entry_open_img(self):
        if self.is_camera_open is True:
            # 关闭摄像头
            self.video_stop()

        file_path, _ = QFileDialog.getOpenFileName(None, '打开图片', './', "Image files (*.jpg *.jpeg *.png)")
        if not file_path:
            return

        self.org_path = file_path
        self.cv_img = tools.img_cvread(self.org_path)
        self.person_img = self.cv_img.copy()
        face_cvimg, self.boxes = tools.info_entry_face_detect(self.cv_img)
        if self.boxes is None:
            QMessageBox.about(self, '提示', '未检测到人脸，请重新载入新图片！')
            return
        self.img_width, self.img_height = self.get_resize_size(face_cvimg)
        resize_cvimg = cv2.resize(face_cvimg, (self.img_width, self.img_height))
        pix_img = tools.cvimg_to_qpiximg(resize_cvimg)
        self.info_entry_page.show_label.setPixmap(pix_img)
        self.info_entry_page.show_label.setAlignment(Qt.AlignCenter)
        # 设置路径显示
        self.info_entry_page.PiclineEdit.setText(file_path)

        # 剪裁人脸区域图片
        top, right, bottom, left = self.boxes
        crop_face = self.cv_img[top:bottom, left:right]
        resize_crop_face = cv2.resize(crop_face, (self.crop_img_width, self.crop_img_height))
        crop_pix_img = tools.cvimg_to_qpiximg(resize_crop_face)
        self.info_entry_page.face_crop_label.setPixmap(crop_pix_img)

        # 对人脸进行编码
        self.face_encode = tools.get_img_encode(self.cv_img, [self.boxes])[0]
        self.save_boxes = self.boxes.copy()

    def camera_show(self):
        self.is_camera_open = True
        self.cap = cv2.VideoCapture(0)
        self.video_start()

    def video_start(self):
        # 定时器开启，每隔一段时间，读取一帧
        self.timer_camera.start(10)
        self.timer_camera.timeout.connect(self.open_frame)

    def open_frame(self):
        ret, self.cv_img = self.cap.read()
        if ret:
            self.face_cvimg, self.boxes = tools.info_entry_face_detect(self.cv_img.copy())
            self.img_width, self.img_height = self.get_resize_size(self.face_cvimg)
            resize_cvimg = cv2.resize(self.face_cvimg, (self.img_width, self.img_height))
            pix_img = tools.cvimg_to_qpiximg(resize_cvimg)
            self.info_entry_page.show_label.setPixmap(pix_img)
            self.info_entry_page.show_label.setAlignment(Qt.AlignCenter)
        else:
            self.cap.release()
            self.timer_camera.stop()

    def photo_img(self):
        if not self.is_camera_open:
            QMessageBox.about(self, '提示', '请先打开摄像头！')
            return
        if self.boxes is None:
            QMessageBox.about(self, '提示', '未检测到人脸，请重新拍摄！')
            return
        # 保存拍照时刻的人脸
        self.person_img = self.cv_img.copy()
        self.save_boxes = self.boxes.copy()

        top, right, bottom, left = self.save_boxes
        crop_face = self.cv_img[top:bottom, left:right]
        resize_crop_face = cv2.resize(crop_face, (self.crop_img_width, self.crop_img_height))
        crop_pix_img = tools.cvimg_to_qpiximg(resize_crop_face)
        self.info_entry_page.face_crop_label.setPixmap(crop_pix_img)

        # 对人脸进行编码
        self.face_encode = tools.get_img_encode(self.cv_img, [self.save_boxes])[0]

        if self.save_boxes is not None:
            QMessageBox.about(self, '提示', '人脸采集成功！')
            return

    def video_stop(self):
        """
        关闭摄像头或者视频
        :return:
        """
        self.is_camera_open = False
        if self.cap is not None:
            self.cap.release()
        self.timer_camera.stop()
        self.face_rec_time_camera.stop()
        self.face_rec_info_timer.stop()

        # 清空label
        self.info_entry_page.show_label.clear()
        self.face_rec_page.show_label.clear()

        self.clear_rec_show_info()

    def save_data(self):
        """
        存储用户信息
        :return:
        """
        if self.face_encode is None:
            QMessageBox.about(self, '提示', '请先采集人脸信息！')
            return

        name = self.info_entry_page.lineEdit.text()
        id = self.info_entry_page.lineEdit_2.text()
        sex = '男' if self.info_entry_page.radioButton.isChecked() else '女'
        age = self.info_entry_page.lineEdit_3.text()
        company = self.info_entry_page.lineEdit_4.text()

        face_encoder = self.face_encode.tolist()
        pre_data = tools.read_json(self.data_path)
        if not name:
            QMessageBox.about(self, '提示', '姓名不能为空！')
            return
        if not id:
            QMessageBox.about(self, '提示', '用户ID不能为空！')
            return
        if id in pre_data:
            QMessageBox.about(self, '提示', '用户ID已存在，请重新输入！')
            return

        save_time = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        photo_name = f"{id}_{name}.jpg"
        photo_path = f"{Config.user_img_path}/{photo_name}"
        user_data = {
            'name': name,
            'id': id,
            'sex': sex,
            'age': age,
            'company': company,
            'face_encoder': face_encoder,
            'img_path': photo_path,
            'save_time': save_time
        }
        # 用户ID作为唯一标识，不可重复
        pre_data[id] = user_data
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(pre_data, f, ensure_ascii=False)

        # 存储用户人脸图片
        tools.save_img(self.person_img, self.save_boxes, photo_path)
        QMessageBox.about(self, '提示', '{}用户信息保存成功！'.format(name))

    def get_resize_size(self, img):
        _img = img.copy()
        img_height, img_width, depth = _img.shape
        ratio = img_width / img_height
        if ratio >= self.show_width / self.show_height:
            self.img_width = self.show_width
            self.img_height = int(self.img_width / ratio)
        else:
            self.img_height = self.show_height
            self.img_width = int(self.img_height * ratio)
        return self.img_width, self.img_height

    def recognize_faces(self, img, boxes):
        """
        通用的人脸识别方法，减少重复代码
        :param img: 图像
        :param boxes: 人脸位置
        :return: 人脸名称列表和已知ID列表
        """
        # 对检测的人脸进行编码
        face_encodings = tools.get_img_encode(img, boxes)
        
        face_datas = tools.get_database_faces(Config.data_path)
        known_encodings = [each[2] for each in face_datas]
        
        # 对每个编码与数据库人脸进行比对
        face_names = []
        know_ids = []
        
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=self.tolerance)
            # 统计匹配的数量
            res_num = matches.count(True)
            if res_num == 1:
                first_match_index = matches.index(True)
                name = face_datas[first_match_index][1]
                know_ids.append(face_datas[first_match_index][0])
            elif res_num > 1:
                # 如有多个结果，则选取距离最小的那个结果
                distances = face_recognition.face_distance(known_encodings, face_encoding)
                min_dis_index = np.argmin(distances)
                name = face_datas[min_dis_index][1]
                know_ids.append(face_datas[min_dis_index][0])
            else:
                name = "unknown"
            face_names.append(name)
            
        return face_names, know_ids

    def face_rec_open_img(self):
        if self.is_camera_open is True:
            # 关闭摄像头
            self.video_stop()

        file_path, _ = QFileDialog.getOpenFileName(None, '打开图片', './', "Image files (*.jpg *.jpeg *.png)")
        if not file_path:
            return

        self.org_path = file_path
        self.cv_img = tools.img_cvread(self.org_path)
        face_cvimg, self.boxes = tools.face_rec_face_detect(self.cv_img)
        if self.boxes is None:
            QMessageBox.about(self, '提示', '未检测到人脸，请重新载入新图片！')
            return
        self.img_width, self.img_height = self.get_resize_size(face_cvimg)
        resize_cvimg = cv2.resize(face_cvimg, (self.img_width, self.img_height))
        pix_img = tools.cvimg_to_qpiximg(resize_cvimg)
        self.face_rec_page.show_label.setPixmap(pix_img)
        self.face_rec_page.show_label.setAlignment(Qt.AlignCenter)
        # 设置路径显示
        self.face_rec_page.PiclineEdit.setText(file_path)

        # 对检测的人脸进行编码并识别
        face_names, know_ids = self.recognize_faces(self.cv_img, self.boxes)

        # 未识别人数
        unknown_num = face_names.count('unknown')
        # 识别人数
        know_num = len(self.boxes) - unknown_num

        if know_num >= 1:
            self.face_rec_page.resLb.setText('识别成功！')
            self.face_rec_page.resLb.setStyleSheet("color:green;")
        elif unknown_num >= 1:
            self.face_rec_page.resLb.setText('信息未录入！')
            self.face_rec_page.resLb.setStyleSheet("color:red;")
            self.clear_rec_show_info()
        else:
            self.face_rec_page.resLb.setText('未检测到人脸！')
            self.face_rec_page.resLb.setStyleSheet("color:red;")
            self.clear_rec_show_info()
        self.face_rec_page.knowNumLb.setText(f'识别人数: {know_num}')
        self.face_rec_page.unknowNumLb.setText(f'未知人数: {unknown_num}')

        frame = self.cv_img.copy()
        # 将捕捉到的人脸显示出来
        for (top, right, bottom, left), name in zip(self.boxes, face_names):
            face_width = right - left
            font_size = int(face_width / 4)
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 3)  # 画人脸矩形框

            # 添加半透明框：用于显示人名标签
            blk = np.zeros(frame.shape, np.uint8)

            cv2.rectangle(blk, (left, top - font_size), (right, top), (0, 0, 255), -1)  # 注意在 blk的基础上进行绘制；
            frame = cv2.addWeighted(frame, 1.0, blk, 1, 1)

            frame = tools.cv2AddChineseText(frame, name, (left + 6, top - font_size), (0, 0, 0), font_size)

        resize_cvimg = cv2.resize(frame, (self.img_width, self.img_height))
        pix_img = tools.cvimg_to_qpiximg(resize_cvimg)
        self.face_rec_page.show_label.setPixmap(pix_img)
        self.face_rec_page.show_label.setAlignment(Qt.AlignCenter)

        # 设置下拉框
        self.face_rec_page.comboBox.clear()
        self.face_rec_page.comboBox.addItems(know_ids)
        if len(know_ids) >= 1:
            self.set_person_info(know_ids[0])

        # 更新人脸识别打卡数据
        datas = []
        clock_on_time = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        for id in know_ids:
            each_person = self.database_data[id]
            each_line = [each_person['name'], id, clock_on_time]
            datas.append(each_line)
        if len(datas) >= 1:
            tools.insert_rows(Config.clock_on_records_file, datas)

    def set_person_info(self, id):
        # 设置详细信息
        cur_person_data = self.database_data[id]
        name = cur_person_data['name']
        id = cur_person_data['id']
        sex = cur_person_data['sex']
        age = cur_person_data['age']
        company = cur_person_data['company']
        entry_time = cur_person_data['save_time']

        pic_img = tools.img_cvread(cur_person_data['img_path'])
        resize_cvimg = cv2.resize(pic_img, (self.crop_img_width, self.crop_img_width))
        pix_img = tools.cvimg_to_qpiximg(resize_cvimg)
        self.face_rec_page.face_crop_label.setPixmap(pix_img)

        self.face_rec_page.lineEdit.setText(name)
        self.face_rec_page.lineEdit_2.setText(id)
        if sex == '男':
            self.face_rec_page.radioButton.setChecked(True)
        else:
            self.face_rec_page.radioButton_2.setChecked(True)
        self.face_rec_page.lineEdit_3.setText(age)
        self.face_rec_page.lineEdit_4.setText(company)
        self.face_rec_page.lineEdit_5.setText(entry_time)

    def clear_rec_show_info(self):
        """
        清除识别界面的详细信息
        :return:
        """
        self.face_rec_page.knowNumLb.setText('识别人数: 0')
        self.face_rec_page.unknowNumLb.setText('未知人数: 0')
        self.face_rec_page.comboBox.clear()
        self.face_rec_page.face_crop_label.clear()
        self.face_rec_page.lineEdit.clear()
        self.face_rec_page.lineEdit_2.clear()
        self.face_rec_page.lineEdit_3.clear()
        self.face_rec_page.lineEdit_4.clear()
        self.face_rec_page.lineEdit_5.clear()

    def combox_change(self):
        com_text = self.face_rec_page.comboBox.currentText()
        self.set_person_info(com_text)

    def clear_entry_show_info(self):
        """
        清除人脸录入界面的详细信息
        :return:
        """
        self.info_entry_page.lineEdit.setText('')
        self.info_entry_page.lineEdit_2.setText('')
        self.info_entry_page.radioButton.setChecked(True)
        self.info_entry_page.lineEdit_3.setText('')
        self.info_entry_page.lineEdit_4.setText('')
        self.info_entry_page.face_crop_label.clear()

    def face_rec_camera_show(self):
        self.is_camera_open = True
        self.cap = cv2.VideoCapture(0)
        self.face_rec_camera_start()

    def face_rec_camera_start(self):
        self.face_rec_time_camera.start(10)
        self.face_rec_time_camera.timeout.connect(self.face_rec_open_frame)

        self.face_rec_info_timer.start(1000)
        self.face_rec_info_timer.timeout.connect(self.face_info_update)

    def face_rec_open_frame(self):
        ret, self.cv_img = self.cap.read()
        if ret:
            self.face_cvimg, self.boxes = tools.face_rec_face_detect(self.cv_img.copy())
            self.img_width, self.img_height = self.get_resize_size(self.face_cvimg)

            frame = self.cv_img.copy()
            if len(self.face_names) >= 1:
                # 将捕捉到的人脸显示出来,并画出识别结果
                for (top, right, bottom, left), name in zip(self.boxes, self.face_names):
                    face_width = right - left
                    font_size = int(face_width / 4)
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 3)  # 画人脸矩形框

                    # 添加半透明框：用于显示人名标签
                    blk = np.zeros(frame.shape, np.uint8)

                    cv2.rectangle(blk, (left, top - font_size), (right, top), (0, 0, 255), -1)  # 注意在 blk的基础上进行绘制；
                    frame = cv2.addWeighted(frame, 1.0, blk, 1, 1)

                    frame = tools.cv2AddChineseText(frame, name, (left + 6, top - font_size), (0, 0, 0), font_size)

            resize_cvimg = cv2.resize(frame, (self.img_width, self.img_height))
            pix_img = tools.cvimg_to_qpiximg(resize_cvimg)
            self.face_rec_page.show_label.setPixmap(pix_img)
            self.face_rec_page.show_label.setAlignment(Qt.AlignCenter)
        else:
            self.cap.release()
            self.face_rec_time_camera.stop()

    def face_info_update(self):
        # 使用通用人脸识别方法
        self.face_names, know_ids = self.recognize_faces(self.cv_img, self.boxes)
        # 未识别人数
        unknown_num = self.face_names.count('unknown')
        # 识别人数
        know_num = len(self.boxes) - unknown_num

        if know_num >= 1:
            self.face_rec_page.resLb.setText('识别成功！')
            self.face_rec_page.resLb.setStyleSheet("color:green;")
        elif unknown_num >= 1:
            self.face_rec_page.resLb.setText('信息未录入！')
            self.face_rec_page.resLb.setStyleSheet("color:red;")
            self.clear_rec_show_info()
        else:
            self.face_rec_page.resLb.setText('未检测到人脸！')
            self.face_rec_page.resLb.setStyleSheet("color:red;")
            self.clear_rec_show_info()

        self.face_rec_page.knowNumLb.setText(f'识别人数: {know_num}')
        self.face_rec_page.unknowNumLb.setText(f'未知人数: {unknown_num}')

        # 设置下拉框
        self.face_rec_page.comboBox.clear()
        self.face_rec_page.comboBox.addItems(know_ids)
        if len(know_ids) >= 1:
            self.set_person_info(know_ids[0])

        # 更新人脸识别打卡数据
        datas = []
        clock_on_time = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        for id in know_ids:
            each_person = self.database_data[id]
            each_line = [each_person['name'], id, clock_on_time]
            datas.append(each_line)
        if len(datas) >= 1:
            tools.insert_rows(Config.clock_on_records_file, datas)

    def record_search(self):
        search_text = self.rec_record_page.lineEdit.text()
        if not search_text.strip():
            return
        data = self.csv_data[self.csv_data['姓名'].str.contains(search_text) |
                             self.csv_data['个人ID'].str.contains(search_text)]
        self.Records_tabel_info_show(data)

    def show_all_rec_dada(self):
        self.Records_tabel_info_show(self.csv_data)

    def del_row_rec_data(self):
        if self.rec_record_page.tableWidget.currentIndex().row() == -1:
            return

        # 获取选中行的序号
        xuhao = self.rec_record_page.tableWidget.selectedItems()[0].text()
        row_index = self.csv_data[self.csv_data['序号']== int(xuhao)].index
        self.csv_data.drop(row_index, inplace=True)
        self.Records_tabel_info_show(self.csv_data)
        QMessageBox.about(self, '提示', '数据删除成功！点击保存更新数据！')

    def save_rec_data_change(self):
        """
        将改变后的人脸识别记录信息写入文件
        :return:
        """
        tools.save_csv_data(self.csv_data, Config.clock_on_records_file)
        QMessageBox.about(self, '提示', '数据保存成功！')

    def data_search(self):
        search_text = self.data_manage_page.lineEdit.text()
        if not search_text.strip():
            return

        res = {}
        for key, value in self.database_data.items():
            if search_text in value['name'] or search_text in value['id']:
                res[key] = value
        self.facedata_tabel_info_show(res)

    def show_all_person_dada(self):
        self.facedata_tabel_info_show(self.database_data)

    def del_row_data(self):
        if self.data_manage_page.tableWidget.currentIndex().row() == -1:
            return
        # 获取选中行的序号
        id = self.data_manage_page.tableWidget.selectedItems()[3].text()
        del self.database_data[id]
        self.facedata_tabel_info_show(self.database_data)
        QMessageBox.about(self, '提示', '数据删除成功！点击保存更新数据！')

    def save_data_change(self):
        tools.save_json(Config.data_path, self.database_data)
        QMessageBox.about(self, '提示', '数据保存成功！')

    def change_data(self):
        if self.data_manage_page.tableWidget.currentIndex().row() == -1:
            return
        # 获取选中行的序号
        id = self.data_manage_page.tableWidget.selectedItems()[3].text()
        pre_data = self.database_data[id]
        # 只能修改名字，性别，年龄，与公司名称
        pre_data['name'] = self.data_manage_page.tableWidget.selectedItems()[1].text()
        pre_data['sex'] = self.data_manage_page.tableWidget.selectedItems()[4].text()
        pre_data['age'] = self.data_manage_page.tableWidget.selectedItems()[5].text()
        pre_data['company'] = self.data_manage_page.tableWidget.selectedItems()[6].text()
        self.database_data[id] = pre_data
        QMessageBox.about(self, '提示', '数据修改成功！点击保存更新数据！')

if __name__ == "__main__":
    # 对于按钮或文字显示不全的，完成高清屏幕自适应设置
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
