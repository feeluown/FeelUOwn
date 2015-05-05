# -*- coding:utf8 -*-
__author__ = 'cosven'

import os
import json

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from api import NetEase


class LoginDialog(QDialog):
    """登录对话框
    描述: 弹出登录对话框，用户输入用户名和密码，点击登录按钮调用login函数。
        登录成功则发射("loginsuccess")信号，失败则显示相关提示信息

    调用: 1. 在用户登录成功时，会发射("loginsuccess")信号
    
    """
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.username_lable = QLabel()
        self.password_lable = QLabel()
        self.hint_label = QLabel()
        self.username_widget = QLineEdit()
        self.password_widget = QLineEdit()
        self.login_btn = QPushButton()
        self.layout = QVBoxLayout()
        self.is_remember_chb = QCheckBox(u'记住账号')
        self.filename = 'cache/user.json'
        self.ne = NetEase()

        self.__set_signal_binding()
        self.__set_widgets_prop()
        self.__set_layouts_prop()
        self.__set_me()
        self.init_me()

    def __set_signal_binding(self):
        self.login_btn.clicked.connect(self.__login)

    def init_me(self):
        """
        判断之前是否保存了用户名和密码:
            保存了就是直接加载
            没保存就pass
        """
        if os.path.exists(self.filename):
            f = open(self.filename, 'r')
            login_data = json.load(f)
            f.close()
            if 'is_remember' in login_data.keys() and login_data['is_remember']:
                username = login_data['username']
                password = login_data['password']
                is_remember = login_data['is_remember']
                self.username_widget.setText(username)
                self.password_widget.setText(password)
                self.is_remember_chb.setCheckState(is_remember)
        return

    def save_login_info(self, login_data):
        if login_data['is_remember']:
            f = open(self.filename, 'w')
            jsondata = json.dumps(login_data)
            f.write(jsondata)
            f.close
        else:
            os.remove(self.filename)

    def __login(self):
        """登录

        在用户登录成功时，会发射("loginsuccess")信号
        """
        login_data = {}

        phone_login = False      # 0: 网易通行证, 1: 手机号登陆
        username = str(self.username_widget.text())     # 包含中文会出错
        password = str(self.password_widget.text())
        # 2: checked, 1: partial checked
        is_remember = self.is_remember_chb.checkState()

        login_data['username'] = username
        login_data['password'] = password
        login_data['is_remember'] = is_remember
        # judget if logining by using phone number
        try:
            int(username)
            phone_login = True
        except ValueError:
            pass

        data = self.ne.login(username, password, phone_login)

        # judge if __login successfully
        # if not, why
        if data['code'] == 200:
            self.hint_label.setText(u'登陆成功')
            self.emit(SIGNAL('loginsuccess'), data)
            self.close()
            self.save_login_info(login_data)

        elif data['code'] == 408:
            self.hint_label.setText(u'网络连接超时')
        elif data['code'] == 501:
            self.hint_label.setText(u'用户名错误')
        elif data['code'] == 502:
            self.hint_label.setText(u'密码错误')
        else:
            self.hint_label.setText(u'未知错误')

    def __set_me(self):
        self.setObjectName('login_dialog')
        self.setLayout(self.layout)

    def __set_widgets_prop(self):
        self.login_btn.setText(u'登陆')

        self.username_lable.setText(u'网易邮箱或者手机号')
        self.password_lable.setText(u'密码')
        self.username_widget.setPlaceholderText(u'请输入用户名')
        self.password_widget.setPlaceholderText(u'请输入密码')
        self.password_widget.setEchoMode(QLineEdit.Password)

    def __set_layouts_prop(self):
        self.layout.addWidget(self.username_lable)
        self.layout.addWidget(self.username_widget)
        self.layout.addWidget(self.password_lable)
        self.layout.addWidget(self.password_widget)
        self.layout.addWidget(self.hint_label)
        self.layout.addWidget(self.is_remember_chb)
        self.layout.addWidget(self.login_btn)
        self.layout.addStretch(1)
