# -*- coding:utf-8 -*-

import codecs
import time

__author__ = 'Gree-gorey'

t1 = time.time()

output = []

with codecs.open('dict.opcorpora.txt', 'r', 'utf-8') as f:
    for line in f:
        line = line.rstrip().split('\t')
        for item in line:
            if 'CONJ' in item:
                output.append(line[0].lower())

with codecs.open('output.csv', 'w', 'utf-8') as w:
    for line in output:
        w.write(line + '\n')

t2 = time.time()

print(t2 - t1)
