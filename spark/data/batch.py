from elasticsearch import Elasticsearch
from kafka import KafkaConsumer
from kafka.common import NodeNotReadyError
import logging
import json
import urllib.request
import time

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    while True:
        try:
            es = Elasticsearch(['es'])
            task_consumer = KafkaConsumer("task_topic", group_id='listing_indexer'
                    , bootstrap_servers=['kafka:9092'])
            break
        except NodeNotReadyError:
            continue
    while True:
        with open('es.json', mode='rb') as es_fixtures_file: 
            fileContent = es_fixtures_file.read()
        reqES = urllib.request.Request('http://es:9200/_bulk', data=fileContent, method='POST')
        reqES.add_header('Content-Type', 'application/x-ndjson/')
        try:
            respES_json = urllib.request.urlopen(reqES).read().decode('utf-8')
            break
        except:
            time.sleep(5)
            continue
    while True:
        task_consumer = KafkaConsumer("task_topic", group_id='listing_indexer'
                , bootstrap_servers=['kafka:9092'])
        for message in task_consumer:
            new_listing = json.loads((message.value).decode('utf-8'))
            if new_listing[1] == "coview":
                print("CONSUMING COVIEW MESSAGE")
                log_string = new_listing[0]['user'] + "," + new_listing[0]['task'] + "\n"
                print(log_string)
                with open('logfile.txt', 'a') as coview_log_file:
                    coview_log_file.write(log_string)
            else:
                one = es.index(index='tasktic', doc_type=new_listing[1], id=new_listing[0]['id']
                        , body=new_listing[0])
                two = es.indices.refresh(index='tasktic')
