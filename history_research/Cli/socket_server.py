#! /usr/bin/env python3
# -*- coding:utf-8 -*-

import socket
import json
from _thread import start_new_thread

from base.logger import LOG

from .api import run_func


class Server():
    """cli的服务端

    cli 和 server 端通过socket来通信
    简单的协议描述:
        服务器每次发送消息之前，先发送一个长度为1024 bytes 的header
        header 里面必须包含content-length 字段，为下次发送数据的长度
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @classmethod
    def start(cls, port=12100):
        try:
            cls.sock.bind(('0.0.0.0', port))
            cls.sock.listen(10)
            LOG.info("the cli server start at port %d" % port)
            cls.loop()
        except Exception as e:
            LOG.error(str(e))
            port += 1
            cls.start(port)

    @classmethod
    def loop(cls):
        while True:
            conn, addr = cls.sock.accept()
            LOG.info("%s:%d connected !" % (addr[0], addr[1]))
            start_new_thread(cls.single_client_handle, (conn,))

    @staticmethod
    def single_client_handle(conn):
        while True:
            recv_data = conn.recv(1024)
            LOG.info("receive data(origin) %s " % recv_data)
            func = str(recv_data, 'utf-8')
            if recv_data != '':
                data = run_func(func)
                content = bytes(json.dumps(data), 'utf-8')
                header_content = bytes(json.dumps({'content-length': len(content)}), 'utf-8')
                header = header_content + b' ' * (1024 - len(header_content))
                try:
                    conn.send(header)
                    conn.send(content)
                except BrokenPipeError:
                    LOG.warning("socket disconnected")
                    conn.close()
                    return
            else:
                conn.close()
                break
        LOG.info("a client closes socket connection")

    @classmethod
    def close(cls):
        cls.sock.close()
        LOG.info("cli socket closed !")
