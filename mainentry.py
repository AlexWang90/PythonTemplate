import os

import sys

from alexutil import stringutil
from test import elegant_code_style
from test.tts import test_gtts
from alexutil import configutil
from alexutil.logutil import LogUtil
from test import test_except
from test import test_tqdm
from alexutil import dateutil

# 获取当前路径并添加到系统path
# cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(cwd)
# os.chdir(cwd)

logger = LogUtil()
def test_config():
    print("test config..............")
    print(os.path.join(os.getcwd(),"resource\myconfig"))
    path = os.path.join(os.getcwd(),"resource\myconfig")
    print(configutil.get_value(path, "db", "db_user"))
    print(len(configutil.get_value(path, "db", "db_user")))

    configutil.set_value(path, 'timerecord', 'start_time', dateutil.current_date_format())

def test_log():
    logger.info("test_logger_info")
    logger.error("test_logger_error")
    logger.debug("test_logger_debug")
    logger.warning("test_logger_warning")

if __name__ == "__main__":
    print(os.getcwd()) #取的是起始执行目录

    stringutil.test()
    # test_gtts.test()
    test_config()

    elegant_code_style.ifelse(130)
    elegant_code_style.test_cnumerate()
    elegant_code_style.test_zip()
    elegant_code_style.test_join()
    # test_log()
    test_except.test()
    test_tqdm.test()

    # 测试args  method = sys.argv[1].strip()
    if len(sys.argv) > 1:
        method = sys.argv[1].strip()
        if method == 'mproc':
            # main_parallel()
            print(method)