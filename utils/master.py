#!/usr/bin/env python
#_*_ coding:utf-8 _*_
'''
Created on May 12, 2019

@author: yangxu
'''

import urllib
import urllib2
import cookielib
from subprocess import Popen,PIPE
import json
import platform
from plugin.cpu import cpu_num
from plugin.disk import disk_size
from plugin.network import net_if_stat
from plugin.memory import memory_size
import logging

#使用了url白名单就不需要login了
def login_master(master,username,password):
    login_url = "http://"+master+"/login/"
    login_data = urllib.urlencode({"username":username,"password":password})
    cookie = cookielib.CookieJar()
    handler=urllib2.HTTPCookieProcessor(cookie)
    opener = urllib2.build_opener(handler)
    login_req = urllib2.Request(login_url,login_data)
    try:
        login_res = opener.open(login_req)
    except urllib2.URLError:
        print "{}连接失败".format(login_url)
    else:
        if login_res.geturl() == login_url:
            print "认证失败，认证信息:{}".format({"username":"admin","password":"admin"})
        else:
            print "认证成功，认证信息:{}".format({"username":"admin","password":"admin"})
            return {"status":True,"opener":opener}
    return {"status":False}
        

def post_register(master,start_info):
    register_url = "http://"+master+"/agent/register/"
    start_info["host"] = get_ip()["private_ip"]
    register_data = json.dumps({"asset":generate_register_info(),"agent":start_info})
    register_req = urllib2.Request(register_url,register_data)
    try:
        register_res = urllib2.urlopen(register_req)
    except urllib2.URLError:
        logging.error("{}连接失败".format(register_url))
        return True
    else:
        logging.info("注册信息发送状态:{}".format(register_res.code))
        data = json.loads(register_res.read())
        if data["code"] == 704:
            logging.error("注册失败, <资产验证返回信息:{} >  <agent验证返回信息:{}>".format(data["asset"],data["agent"]))
            return True
    return False

def post_heartbeat(master):
    heartbeat_url = "http://"+master+"/agent/heartbeat/"
    heartbeat_data = json.dumps({"host":get_ip()["private_ip"]})
    heartbeat_req = urllib2.Request(heartbeat_url,heartbeat_data)
    try:
        heartbeat_res = urllib2.urlopen(heartbeat_req)
    except urllib2.URLError:
        logging.error("{}连接失败".format(heartbeat_url))
    else:
        logging.info("心跳信息发送状态:{}".format(heartbeat_res.code))
        data = json.loads(heartbeat_res.read())
        #如果此资产主机在server端不存在，服务端返回404,返回true，让first_flag=true执行注册动作
        if data["code"] == 704:
            logging.error("此ip在资产表或agent表不存在，需要都存在，<返回报错信息:{}>".format(data["msg"]))
            return True
    return False
    

def generate_register_info():
    register_info = {
            "serial":"",
            "vendor":"",
            "private_ip":"",
            "port":22,
            "remote_user":"root",
            "remote_passwd":"password",
            "public_ip":"",
            "hostname":"",
            "cpu_no":1,
            "cpu_model":"",
            "memory":1,
            "disk":1,
            "os":"",
            "kernel":"",
            "machine_model":"",
            "agent_is_install":1
        }
    dmi_data = getDmi()
    parsed_data = parseData(dmi_data)
    pro_data = parseDmi(parsed_data)
    register_info["serial"] = pro_data["sn"]
    register_info["vendor"] = pro_data["vendor"]
    register_info["machine_model"] = pro_data["product"]
    register_info["cpu_no"] = cpu_num()
    register_info["cpu_model"] = pro_data['cpu_model']
    register_info["memory"] = memory_size()
    register_info["disk"] = disk_size()
    register_info["kernel"] = platform.release()
    register_info["hostname"] = platform.node()
    register_info["os"] = platform.platform().split("with")[1].strip("-")
    ips = get_ip()
    register_info["private_ip"] = ips["private_ip"]
    register_info["public_ip"] = ips["public_ip"]
    return register_info

def get_ip():
    if_dict = net_if_stat()
    for k in if_dict.keys():
        if k.startswith("lo") or k.startswith("docker"):
            del if_dict[k]
    if_list = [(k,if_dict[k]) for k in sorted(if_dict.keys())]
    if len(if_list) > 1:
        return {"private_ip":if_list[0][1],"public_ip":if_list[1][1]}
    else:
        return {"private_ip":if_list[0][1],"public_ip":if_list[0][1]}
            
    

''' 获取 dmidecode 命令的输出 '''
def getDmi():
    p = Popen(['dmidecode'], stdout = PIPE)
    data = p.stdout.read()
    return data

''' 根据空行分段落 返回段落列表'''
def parseData(data):
    parsed_data = []
    new_line = ''
    data = [i for i in data.split('\n') if i]
    for line in data:
        if line[0].strip():
            parsed_data.append(new_line)
            new_line = line + '\n'
        else:
            new_line += line + '\n'
    parsed_data.append(new_line)
    return [i for i in parsed_data if i]

''' 根据输入的dmi段落数据 分析出指定参数 '''
def parseDmi(parsed_data):
    dic = {}
    cpu_data = [i for i in parsed_data if i.startswith('Processor Information')]
    parsed_data = [i for i in parsed_data if i.startswith('System Information')]
    parsed_data = [i for i in parsed_data[0].split('\n')[1:] if i]
    cpu_data = [i for i in cpu_data[0].split('\n')[1:] if i]
    dmi_dic = dict([i.strip().split(':') for i in parsed_data])
    cpu_list = ([i.strip().split(':') for i in cpu_data])
    cpu_dict = dict(i for i in cpu_list if len(i) == 2)
    dic['vendor'] = dmi_dic['Manufacturer'].strip()
    dic['product'] = dmi_dic['Product Name'].strip()
    dic['sn'] = dmi_dic['Serial Number'].strip()
    dic['cpu_model'] = cpu_dict['Version']
    return dic