#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : process_demo.py
# @Author: Pen
# @Date  : 2018-09-21 11:27
# @Desc  :

import time
import datetime

from multiprocessing import Process


def target():
    # 4s/23s左右
    x = []
    for i in range(0, 10000000):
        # if i % 1000 == 0:
        #     time.sleep(0.001)
        x.append(i)


if __name__ == '__main__':
    print(datetime.datetime.now())

    process = []

    for i in range(0, 16):
        t = Process(target=target)
        process.append(t)

    for p in process:
        p.start()

    for p in process:
        p.join()

    print(datetime.datetime.now())
    #
    # x = []
    # for i in range(0, 10000000):
    #     # if i % 1000 == 0:
    #     #     time.sleep(0.001)
    #     x.append(i)
    # print(datetime.datetime.now())
