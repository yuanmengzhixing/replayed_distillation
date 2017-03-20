import datetime as dt
import json
import os
import sys
import tensorflow as tf

from subprocess import check_output


def get_logger(f):
    if len(f.commit) == 0:
        print('No commit hash provided, using most recent on HEAD')
        f.commit = check_output(['git', 'rev-parse', 'HEAD'])

    if any(map(
        lambda x: x == 0,
        [len(f.run_name), len(f.dataset), len(f.model),
            len(f.procedure)])):
        print('No Run Name, Dataset, Model, or Procedure provided!')
        sys.exit(-1)

    log = {}
    log['run_file'] = 'train.py'
    log['start_time'] = dt.datetime.now().timestamp()
    log['end_time'] = None

    log['run_name'] = f.run_name
    log['commit'] = f.commit.decode('utf-8')
    log['dataset'] = f.dataset
    log['model'] = f.model
    log['rng_seed'] = f.rng_seed
    log['train_procedure'] = f.procedure

    log['epochs'] = f.epochs
    log['train_batch_size'] = f.train_batch_size
    log['test_batch_size'] = f.test_batch_size
    log['eval_interval'] = f.eval_interval
    log['checkpoint_interval'] = f.checkpoint_interval

    return log

def save_log(log, summary_folder, run_name, log_file):
    log['end_time'] = dt.datetime.now().timestamp()
    dirname = os.path.join(summary_folder, run_name)
    ensure_dir_exists(dirname)
    with open(os.path.join(dirname, log_file), 'w') as f:
        f.write(json.dumps(log))

def create_keep_probs():
    keep_prob_input = tf.placeholder(tf.float32, name='keep_prob_input')
    keep_prob = tf.placeholder(tf.float32, name='keep_prob')
    return keep_prob_input, keep_prob

def create_placeholders(input_size, output_size):
    inp = tf.placeholder(tf.float32, [None, input_size], name='inputs')
    labels = tf.placeholder(tf.float32, [None, output_size], name='outputs')
    return inp, labels

def create_train_ops(h, labels):
    with tf.variable_scope('xent'):
        loss = tf.reduce_mean(
                tf.nn.softmax_cross_entropy_with_logits(labels=labels, logits=h, name='sftmax_xent'))

    with tf.variable_scope('opt'):
        train_step = tf.train.AdamOptimizer().minimize(loss)

    return loss, train_step

def create_eval_ops(y, y_):
    with tf.variable_scope('eval'):
        correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

        y_dense = tf.where(tf.equal(y_, 1))[:,1]
        correct_top5 = tf.nn.in_top_k(y, y_dense, 5)
        top5_accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    return accuracy, top5_accuracy

def create_summary_ops(loss, accuracy, top5):
    loss_summary_op = tf.summary.scalar('loss', loss)
    accuracy_summary_op = tf.summary.scalar('accuracy', accuracy)
    top5_summary_op = tf.summary.scalar('top5 accuracy', top5)
    return tf.summary.merge_all()

def ensure_dir_exists(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

def get_sess_config(use_gpu=True):
    if use_gpu:
        return None
    else:
        return tf.ConfigProto(device_count={'GPU': 0})