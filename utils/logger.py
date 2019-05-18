#!/usr/bin/env python
#_*_ coding:utf-8 _*_
'''
Created on May 14, 2019

@author: yangxu
'''

#coding=utf-8
import logging.config

def logger_config(logfile):
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                'format': '[%(levelname)s] [%(asctime)s] [%(name)s:%(lineno)d]  %(message)s'
            },
            'standard': {
                'format': '[%(levelname)s] [%(asctime)s] [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d]  %(message)s'
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },

            "default": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": logfile,
                'mode': 'w+',
                "maxBytes": 1024*1024*5,  # 5 MB
                "backupCount": 20
            },
        },

        "root": {
            'handlers': ['default'],
            'level': "INFO",
            'propagate': False
        }
    }

    logging.config.dictConfig(LOGGING)
    

    
    