# coding: utf-8
"""
Created by Alex Wang
On 20170922
"""
import os
import shutil

def get_basename(path):
    """
    获取路径的最后一部分
    :return:
    """
    return os.path.basename(path)

def dir_clear(dir_path):
    """
    清空一个目录
    :param dir_path:
    :return:
    """
    # for file in os.listdir(dir_path):
    #     if os.path.isfile(os.path.join(dir_path,file)):
    #         os.remove(os.path.join(dir_path,file))
    for the_file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):  # 递归删除目录
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def list_dirs(path):
    """
    列出当前目录下的所有目录
    :param path:
    :return:
    """
    dir_abs_list = [] # 绝对路径
    dir_list = []  # 相对路径
    for file in os.listdir(path):
        abs_file_path = os.path.join(path, file)
        if os.path.isdir(abs_file_path):
            dir_abs_list.append(abs_file_path)
            dir_list.append(file)
    return dir_abs_list, dir_list

def list_files(path):
    """
    列出当前目录下的所有文件（非目录）
    :param path:
    :return:
    """
    file_abs_list = [] # 绝对路径
    file_list = []  # 相对路径
    for file in os.listdir(path):
        abs_file_path = os.path.join(path, file)
        if os.path.isfile(abs_file_path):
            file_abs_list.append(abs_file_path)
            file_list.append(file)
    return file_abs_list, file_list

def dir_exist(dir_path):
    """
    判断目录是否存在
    :param dir_path:
    :return:
    """
    if os.path.isdir(dir_path):
        return True
    else:
        return False

def file_exist(file_path):
    """
    判断文件（非目录）是否存在
    :param file_path:
    :return:
    """
    if os.path.isfile(file_path):
        return True
    else:
        return False

def mkdir_if_not_exist(dir_name):
    """
    创建目录
    Python 3.2+
    :param dir_name:
    :return:
    """
    os.makedirs(dir_name, exist_ok=True)

def recreate_dir(dir_name):
    """
    重新创建目录
    如果目录存在, 清空目录后创建新目录
    如果目录不存在, 创建新目录
    :param dir_name:
    :return:
    """
    if dir_exist(dir_name):
        dir_clear(dir_name)
    mkdir_if_not_exist(dir_name)

def test_current_dir():
    print(os.getcwd()) ##当前目录
    print(os.path.abspath(__file__)) ##当前文件
    cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  ##当前目录的上一级
    print(cwd)

if __name__ == "__main__":
    print("__main__")
    print(get_basename('http://flv3.bn.netease.com/videolib3/1707/24/HhsvJ4943/HD/HhsvJ4943-mobile.mp4'))

    dir_abs_list, dir_list = list_dirs('E://workspace/gitlab')
    print(", ".join(dir_abs_list))
    print(", ".join(dir_list))

    file_abs_list, file_list = list_files('E://workspace/gitlab')
    print(", ".join(file_abs_list))
    print(", ".join(file_list))

    test_current_dir()
    mkdir_if_not_exist('E://workspace/tmp/test_python_mkdir')