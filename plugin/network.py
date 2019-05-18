#!/usr/bin/env python
#_*_ coding:utf-8 _*_ 

import psutil
import time

__all__ = ["net_io_stat","net_con_stat"]


def net_io_stat(last_snetio,this_snetio,interval):
    traffic_dict = {}
    traffic_dict["kb_sent"] = round(float(this_snetio.bytes_sent -last_snetio.bytes_sent)/interval/1024,2)
    traffic_dict["kb_recv"] = round(float(this_snetio.bytes_recv -last_snetio.bytes_recv)/interval/1024,2)
    return traffic_dict

def net_con_stat():
    conns_dict = {"LISTEN":0,"ESTABLISHED":0}
    conns4_list = psutil.net_connections(kind="tcp4")
    conns6_list = psutil.net_connections(kind="tcp6")
    for con in conns4_list+conns6_list:
        if con.status == "ESTABLISHED":
            conns_dict["ESTABLISHED"] = conns_dict["ESTABLISHED"] + 1
        elif con.status == "LISTEN":
            conns_dict["LISTEN"] = conns_dict["LISTEN"] + 1
    return conns_dict

def net_if_stat():
    addrs_dict = {}
    for ethname,info in psutil.net_if_addrs().items():
        addrs_dict[ethname] = info[0].address
    return addrs_dict
    
    