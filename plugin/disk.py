#!/bin/usr/env python
#_*_ coding:utf-8 _*_ 

import psutil


__all__ = ["disk_size_usage","disk_io_usage"]

# def disk(path):
#     try:
#         disk=os.statvfs(path)
#     except:
#         return {'total':'','used':''}
#     diskUsed=(disk.f_blocks - disk.f_bfree) * disk.f_bsize
#     diskTotal=disk.f_blocks * disk.f_bsize
#     #diskUsage=float(diskUsed)/float(diskTotal) * 100
#     return {'total':round(float(diskTotal)/1024/1000/1000,2),'used':round(float(diskUsed)/1024/1000/1000,2)}

def disk_io(last_sdiskio,this_sdiskio,interval):
    #这种统计方式有概率性，因为选取的2s太短，比如采集频率是60s，那么这60s之间差值可能更大，所以会监控不准确
    #正确的统计方式是以上一次数据作为被减值，统计的读写速度就是   速度/60s   即每分钟读写速度
    last_io_total = last_sdiskio.read_count + last_sdiskio.write_count
    last_by_total = last_sdiskio.read_bytes + last_sdiskio.write_bytes
    this_io_total = this_sdiskio.read_count + this_sdiskio.write_count
    this_by_total = this_sdiskio.read_bytes + this_sdiskio.write_bytes
    #该设备每秒的传输次数 一次传输,意思是“一次I/O请求”,一次传输请求的大小是未知的,单位为个
    tps = round(float(this_io_total - last_io_total) / interval,2)
    #每秒从设备（drive expressed）读写的数据量,单位为kb
    blks = round(float(this_by_total - last_by_total) / interval / 1024,2)
    return {"tps":tps,"blks":blks}

def disk_usage():
    partitions_list = psutil.disk_partitions()
    partitions_dict = {}
    total = 0
    used = 0
    for partition in partitions_list:
        if (partition.device).startswith("/dev/sd") or (partition.device).startswith("/dev/hd"):
            if not partitions_dict.has_key(partition.device):
                partitions_dict[partition.device] =  {}
                sdiskusage = psutil.disk_usage(partition.mountpoint)
                total = total + sdiskusage.total
                used = used + sdiskusage.used
    used_percent = round(float(used)/total,2)*100
    available_percent = 100 - used_percent
    return {"used":used_percent,"available":available_percent}

def disk_size():
    partitions_list = psutil.disk_partitions()
    partitions_dict = {}
    total = 0
    for partition in partitions_list:
        if (partition.device).startswith("/dev/sd") or (partition.device).startswith("/dev/hd"):
            if not partitions_dict.has_key(partition.device):
                partitions_dict[partition.device] =  {}
                sdiskusage = psutil.disk_usage(partition.mountpoint)
                total = total + sdiskusage.total
    return round(total/1024/1000,2) #单位MB, float
    
            

