#!/usr/bin/python
#-*- coding:utf-8 -*-

"""
pull local log info for zabbix server, -s (source) , -b (buffer) and -d (discovery) options are necessary.
"""

import sys
import optparse
import re
import json
import os

def get_send(sourcefile, lastline):
    """
    从源文件中获取新数据, 并用zabbix_send将新数据推送给zabbix_server
opt.dir
    @param sourcefile string 文件路径
    @param lastline int   上一次读取的文件位置

    @return int 现在读取到的文件位置
    """

    file    = open(sourcefile)  
    lines   = file.readlines()  
    line    = int(len(lines))
    dis     = []                #the dict object to be translated to json data served for zabbix discovery
    lastline = int(lastline)

    file.close()

    service_reg = re.compile("\s*(\w+)")
    parts_reg   = re.compile("\s+")
    item_reg    = re.compile("([^\[]+)\[([^ ]+?)\]=([^ ]+)")

    hdiscovery = open(opt.discovery, "r")
    try:
        dis = json.loads(hdiscovery.read())
    except:
        dis = []
    hdiscovery.close()

    if lastline > line:
        #日志被回滚, 从开头读取
        dl("lastline is bigger than the total lines of source file, read from the top")
        lastline = 0

    if lastline == line:
        #日志未更新, 结束操作
        dl("lastline is equal to current total lines of source file, do nothing and quit")
        return lastline

    for i in range(lastline, line):
        #从上次结束行开始读取日志
        dl("about to parse line %s: %s " % (line, lines[i]))
        piece = service_reg.split(lines[i], 1)
        (service, left) = (piece[1], piece[2])
        dl("service is %s" % service) 
        #parts包含service后面的检查项目, 可能含有空项
        parts = parts_reg.split(left)
        for i in range(len(parts)):
            if parts[i] == '':
                continue
            items = item_reg.search(parts[i])
            if items == None:
                dl("can't get anything from the line: %s" % lines[i])
                break
            res = [service]
            #res :      [$service, $item, $key, $value]
            res.extend(list(items.groups()))
            item = {"{#SERVICE}": res[0], "{#ITEM}": res[1], "{#KEY}": res[2]}
            
            if item not in dis:
                dis.append(item)
            dl("service: %s   item: %s   key: %s    value: %s" % tuple(res))
            #todo: zabbix_sender
            command = "zabbix_sender -z 127.0.0.1 -s external -k external[%s,%s,%s] -o %s" % tuple(res)
            dl(command)
            dl(os.popen(command, "r").read())
    
    hdiscovery = open(opt.discovery, "w")
    hdiscovery.write(json.dumps(dis))
    hdiscovery.close()
    return line
        
def dl(info):
    """
    debug or | and log
    """
    global opt
    global hlogfile

    if opt.debug:
        print info

    if "hlogfile" in globals():
        hlogfile.write("%s\n" % info);

if __name__ == "__main__":

    optparser = optparse.OptionParser(usage="%s" % __doc__.strip());

    optparser.add_option("-b", "--buffer", dest="buffer_file", help="the buffer file saved the last read line")
    optparser.add_option("-s", "--source", dest="source", help="the source file for pulling logs from")
    optparser.add_option("-d", "--debug", dest="debug", action="store_true", help="print extra information but do not send data to zabbix")
    optparser.add_option("-m", "--deamon", dest="deamon", action="store_true", help="not supported yet")
    optparser.add_option("-f", "--frequency", dest="frequency", help="not supported yet")
    optparser.add_option("-l", "--logfile", dest="logfile", help="the log file which to print debug information to")
    optparser.add_option("-i", "--discovery", dest="discovery", help="a json file(contained json format string) works for zabbix discovery")
    optparser.set_defaults(buffer_file=False, source=False, debug=False, deamon=False, frequency=False, logfile=False, discovery=False)

    (opt, args) = optparser.parse_args(sys.argv)

    if ( not opt.buffer_file or not opt.source or not opt.discovery):
        print "necessary options is missing"
        sys.exit()

    #open log file
    if opt.logfile:
        hlogfile = open(opt.logfile, "a")

    dl("starting to executed")
        
    #get the last line number
    hbuffer = open(opt.buffer_file, "r")
    match = re.match("(^\d+)", hbuffer.read())
    hbuffer.close()
    if match:
        last_line = match.groups()[0]
    else:
        dl("couldn't get any numbers of the buffer file, use 0 to replace")
        last_line = 0
    
    #do the main job!
    now_line = get_send(opt.source, last_line)
    hbuffer = open(opt.buffer_file, "w")
    hbuffer.write(str(now_line))
    hbuffer.close()
    dl("now we have read the source file till line %s and saved it to the buffer" % now_line)

    #close logfile
    if opt.logfile:
        close(logfile_handler)
