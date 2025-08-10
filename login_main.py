# coding:utf-8
import sqlite3

import sys
sys.path.append('UIProgram')

from login_functions import Loginfunctions
from UIProgram.LoginWin import Ui_LoginWin
from PyQt5.QtWidgets import  QMainWindow,QApplication,QWidget
import os
import Config
from MainProgram import MainWindow


class LoginMainWin(QMainWindow,Ui_LoginWin):
    def __init__(self):
        super(LoginMainWin, self).__init__()
        self.dbPath = Config.users_database_path
        self.database_init()
        self.ui =Ui_LoginWin()
        self.ui.setupUi(self)

        self.main_win = MainWindow()
        self.loginfunctions = Loginfunctions(self.dbPath, self.conn, self.cur, self.ui, self)

        self.ui.registerBtn.clicked.connect(self.loginfunctions.user_register)
        self.ui.loginBtn.clicked.connect(self.loginfunctions.user_login)


    def database_init(self):
        if not os.path.exists(self.dbPath):
            # '''创建一个数据库，文件名'''
            self.conn = sqlite3.connect(self.dbPath)
            # '''创建游标'''
            self.cur = self.conn.cursor()
            # 建用户表
            sql = '''create table users (
                    id integer primary key autoincrement,
                    username varchar(15) not null,
                    password varchar(15) not null)'''
            self.cur.execute(sql)
        else:
            self.conn = sqlite3.connect(self.dbPath)
            # '''创建游标'''
            self.cur = self.conn.cursor()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LoginMainWin()
    win.show()
    sys.exit(app.exec_())