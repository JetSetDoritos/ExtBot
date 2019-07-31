import sys
import os
import json
from threading import Thread

import extbot.extbot as extbot

if len(sys.argv) is 2: #config file is specified
    config_file = os.path.normpath(sys.argv[1])
else:
    config_file = os.path.join('.', 'data', 'config.json')

with open(config_file) as data_file:
    config = json.load(data_file)

extbot.initialize(
    bot_id=config['bot_id']
    )

refreshthread = Thread(target=extbot.schduled_tasks)
refreshthread.start()

extbot.listen(port=config['listening_port']) #blocking call