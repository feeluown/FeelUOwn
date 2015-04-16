# -*- coding:utf8 -*-
__author__ = 'cosven'

from PyQt4.QtGui import QLabel, QLineEdit, QDialog, QPushButton, QVBoxLayout
from PyQt4.QtCore import SIGNAL

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
        self.ne = NetEase()

        self.__set_signal_binding()
        self.__set_widgets_prop()
        self.__set_layouts_prop()
        self.__set_me()

    def __set_signal_binding(self):
        self.login_btn.clicked.connect(self.__login)

    def __login(self):
        """登录

        在用户登录成功时，会发射("loginsuccess")信号
        """
        phone_login = False      # 0: 网易通行证, 1: 手机号登陆
        username = str(self.username_widget.text())     # 包含中文会出错
        password = str(self.password_widget.text())

        # judget if logining by using phone number
        try:
            int(username)
            phone_login = True
        except ValueError:
            pass

        data = self.ne.login(username, password, phone_login)

        # judge if __login successfully
        # if not, why
        print data['code'], type(data['code'])
        if data['code'] == 200:
            self.hint_label.setText(u'登陆成功')
            self.emit(SIGNAL('loginsuccess'), data)
            self.close()
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
        self.layout.addWidget(self.login_btn)
        self.layout.addStretch(1)
