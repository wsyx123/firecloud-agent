#!/usr/bin/env python
#_*_ coding:utf-8 _*_

import psutil
from time import sleep

__all__ = ["cpu_load","cpu_usage"]
'''
cat /proc/stat  
total     user    nice system  idle      iowait irq  softirq  steal guest  guest_nice
cpu       46612   38   16901   4975005   22939   2   1615      0     0      0

1jiffies=0.01秒

计算总的Cpu时间片totalCpuTime
         把所有cpu使用情况求和，得到total;

计算总的繁忙时间
         用total-idle,得到 usage

cpu 使用率
         (usage2-usage1)/(total2-total1)
'''

def cpu_load():
    load_tuple = psutil.getloadavg()
    return {"load1":load_tuple[0],"load5":load_tuple[1],"load15":load_tuple[2]}

def cpu_usage(last_cpu_times,this_scputime):
    #这种统计方式有概率性，因为选取的2s太短，比如采集频率是60s，那么这60s之间差值可能更大，所以会监控不准确
    #正确的统计方式是以上一次数据作为被减值，统计的读写速度就是   速度/60s   即每分钟读写速度
    #计算中将nice时间并入user时间，将irq时间和softirq时间并入system时间
    usage1 = last_cpu_times
    total1 = usage1.user + usage1.nice + usage1.system + usage1.idle + usage1.iowait + usage1.irq + usage1.softirq
    usage2 = this_scputime
    total2 = usage2.user + usage2.nice + usage2.system + usage2.idle + usage2.iowait + usage2.irq + usage2.softirq
    total = total2 - total1
    idle = round((usage2.idle - usage1.idle)/total,2)*100
    user = round((usage2.user - usage1.user + usage2.nice - usage1.nice)/total,2)*100
    system = round((usage2.system - usage1.system + usage2.irq - usage1.irq + usage2.softirq - usage1.softirq)/total,2)*100
    iowait = round((usage2.iowait - usage1.iowait)/total,2)*100
    return {"idle":idle,"user":user,"system":system,"iowait":iowait}

def cpu_num():
    return psutil.cpu_count()


