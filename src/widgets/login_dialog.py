# -*- coding:utf8 -*-
__author__ = 'cosven'

import os
import json
import hashlib

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from base.network_manger import NetworkManager

from base.logger import LOG
from base.common import write_json_into_file

from constants import DATA_PATH


class LoginDialog(QDialog):
    """登录对话框
    描述: 弹出登录对话框，用户输入用户名和密码，点击登录按钮调用login函数。
        登录成功则发射("loginsuccess")信号，失败则显示相关提示信息

    调用: 1. 在用户登录成功时，会发射("login_success")信号
    
    """
    signal_login_sucess = pyqtSignal([dict], name='login_success')
    pw_filename = "ne_un_pw.json"

    def __init__(self, parent):
        super(LoginDialog, self).__init__(parent)
        self.username_lable = QLabel()
        self.password_lable = QLabel()
        self.hint_label = QLabel()
        self.username_widget = QLineEdit()
        self.password_widget = QLineEdit()
        self.login_btn = QPushButton()

        self.captcha_label = QLabel()
        self.captcha_lineedit = QLineEdit()

        self.layout = QVBoxLayout()
        self.is_remember_chb = QCheckBox(u'记住账号')

        self.nm = NetworkManager()

        self.ne = parent.api

        self.is_autofill = False
        self.is_need_captcha = False
        self.captcha_id = 0
        self.user_data = 0

        self.__set_signal_binding()
        self.__set_widgets_prop()
        self.__set_layouts_prop()
        self.__set_me()
        self.fill_content()

    def __set_signal_binding(self):
        self.login_btn.clicked.connect(self.__login)
        self.password_widget.textChanged.connect(self.on_password_lineedit_changed)

    def fill_content(self):
        """
        判断之前是否保存了用户名和密码:
            保存了就是直接加载
        """
        if self.has_saved_userinfo():
            try:
                f = open(DATA_PATH + self.pw_filename, 'r')
                login_data = json.load(f)
                f.close()
                if 'is_remember' in login_data.keys() and login_data['is_remember']:
                    self.username_widget.setText(str(login_data['username']))
                    self.password_widget.setText(str(login_data['password']))
                    self.is_remember_chb.setCheckState(2)
                    self.is_autofill = True
            except Exception as e:
                LOG.error(str(e))

    def has_saved_userinfo(self):
        """判断之前是否有保存过的用户名与密码
        :return:
        """
        if os.path.exists(DATA_PATH + self.pw_filename):
            return True
        return False

    def save_login_info(self, login_data):
        if login_data['is_remember']:
            try:
                f = open(DATA_PATH + self.pw_filename, 'w')
                if self.is_autofill is not True:    # 如果不是自动填充，说明密码时已经没有加密过
                    password = login_data['password'].encode('utf-8')
                    login_data['password'] = hashlib.md5(password).hexdigest()
                data_json = json.dumps(login_data)
                write_json_into_file(data_json, f)
            except Exception as e:
                LOG.error(str(e))
        else:
            try:
                os.remove(DATA_PATH + self.pw_filename)
            except Exception as e:
                LOG.warning(str(e))

    def __login(self):
        """登录

        在用户登录成功时，会发射("login_success")信号
        """
        data = {}
        if self.is_need_captcha is True:
            captcha_text = str(self.captcha_lineedit.text())
            flag, self.captcha_id = self.ne.confirm_captcha(self.captcha_id, captcha_text)
            if flag is not True:
                self.hint_label.setText(u'验证码错误')
                url = self.ne.get_captcha_url(data['captchaId'])
                request = QNetworkRequest(QUrl(url))
                self.nm.get(request)
                self.parent().network_queue.put(self.show_captcha)
                return

        phone_login = False      # 0: 网易通行证, 1: 手机号登陆
        username = str(self.username_widget.text())     # 包含中文会出错
        password = str(self.password_widget.text())
        # 2: checked, 1: partial checked
        is_remember = self.is_remember_chb.checkState()

        # judget if logining by using phone number
        if username.isdigit() and len(username) == 11:
            username = int(username)
            phone_login = True
            LOG.info(u"正在使用手机号进行登录")

        login_data = {
            'username': username,
            'password': password,
            'is_remember': is_remember
        }

        if not self.is_autofill:
            data = self.ne.login(username, password, phone_login)
        else:
            data = self.ne.auto_login(username, password, phone_login)

        if data['code'] == 200:
            self.hint_label.setText(u'登录成功')
            self.signal_login_sucess.emit(data)
            self.close()
            self.save_login_info(login_data)
        elif data['code'] == 415:   # 需要验证码
            self.is_need_captcha = True
            self.hint_label.setText(data['message'])
            LOG.info(u'本次登陆需要验证码')
            self.captcha_id = data['captchaId']
            self.captcha_label.show()
            self.captcha_lineedit.show()
            url = self.ne.get_captcha_url(data['captchaId'])
            request = QNetworkRequest(QUrl(url))
            self.nm.get(request)
            self.parent().network_queue.put(self.show_captcha)
        elif data['code'] == 408:
            self.hint_label.setText(u'网络连接超时')
        elif data['code'] == 501:
            self.hint_label.setText(u'用户名错误')
        elif data['code'] == 502:
            self.hint_label.setText(u'密码错误')
        elif data['code'] == 509:
            self.hint_label.setText(u'你可能正在使用手机号登陆，密码错误几次之后，你可能需要等待几分钟再登录')
        else:
            self.hint_label.setText(u'未知错误')

    def show_captcha(self, res):
        img = QImage()
        img.loadFromData(res.readAll())
        self.captcha_label.setPixmap(QPixmap(img))

    @pyqtSlot()
    def on_password_lineedit_changed(self):
        self.is_autofill = False

    def __set_me(self):
        self.setObjectName('login_dialog')
        self.setLayout(self.layout)

    def __set_widgets_prop(self):
        self.login_btn.setText(u'登录')

        self.username_lable.setText(u'网易邮箱或者手机号')
        self.password_lable.setText(u'密码')
        self.username_widget.setPlaceholderText(u'请输入用户名')
        self.password_widget.setPlaceholderText(u'请输入密码')

        self.username_widget.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.password_widget.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)

        self.captcha_label.hide()
        self.captcha_lineedit.hide()

        self.password_widget.setEchoMode(QLineEdit.Password)

    def __set_layouts_prop(self):
        self.layout.addWidget(self.username_lable)
        self.layout.addWidget(self.username_widget)
        self.layout.addWidget(self.password_lable)
        self.layout.addWidget(self.password_widget)
        self.layout.addWidget(self.hint_label)
        self.layout.addWidget(self.captcha_label)
        self.layout.addWidget(self.captcha_lineedit)
        self.layout.addWidget(self.is_remember_chb)
        self.layout.addWidget(self.login_btn)
        self.layout.addStretch(1)
