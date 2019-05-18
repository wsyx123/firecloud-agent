#!/usr/bin/env python
#_*_ coding:utf-8 _*_

import threading
import Queue
import os
# import sys
from wsgiref.simple_server import make_server
from optparse import OptionParser
import json
import time
from datetime import datetime
# module_path = os.path.abspath(os.path.dirname(__file__))
# sys.path.append(module_path+'/plugin')
import psutil
import logging
from utils.logger import logger_config

from plugin.cpu import cpu_load,cpu_usage
from plugin.memory import memory_usage
from plugin.disk import disk_usage,disk_io
from plugin.network import net_io_stat,net_con_stat
from plugin.process import process_thread_num
from utils.kafka_ops import KafkaOps
from utils.master import post_register,post_heartbeat,get_ip
from server_api.get_server import get_status

#server api router
def routers():
    urlpatterns = (
        ('/status', get_status),
    )
    return urlpatterns

#server api handle portal
def handle_request(environment,start_response):
    start_response('200 OK',[('Content-Type','text/plain')])
    url = environment['PATH_INFO']
    urlpatterns = routers()
    func = None
    for item in urlpatterns:
        if item[0] == url:
            func = item[1]
            break
    if func:
        return func()
    else:
        return '404 not found'

#运行一个简单http server        
def run_server(port,handle_request):
    try:
        httpd = make_server('',port,handle_request)
        logging.info("Listen on : 0.0.0.0:{}".format(port))
        httpd.serve_forever()
    except Exception as e:
        logging.error(e.message)
        os._exit(1)
        
#定时向master汇报情况函数,默认5分钟汇报一次，第一次启动会提供注册信息（ip,cpu,disk,memory,serial,network,os,hostname）        
def run_register(master,interval,start_info):
    first_flag = True
    while True:
        if first_flag:
            first_flag = post_register(master,start_info)
        else:
            first_flag = post_heartbeat(master)
        time.sleep(interval)

#从queue获取数据，发送到kafka
def run_data_to_kafka(kafka_hosts,collect_queue):
    #kafka有可能没启动，连接不成功，这里需要一直重试
    is_ok = False
    while not is_ok:
        try:
            kfkOps = KafkaOps(kafka_hosts)
        except Exception as e:
            logging.error(e.message)
            for i in range(collect_queue.qsize()):
                logging.info(collect_queue.get())
            time.sleep(20)
        else:
            is_ok = True
    while True:
        data = collect_queue.get()
        kfkOps.json_to_kafka(data["topic"], data["data"])

#以interval为时间间隔，从本机采集数据，put到 queue        
def run_collect(interval,collect_queue):
    #当agent开始启动时，需要获取参考值，获得后，间隔采集频率的秒数后就可以正常采集计算。
    first_flag = True
    while True:
        this_scputime = psutil.cpu_times()
        this_sdiskio = psutil.disk_io_counters()
        this_snetio = psutil.net_io_counters()
        #获取参考值
        if first_flag:
            last_scputime = this_scputime
            last_sdiskio = this_sdiskio
            last_snetio = this_snetio
            first_flag = False
        else:
            cpu_load_res = cpu_load()
            cpu_usage_res = cpu_usage(last_scputime,this_scputime)
            mem_usage_res = memory_usage()
            disk_io_res = disk_io(last_sdiskio,this_sdiskio,interval)
            disk_usage_res = disk_usage()
            net_io_res = net_io_stat(last_snetio,this_snetio,interval)
            net_con_res = net_con_stat()
            pro_thre_res = process_thread_num()
            
            #把最新的参考值赋值保留
            last_scputime = this_scputime
            last_sdiskio = this_sdiskio
            last_snetio = this_snetio
            
            #把数据放到collect_queue队列
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hostname = get_ip()["private_ip"]
            cpu_load_res = dict(cpu_load_res.items()+{"collect_time":timestamp,"hostname":hostname}.items())
            cpu_usage_res = dict(cpu_usage_res.items()+{"collect_time":timestamp,"hostname":hostname}.items())
            mem_usage_res = dict(mem_usage_res.items()+{"collect_time":timestamp,"hostname":hostname}.items())
            disk_io_res = dict(disk_io_res.items()+{"collect_time":timestamp,"hostname":hostname}.items())
            disk_usage_res = dict(disk_usage_res.items()+{"collect_time":timestamp,"hostname":hostname}.items())
            net_io_res = dict(net_io_res.items()+{"collect_time":timestamp,"hostname":hostname}.items())
            net_con_res = dict(net_con_res.items()+{"collect_time":timestamp,"hostname":hostname}.items())
            pro_thre_res = dict(pro_thre_res.items()+{"collect_time":timestamp,"hostname":hostname}.items())
            collect_queue.put({"topic":"cpu-load","data":cpu_load_res})
            collect_queue.put({"topic":"cpu-usage","data":cpu_usage_res})
            collect_queue.put({"topic":"mem-usage","data":mem_usage_res})
            collect_queue.put({"topic":"disk-io","data":disk_io_res})
            collect_queue.put({"topic":"disk-usage","data":disk_usage_res})
            collect_queue.put({"topic":"net-io","data":net_io_res})
            collect_queue.put({"topic":"net-conn","data":net_con_res})
            collect_queue.put({"topic":"process-thread","data":pro_thre_res})
            
        time.sleep(interval)

def main(install_path):
    #第一次fork
    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)
    except OSError,error:
        logging.error( 'fork #1 failed: %d (%s)' % (error.errno, error.strerror))
        os._exit(1)
    os.chdir('/')
    os.setsid()
    os.umask(0)
    #第二次fork
    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)
    except OSError,error:
        logging.error( 'fork #2 failed: %d (%s)' % (error.errno, error.strerror))
        os._exit(1)
    
    #解析命令行输入参数
    parser = OptionParser()
    parser.add_option("-p","--port",dest="port",help="the agent listen port,default:7000",default=7000)
    parser.add_option("-m","--master",dest="master",help="the register center of master server address,default:localhost:9000",
                      default="localhost:9000")
    parser.add_option("-k","--kafka",dest="kafka",help="the message queue server address of kafka,default:localhost:9092",
                      default="localhost:9092")
    parser.add_option("-l","--log",dest="log",help="the log file path,default:/var/log/agent.log",default="/var/log/agent.log")
    (options, args) = parser.parse_args()
    
    port = options.port
    master = options.master
    kafka_hosts = options.kafka.split(",")
    logfile = options.log
    
    #日志初始化
    logger_config(logfile)
    
    #启动http server
    http_thread = threading.Thread(target=run_server,args=(port,handle_request))
    http_thread.start()
    
    #启动register注册线程
    #agent 启动信息, agent注册的时候需要向server提供
    heartbeat_interval = 300 # 5分钟
    start_cmd = "python {} -p {} -m {} -k {} -l {}".format(os.path.join(install_path,"agent.py"),
                                                           port,master,kafka_hosts,logfile)
    start_info = {
            "port": port,
#             "master": master,
#             "kafka_hosts": kafka_hosts,
            "install_path": install_path,
            "log_full_file": logfile,
            "collect_interval": 60,
            "heartbeat_interval": heartbeat_interval,
            "pid": os.getpid(),
            "start_cmd":start_cmd,
            "is_online":1
        }
    register_thread = threading.Thread(target=run_register,args=(master,heartbeat_interval,start_info))
    register_thread.start()
    
    #初始queue，定义interval,启动采集， 发送线程
    collect_queue = Queue.Queue()
    collect_interval = 60
    collect_thread = threading.Thread(target=run_collect,args=(collect_interval,collect_queue))
    collect_thread.start()
    
    post_thread = threading.Thread(target=run_data_to_kafka,args=(kafka_hosts,collect_queue))
    post_thread.start()
    


if __name__ == "__main__":
    install_path = os.path.split(os.path.realpath(__file__))[0]
    main(install_path)

    
