#!/usr/bin/env python
#_*_ coding:utf-8 _*_

'''
Created on May 18, 2019

@author: yangxu
'''
import json,math,time
from plugin.cpu import cpu_usage
from plugin.disk import disk_usage
from plugin.memory import memory_usage
import psutil


def changeTime(allTime):
    day = 24*60*60
    hour = 60*60
    minu = 60
    allTime = int(allTime)
    if allTime <60:        
        return  "%d秒"%math.ceil(allTime)
    elif  allTime > day:
        days = divmod(allTime,day) 
        return "%d天, %s"%(int(days[0]),changeTime(days[1]))
    elif allTime > hour:
        hours = divmod(allTime,hour)
        return '%d时, %s'%(int(hours[0]),changeTime(hours[1]))
    else:
        mins = divmod(allTime,minu)
        return "%d分, %d秒"%(int(mins[0]),math.ceil(mins[1]))

def get_cpu_usage():
    #plugin.cpu_usage返回的是idle,user,system,iowait,需要user,system,iowait 的总和
    last_cpu_times = psutil.cpu_times()
    time.sleep(1)
    this_scputime = psutil.cpu_times()
    usage = cpu_usage(last_cpu_times, this_scputime)
    return (usage["iowait"]+usage["user"]+usage["system"])
#agent 简单状态查询api
def get_status():
    '''
        为了让用户可用自定义阀值与颜色的关系，需要在server 端增加表, agent从 server api 获取阀值的颜色值，然后
        返回，格式如下：
        {"uptime":"",
        "cpu":{"value":3,"color":"#d34212"},
        ...
        }
    '''
    status_dict = {"uptime":"","cpu":"","disk":"","mem":""}
    status_dict["uptime"] = changeTime(time.time() - psutil.boot_time())
    status_dict["cpu"] = get_cpu_usage()
    status_dict["mem"] = memory_usage()["virt_used"]
    status_dict["disk"] = disk_usage()["used"]
    return json.dumps(status_dict)

def set_server(environment):
    try:
        request_body_size = int(environment.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    else:
        data_json = eval(environment['wsgi.input'].read(request_body_size))