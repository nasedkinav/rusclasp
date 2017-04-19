# -*- coding:utf-8 -*-

import codecs
import json


def create(type_of):
    var = ['predicates',  # 0
           'inserted',  # 1
           'complimentizers',  # 2
           'prepositions',  # 3
           'inserted_evidence',  # 4
           'complex_complimentizers',  # 5
           'specificators']  # 6
    result = None
    with codecs.open(var[type_of] + '.csv', 'r', 'utf-8') as f:
        if type_of == 1:
            result = {}
            for line in f:
                line = line.rstrip()
                words = line.split(' ')
                if words[0] in result:
                    result[words[0]].append(line)
                else:
                    result[words[0]] = [line]
        if type_of == 5:
            result = {}
            for line in f:
                line = line.rstrip()
                words = line.split(' ')
                # result[words[0]] = [line, len(words)]
                if words[0] in result:
                    result[words[0]].append([line, len(words)])
                else:
                    result[words[0]] = [[line, len(words)]]
        elif type_of == 2 or type_of == 0 or type_of == 4 or type_of == 6:
            result = []
            for line in f:
                line = line.rstrip()
                result.append(line)
        elif type_of == 3:
            result = {}
            for line in f:
                line = line.rstrip()
                result[line[0]] = line[1].split(',')
    return var[type_of] + '.json', result

name, res = create(5)

w = codecs.open(name, 'w', 'utf-8')
json.dump(res, w, ensure_ascii=False, indent=2)
w.close()
