'''
Created on May 12, 2019

@author: yangxu
'''

import psutil

__all__ = ["process_thread_num"]

def process_thread_num():
    process_thread_dict = {"processes":0,"threads":0}
    pid_list = psutil.pids()
    process_thread_dict["processes"] = len(pid_list)
    for pid in pid_list:
        processObj = psutil.Process(pid)
        process_thread_dict["threads"] = process_thread_dict["threads"] + processObj.num_threads()
    return process_thread_dict