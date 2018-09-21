#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : thread_demo.py
# @Author: Pen
# @Date  : 2018-09-21 09:57
# @Desc  :

# !/usr/bin/python
# encoding=utf-8
# Filename: thread-extends-class.py
# 直接从Thread继承，创建一个新的class，把线程执行的代码放到这个新的 class里
import threading
import time
import datetime


class T(threading.Thread):
    def run(self):
        print('线程{0}开始执行'.format(threading.currentThread().getName()))
        target()
        print('线程{0}执行完成'.format(threading.currentThread().getName()))


def target():
    # 23s左右
    x = []
    for i in range(0, 10000000):
        if i % 1000 == 0:
            time.sleep(0.001)
        x.append(i)


if __name__ == '__main__':
    threads = []
    print(datetime.datetime.now())
    for i in range(0, 10):
        threads.append(T())

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print(datetime.datetime.now())
