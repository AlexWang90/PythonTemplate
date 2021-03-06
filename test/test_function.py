'''
Created on 2017-5-18
@author: Alex Wang
'''


def devide(a, b):
    try:
        return a / b
    except Exception as e:
        print(e.__str__())
        return None


def test_none():
    if devide(0, 2) is None:
        print(devide(0, 2))
        print("devide(0,2) is None")

    if devide(2, 0) is None:
        print("devide(2,0) is None")


def arg_num_wunknow(*args, **kwargs):
    for arg in args:
        print("arg:" + str(arg))
    for key in kwargs:
        print("kwargs:" + key + "\t" + kwargs[key])


def test_arguments(name, age, school=None):
    """
    use tuple and dict as arguments
    """
    print('name:{}, age:{}, school:{}'.format(name, age, school))


if __name__ == "__main__":
    test_none()
    if 0 is None:
        print("0 is None")
    arg_num_wunknow(45, 23, "abc", karg_one="one", karg_two="two")

    # use tuple and dict as arguments
    tuple_args_1 = ('Alex Wang', 18, 'SDU')
    tuple_args_2 = ('Alex Wang', 19)
    dict_args = {'name':'Alex Wang', 'age':20}
    test_arguments(*tuple_args_1)
    test_arguments(*tuple_args_2)
    test_arguments(**dict_args)
