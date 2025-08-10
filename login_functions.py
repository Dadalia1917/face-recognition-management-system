# coding:utf-8
from PyQt5 import QtWidgets as qw

class Loginfunctions():
    def __init__(self, dbPath, conn, cursor, ui, MainWindow):
        self.dbPath = dbPath
        self.conn = conn
        self.cursor = cursor
        self.ui = ui
        self.MainWindow = MainWindow

    def user_create(self):
        user_name = self.ui.lineEditUserName.text()
        user_pwd = self.ui.lineEditPassword.text()
        sql = "insert into users (username,password) values ('%s','%s')" % (user_name, user_pwd)
        try:
            # 向数据库插入数据
            self.cursor.execute(sql)
            self.conn.commit()
        except:
            self.conn.rollback()

    def user_delete(self):
        user_name = self.ui.lineEditUserName.text()
        user_pwd = self.ui.lineEditPassword.text()
        sql = "delete from users where username='%s' and password='%s'" % (user_name, user_pwd)
        try:
            # 向数据库插入数据
            self.cursor.execute(sql)
            self.conn.commit()
        except:
            self.conn.rollback()

    def password_change(self):
        user_name = self.ui.lineEditUserName.text()
        user_pwd = self.ui.lineEditPassword.text()
        sql = "update users set password='%s' where username='%s'" % (user_pwd, user_name)
        try:
            # 向数据库插入数据
            self.cursor.execute(sql)
            self.conn.commit()
        except:
            self.conn.rollback()

    def user_deleter(self):
        user_name = self.ui.lineEditUserName.text()
        user_pwd = self.ui.lineEditPassword.text()
        sql = "select * from users where username='%s' and password='%s'" % (user_name, user_pwd)
        if len(user_name) == 0 or len(user_pwd) == 0:
            qw.QMessageBox.information(self.MainWindow, '消息',
                                       "您的用户名或密码不能为空")
        else:
            try:
                self.cursor.execute(sql)
                result = self.cursor.fetchall()
                num = len(result)
                # print(num)
                if num == 1:
                    qw.QMessageBox.information(self.MainWindow, '消息',
                                               "用户注销成功")
                    self.user_delete()
                else:
                    qw.QMessageBox.information(self.MainWindow, '消息',
                                               "用户名或密码错误")
            except:
                self.conn.rollback()

    def password_changer(self):
        user_name = self.ui.lineEditUserName.text()
        user_pwd = self.ui.lineEditPassword.text()
        sql = "select * from users where username='%s'" % (user_name)
        if len(user_name) == 0 or len(user_pwd) == 0:
            qw.QMessageBox.information(self.MainWindow, '消息',
                                       "您的用户名或密码不能为空")
        else:
            try:
                self.cursor.execute(sql)
                result = self.cursor.fetchall()
                num = len(result)
                # print(num)
                if num == 1:
                    qw.QMessageBox.information(self.MainWindow, '消息',
                                               "密码修改成功")
                    self.password_change()
                else:
                    qw.QMessageBox.information(self.MainWindow, '消息',
                                               "您要密码修改的用户不存在")
            except:
                self.conn.rollback()

    def user_register(self):
        user_name = self.ui.lineEditUserName.text()
        user_pwd = self.ui.lineEditPassword.text()
        sql = "select * from users where username='%s'" % (user_name)
        if len(user_name) == 0 or len(user_pwd) == 0:
            qw.QMessageBox.information(self.MainWindow, '消息',
                                       "您的用户名或密码不能为空！")
        else:
            try:
                self.cursor.execute(sql)
                result = self.cursor.fetchall()
                num = len(result)
                if num >= 1:
                    qw.QMessageBox.information(self.MainWindow, '消息',
                                               "用户已存在，请重新输入")
                else:
                    self.user_create()
                    qw.QMessageBox.information(self.MainWindow, '消息',
                                               "注册成功！")
            except Exception as e:
                self.conn.rollback()

    def user_login(self):
        user_name = self.ui.lineEditUserName.text()
        user_pwd = self.ui.lineEditPassword.text()

        if len(user_name) == 0 or len(user_pwd) == 0:
            qw.QMessageBox.information(self.MainWindow, '消息',
                                       "您的用户名或密码不能为空")
            return

        try:
            user_conform_sql = "select * from users where username='%s'" % (user_name)
            self.cursor.execute(user_conform_sql)
            result = self.cursor.fetchall()
            num = len(result)
            if num == 0:
                qw.QMessageBox.information(self.MainWindow, '消息',
                                           "用户名不存在，请先注册！")
                return
        except Exception as e:
            print(e)
            self.conn.rollback()

        try:
            sql = "select * from users where username='%s' and password='%s'" % (user_name, user_pwd)
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            num = len(result)
            if num == 1:
                self.cursor.close()
                self.conn.close()
                self.MainWindow.close()
                self.MainWindow.main_win.show()
            else:
                qw.QMessageBox.information(self.MainWindow, '消息',
                                           "密码错误,请重新输入密码！")
        except Exception as e:
            print(e)
            self.conn.rollback()

