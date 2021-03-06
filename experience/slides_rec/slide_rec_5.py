# coding: utf-8
"""
Created by Alex Wang on 2019-03-17
"""
import os
import sys
import traceback

import numpy as np
import time
from datetime import datetime

import tensorflow as tf
import tensorlayer as tl

slim = tf.contrib.slim

from slide_rec.slide_rec_config import FLAGS, CLIP_LENGTH, CROP_SIZE, CROP_SIZE, CHANNEL_NUM
import resnet_v1_p3d
from slide_rec.data_preprocess import shot_data_prepare_optical_max_5

init_learning_rate = FLAGS.learning_rate
decay_step = FLAGS.decay_step
decay_rate = 0.95


class ImgtoolkitVideo():

    def construct_network(self, frame_feat_input, batch_labels, weights, reuse, is_training):
        with slim.arg_scope(resnet_v1_p3d.resnet_arg_scope()):
            model, end_points = resnet_v1_p3d.resnet_v1_50_v1(inputs=frame_feat_input,
                                                                 num_classes=self.num_classes,
                                                                 is_training=is_training,
                                                                 dropout_rate=FLAGS.dropout_rate,
                                                                 reuse=reuse)
        logits = end_points['logits']
        with tf.name_scope('loss'):
            cost = tf.reduce_mean(
                tf.losses.sparse_softmax_cross_entropy(logits=logits, labels=batch_labels,
                                                       weights=weights))

        L2_frame = 0
        for w in tl.layers.get_variables_with_name('resnet_v1_50', True, True):
            L2_frame += tf.contrib.layers.l2_regularizer(1.0)(w)

        # loss = 10 * cost + 0.0001 * L2_frame  # save-4500-0.8125  0.7499
        loss = cost + FLAGS.l2_weight * L2_frame   # FLAGS.l2_weight= 0.0001 is good
        with tf.name_scope('accuracy'):
            predict_index = tf.argmax(logits, 1)
            predicts = tf.equal(predict_index, batch_labels)
            accuracy = tf.reduce_mean(tf.cast(predicts, np.float32))
            tf.summary.scalar('accuracy', accuracy)

        end_point = {'L2_frame': L2_frame, 'loss': loss, 'cost': cost, 'accuracy': accuracy,
                     'logits': logits, 'predict': predict_index}
        return end_point

    def print_graph(self):
        bytes_num = 0
        operations = tf.get_default_graph().get_operations()
        for operation in operations:
            print("Operation:{}".format(operation.name))
            for k in operation.inputs:
                try:
                    print("{} Input: {}  {}".format(operation.name, k.name, k.get_shape()))
                    shape_list = []
                    for item in k.get_shape().as_list():
                        if item:
                            shape_list.append(item)
                        else:
                            shape_list.append(self.read_batch_size)
                    temp_bytes_num = int(np.prod(shape_list))
                    if temp_bytes_num > bytes_num:
                        bytes_num = temp_bytes_num
                except Exception as e:
                    traceback.print_exc()
            for k in operation.outputs:
                print("{} Output:{}".format(operation.name, k.name))
            print("\n")
            print('bytes_num:{}'.format(bytes_num))

    def build_graph(self):
        self.batch_clips = tf.placeholder(tf.float32,
                                          [None, 4, CROP_SIZE, CROP_SIZE, CHANNEL_NUM],
                                          name='input')
        self.batch_labels = tf.placeholder(tf.int64, (None), name='label')
        self.weights = tf.placeholder(tf.float32, (None), name='weight')
        self.keep_prob = tf.placeholder(tf.float32)
        self.global_step = tf.Variable(0, name="global_step", trainable=False)

        self.train_nets = self.construct_network(self.batch_clips, self.batch_labels,
                                                 self.weights, False, True)
        self.valid_nets = self.construct_network(self.batch_clips, self.batch_labels,
                                                 self.weights, True, False)

        self.learning_rate = tf.train.exponential_decay(init_learning_rate, self.global_step,
                                                        decay_step, decay_rate,
                                                        staircase=True)
        optimizer = tf.train.AdamOptimizer(self.learning_rate, beta1=0.9, beta2=0.999, epsilon=1e-08,
                                           use_locking=False)
        self.train_op = slim.learning.create_train_op(self.train_nets['loss'], optimizer, self.global_step)
        self.update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        self.saver = tf.train.Saver(max_to_keep=1000)
        self.summary_op = tf.summary.merge_all()


def main(_):
    ps_hosts = FLAGS.ps_hosts.split(",")
    worker_hosts = FLAGS.worker_hosts.split(",")
    worker_number = len(worker_hosts)
    table_pattern = FLAGS.tables.split(',')
    train_table, valid_table = table_pattern[0], table_pattern[1]
    print table_pattern

    # Create a cluster from the parameter server and worker hosts.
    cluster = tf.train.ClusterSpec({"ps": ps_hosts, "worker": worker_hosts})

    # Create and start a server for the local task.
    config = tf.ConfigProto(inter_op_parallelism_threads=32)
    server = tf.train.Server(cluster,
                             job_name=FLAGS.job_name,
                             task_index=FLAGS.task_index,
                             config=config)
    if FLAGS.job_name == "ps":
        server.join()
    elif FLAGS.job_name == "worker":
        with tf.device('/job:worker/task:%d' % FLAGS.task_index):
            filename_queue = tf.train.string_input_producer(
                [train_table],
                num_epochs=FLAGS.num_epochs)
            filename_queue_test = tf.train.string_input_producer(
                [valid_table],
                num_epochs=FLAGS.num_epochs)

        with tf.device(tf.train.replica_device_setter(
                worker_device='/job:worker/task:%d' % FLAGS.task_index,
                cluster=cluster)):

            model = ImgtoolkitVideo(worker_number)
            model.read_record(filename_queue, valid=False)
            model.read_record(filename_queue_test, valid=True)
            model.build_graph()

        config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=True)
        config.gpu_options.allow_growth = True

        hooks = [tf.train.StopAtStepHook(last_step=2000000000000000000000)]
        init_op = [tf.global_variables_initializer(),
                   tf.local_variables_initializer()]

        def get_session(sess):
            session = sess
            while type(session).__name__ != 'Session':
                session = session._sess
            return session

        good_model_num = 0
        with tf.train.MonitoredTrainingSession(master=server.target,
                                               checkpoint_dir=FLAGS.checkpointDir,
                                               save_checkpoint_secs=100,
                                               save_summaries_steps=None,
                                               save_summaries_secs=None,
                                               is_chief=(FLAGS.task_index == 0),
                                               hooks=hooks) as sess:
            sess.run(init_op)
            summary_writer = tf.summary.FileWriter(FLAGS.checkpointDir)

            print('[{}] start to train... '.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            total_acc = 0.0
            total_loss = 0.0
            step = 0
            test_step = 0
            while step < FLAGS.train_steps:
                # wait to get train data
                step = step + 1
                start_1 = time.time()
                frames_batch, batch_labels, video_ids = shot_data_prepare_optical_max_5(batch_data)
                end_1 = time.time()
                feed_dict = {}
                feed_dict[model.batch_clips] = frames_batch
                feed_dict[model.batch_labels] = batch_labels
                feed_dict[model.keep_prob] = FLAGS.keep_prob
                feed_dict[model.weights] = [FLAGS.pos_weight if label == 1 else 1.0
                                            for label in batch_labels]

                run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
                run_metadata = tf.RunMetadata()
                start_2 = time.time()
                _, _, _, learning_rate_val, summary, end_point = sess.run(
                    [model.train_op, model.update_ops, model.global_step,
                     model.learning_rate, model.summary_op, model.train_nets], feed_dict=feed_dict,
                    options=run_options, run_metadata=run_metadata)
                end_2 = time.time()
                accuracy = end_point['accuracy']
                loss = end_point['loss']
                cost = end_point['cost']
                total_acc = total_acc + accuracy
                total_loss = total_loss + loss

                if step % 20 == 0:
                    print("")
                    print('[{}] [Train] step = {} loss = {:.6f}, cost:{:.6f}, L2_loss:{:.4f}, '
                          'acc = {:.4f}, learning_rate:{:.8f}, decay_step:{}'.format(
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'), step, loss, cost,
                        end_point['L2_frame'], accuracy, learning_rate_val, decay_step))
                    print('length of batch_data:{}, frame_num of one shot:{},'
                          ' data prepare time:{:.4f}, session run time:{:.4f}'.
                          format(len(batch_data), len(batch_data[0]),
                                 end_1 - start_1, end_2 - start_2))
                    data_0 = batch_data[0][0]
                    print('video_id:{}, shot_id:{}, frame_id:{}, image shape:{}, label:{}, video_ids:{}'.format(
                        data_0['video_id'], data_0['shot_id'], data_0['frame_id'],
                        data_0['frame'].shape, batch_labels[0:8], video_ids[0:8]))

                if step % 100 == 0:
                    summary_writer.add_run_metadata(run_metadata, 'step%d' % step)
                    summary_writer.add_summary(summary, step)
                    summary_writer.flush()
                    # wait to get test data
                    total_acc_test = 0.0
                    total_loss_test = 0.0
                    label_list = []
                    predict_list = []
                    video_ids_list = []

                    test_batch_num = 10
                    for i in range(test_batch_num):
                        if i == 0:
                            print('[test] length of batch_data_test:{}, frame_num of one shot:{}'.
                                  format(len(batch_data_test), len(batch_data_test[0])))
                            data_0 = batch_data_test[0][0]
                            print('[test] video_id:{}, shot_id:{}, frame_id:{}, image shape:{}, label:{}'.
                                  format(data_0['video_id'], data_0['shot_id'], data_0['frame_id'],
                                         data_0['frame'].shape, data_0['label']))

                        frames_batch_test, batch_labels_test, video_ids_test = \
                            shot_data_prepare_optical_max_5(batch_data_test)
                        test_step = test_step + 1
                        feed_dict = {}
                        feed_dict[model.batch_clips] = frames_batch_test
                        feed_dict[model.batch_labels] = batch_labels_test
                        feed_dict[model.keep_prob] = 1.0
                        feed_dict[model.weights] = [1.0 for label in batch_labels_test]

                        end_point_valid = sess.run(model.valid_nets, feed_dict=feed_dict)
                        acc_valid = end_point_valid['accuracy']
                        loss_valid = end_point_valid['loss']
                        total_acc_test = total_acc_test + acc_valid
                        total_loss_test = total_loss_test + loss_valid

                        label_list.extend(batch_labels_test)
                        predict_list.extend(end_point_valid['predict'])
                        video_ids_list.extend(video_ids_test)

                    print('script file:{}, dropout_rate:{}, oss:{}'.format(os.path.basename(__file__), FLAGS.dropout_rate, FLAGS.checkpointDir))
                    print('[{}] [valid] step = {} test_loss = {:.6f}, test_acc = {:.4f}'.format(
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        step, total_loss_test / test_batch_num, total_acc_test / test_batch_num))
                    print('label:{}'.format(label_list[0:64]))
                    print('predict:{}'.format(predict_list[0:64]))
                    # print('video_ids:{}'.format(video_ids_list[0:16]))

                    test_acc = total_acc_test / test_batch_num
                    if test_acc >= 0.79:
                        # save model
                        print("[{}] Start to save model to oss...".format(
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                        ckp_path = os.path.join(FLAGS.checkpointDir, 'good_models',
                                                'save-{}-{}'.format(step, test_acc))
                        save_path = model.saver.save(get_session(sess), ckp_path)
                        good_model_num += 1
                        print("[{}] Model save finished, saved path is {}, good model num:{}".format(
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), save_path, good_model_num))


            model.is_train_end = True

            print('[{}] train end '.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


if __name__ == '__main__':
    tf.app.run()
