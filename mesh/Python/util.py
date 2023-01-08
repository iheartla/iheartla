import numpy as np


def permute_rvector(source):
    if len(source) > 0:
        min_index = 0
        cur_val = source[0]
        for i in range(1, len(source)):
            if source[i] < cur_val:
                cur_val = source[i]
                min_index = i
        if min_index != 0:
            res = np.zeros(len(source))
            for i in range(len(source)):
                res[i] = source[(i + min_index) % len(source)]
            return res
    return source


def compare_vec(fir, sec):
    less = True
    for i in range(len(fir)):
        if fir[i] != sec[i]:
            if fir[i] > sec[i]:
                less = False
            break
    return less


def swap(source, i, j):
    for k in range(source.shape[1]):
        tmp = source[i, k]
        source[i, k] = source[j, k]
        source[j, k] = tmp


def swap_vector(source, i, j):
    tmp = source[i]
    source[i] = source[j]
    source[j] = tmp


def partition(source, start, end):
    pivot = source[end, :]
    i = start - 1
    for j in range(start, end):
        cur = source[j, :]
        if compare_vec(cur, pivot):
            i = i + 1
            swap(source, i, j)
    swap(source, i + 1, end)
    return i + 1


def partition_vector(source, start, end):
    pivot = source[end]
    i = start - 1
    for j in range(start, end):
        if source[j] < pivot:
            i = i + 1
            swap_vector(source, i, j)
    swap_vector(source, i + 1, end)
    return i + 1


def quick_sort(source, start, end):
    if start >= end:
        return
    p = partition(source, start, end)
    quick_sort(source, start, p - 1)
    quick_sort(source, p + 1, end)


def quick_sort_vector(source, start, end):
    if start >= end:
        return
    p = partition_vector(source, start, end)
    quick_sort_vector(source, start, p - 1)
    quick_sort_vector(source, p + 1, end)


def sort_matrix(source):
    quick_sort(source, 0, source.shape[0] - 1)
    return source


def sort_vector(source):
    quick_sort_vector(source, 0, len(source) - 1)
    return source


def remove_duplicate_rows(source):
    if source.shape[0] == 0:
        return source
    output = np.zeros(source.shape)
    cur = source[0, :]
    output[0, :] = cur
    cnt = 1
    for j in range(source.shape[0] - 1):
        if np.array_equal(cur, source[j + 1, :]):
            continue
        else:
            cur = source[j + 1, :]
            output[cnt, :] = cur
            cnt += 1
    # output.resize((cnt, source.shape[1]))
    return output[:cnt, :]


def preprocess_matrix(source):
    new_source = np.zeros(source.shape)
    for i in range(source.shape[0]):
        new_source[i, :] = permute_rvector(source[i, :])
    return remove_duplicate_rows(sort_matrix(new_source))


if __name__ == '__main__':
    P = np.asarray([[1, 31, 4], [1, 3, 1], [1, 1, 1], [31, 4, 1]])
    # P = np.asarray([[1, 31, 1], [1, 3, 1], [1, 1, 1], [31, 1, 1]])
    print(sort_matrix(P))
    # print(sort_vector([3, 2, 1, 1, 3]))