"""
Created by Alex Wang on 2018-04-25
download split images from tfs

Data prepare:
    tunnel download -fd '\t' -limit 5000 search_offline.image_split_result_alexwang /Users/alexwang/data/image_split/image_split_alexwang.txt;
"""
import os
import random
from multiprocessing.dummy import Pool as ThreadPool

import shutil
from util.download_tfs_image import image_download_tuple


def parse_and_download_images():
    """
    :return:
    """
    file_name = '/Users/alexwang/data/image_split/image_split_alexwang.txt'
    save_dir = '/Users/alexwang/data/image_split/image_split_filter_result'

    if os.path.isdir(save_dir):
        # os.remove(save_dir)
        shutil.rmtree(save_dir)
    os.makedirs(save_dir)

    index = 0
    url_path_tuple_list = []
    for line in open(file_name, 'r'):
        elems = line.split('\t')
        org_image_name = elems[2]
        split_image_name = elems[3]

        url_one = 'http://img01.taobaocdn.com/bao/uploaded/' + org_image_name
        url_two = 'http://img01.taobaocdn.com/bao/uploaded/' + split_image_name
        path_one = os.path.join(save_dir, org_image_name)
        comma_index = org_image_name.rfind('.')
        prefix = org_image_name[0:comma_index]
        postfix = org_image_name[comma_index:]
        path_two = os.path.join(save_dir, '{}_{}{}'.format(prefix, index, postfix))
        print('path_one:', path_one)
        print('path_two:', path_two)
        index += 1

        # url_path_tuple_list.append((url_one, path_one))
        url_path_tuple_list.append((url_two, path_two))

    pool = ThreadPool(100)
    pool.map(image_download_tuple, url_path_tuple_list)
    pool.close()
    pool.join()


if __name__ == '__main__':
    parse_and_download_images()