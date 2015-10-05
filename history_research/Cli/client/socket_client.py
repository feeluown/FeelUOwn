#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import socket
import json

from helpers import Helpers


class Client(object):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @classmethod
    def connect(cls, host='0.0.0.0', port=12100):
        try:
            cls.sock.connect((host, port))
            return True
        except Exception as e:
            Helpers.print_error(str(e))
        return False

    @classmethod
    def send(cls, data):
        cls.sock.sendall(bytes(str(data), "utf-8"))

    @classmethod
    def recv(cls):
        recv_header = cls.sock.recv(1024)
        headers = json.loads(recv_header.decode('utf-8'))
        content_length = headers['content-length']
        recv_data = cls.sock.recv(content_length)
        data = recv_data.decode('utf-8')
        data_dict = json.loads(data)
        Helpers.check_data(data_dict)
        return data_dict

    @classmethod
    def close(cls):
        cls.sock.close()


if __name__ == "__main__":
    Client.connect(port=12100)
