#!/usr/bin/python

import json
import sys

json_file = sys.argv[1]
service = sys.argv[2]
item = sys.argv[3]    

result = {"data": []} 
jh = open(json_file, "r")
config = json.loads(jh.read())

jh.close()

for i in range(len(config)):
    if config[i]["{#SERVICE}"] == service and config[i]["{#ITEM}"] == item:
        result["data"].append(config[i])

print json.dumps(result)
