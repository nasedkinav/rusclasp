# -*- coding:utf-8 -*-

import time
from structures import Corpus

__author__ = 'gree-gorey'


def main():
    t1 = time.time()

    new_corpus = Corpus('/home/gree-gorey/CorpusTest/')

    for text in new_corpus.texts('txt'):

        text.write_dummy_ann()

        text.copy_into_brat('/opt/brat-v1.3_Crunchy_Frog/data/left/', True)

    t2 = time.time()

    print(t2 - t1)


if __name__ == '__main__':
    main()
