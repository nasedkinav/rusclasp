# -*- coding:utf-8 -*-

import os
import codecs
import json
import copy
from pymystem3 import Mystem
import treetaggerwrapper

__author__ = u'Gree-gorey'

m = Mystem(grammar_info=True, disambiguation=True, entire_input=True)
t = treetaggerwrapper.TreeTagger(TAGLANG=u'ru')

prepositions = json.load(codecs.open(u'./data/prepositions.json', u'r', u'utf-8'))
complimentizers = json.load(codecs.open(u'./data/complimentizers.json', u'r', u'utf-8'))
inserted = json.load(codecs.open(u'./data/inserted.json', u'r', u'utf-8'))


class Corpus:
    def __init__(self, path):
        self.path = path

    def texts(self, extension):
        for root, dirs, files in os.walk(self.path):
            for filename in files:
                if extension in filename:
                    open_name = self.path + filename
                    f = codecs.open(open_name, u'r', u'utf-8')
                    if extension == u'json':
                        result = json.load(f)
                    else:
                        result = f.read()
                    f.close()
                    yield Text(result, open_name)

# /home/gree-gorey/Corpus/
# /opt/brat-v1.3_Crunchy_Frog/data/right/collection/'


class Text:
    def __init__(self, result, path):
        self.result = result
        self.path = path
        self.sentences = []
        self.sentence = False
        self.analysis = None

    def mystem_analyzer(self):
        self.result = self.result.replace(u' ', u' ')
        self.analysis = m.analyze(self.result)
        position = 0
        if self.analysis[-1][u'text'] == u'\n':
            del self.analysis[-1]
        for token in self.analysis:
            token[u'begin'] = position
            position += len(token[u'text'])
            token[u'end'] = position

    def treetagger_analyzer(self):
        self.result = self.result.replace(u' ', u' ')
        self.analysis = t.tag_text(self.result, tagblanks=True)
        position = 0
        new_analysis = []
        for token in self.analysis:
            if token[0] == u'<':
                # new_token[u'text'], new_token[u'gr'], new_token[u'lex'] = None, u'SPACE', None
                position += 1
            else:
                new_token = {u'begin': position}
                new_token[u'text'], new_token[u'gr'], new_token[u'lex'] = token.split(u'\t')
                position += len(new_token[u'text'])
                new_token[u'end'] = position
                new_analysis.append(new_token)
        self.analysis = new_analysis

    def sentence_on(self):
        if not self.sentence:
            self.sentence = True
            self.sentences.append(Sentence())

    def sentence_off(self):
        if self.sentence:
            self.sentence = False

    def sentence_splitter(self):
        for i in xrange(len(self.result)):
            self.sentence_on()
            self.add_token(self.result[i]) if i == len(self.result)-1 else self.add_token(self.result[i],
                                                                                            self.result[i+1])
            if self.end_of_sentence():
                self.sentence_off()
        self.sentence_off()

    def end_of_sentence(self):
        if self.sentences[-1].tokens[-1].pos == u'PERIOD':  # if it is a period
            if self.sentences[-1].tokens[-1].next_token_title:  # if the next token is uppercase
                if self.sentences[-1].tokens[-1].after_abbreviation:  # if the previous one is abbreviation
                    if self.sentences[-1].tokens[-1].next_token_name:  # if the next one in a name
                        if self.sentences[-1].tokens[-1].after_name:  # if one of the previous five tokens is a name
                            return True
                        else:
                            return False
                    else:
                        return True
                else:
                    return True
            else:
                return False
        return False

    def after_name(self):
        if self.sentences[-1].after_name[0]:
            if self.sentences[-1].after_name[1] <= 5:
                self.sentences[-1].tokens[-1].after_name = True
            else:
                self.sentences[-1].after_name = [False, 0]
            self.sentences[-1].after_name[1] += 1
        if len(self.sentences[-1].tokens[-1].pos) > 1:
            if self.sentences[-1].tokens[-1].pos[1] == u'p':
                self.sentences[-1].after_name[0] = True
        if self.sentences[-1].tokens[-1].pos == u'-':
            if self.sentences[-1].tokens[-1].content[0].isalpha() and u'.' in self.sentences[-1].tokens[-1].content:
                self.sentences[-1].after_abbreviation = True
        else:
            self.sentences[-1].after_abbreviation = False

    def add_punctuation(self, token, next_token):
        if token[u'gr'] == u',':
            self.sentences[-1].tokens[-1].pos = u'COMMA'
            if len(self.sentences[-1].tokens) > 1:
                if self.sentences[-1].tokens[-2].content[-1].isdigit():
                    if next_token is not None:
                        if next_token[u'text'][0].isdigit():
                            self.sentences[-1].tokens[-1].pos = u'pseudoCOMMA'
        elif token[u'gr'] == u'-':
            if token[u'lex'] in u'-:;—':
                self.sentences[-1].tokens[-1].pos = u'COMMA'
            elif token[u'lex'] in u'()':
                self.sentences[-1].tokens[-1].pos = u'pairCOMMA'
            else:
                self.sentences[-1].tokens[-1].pos = u'UNKNOWN'
                self.sentences[-1].tokens[-1].lex = token[u'lex']
        elif token[u'gr'] == u'SENT':
            self.add_period(next_token)

    def add_period(self, next_token):
        self.sentences[-1].tokens[-1].pos = u'PERIOD'
        if self.sentences[-1].after_abbreviation:
            self.sentences[-1].tokens[-1].after_abbreviation = True
        if next_token is not None:
            if next_token[u'text'].istitle() or next_token[u'text'] == u'\"':
                self.sentences[-1].tokens[-1].next_token_title = True
                if next_token[u'gr'][0] == u'N':
                    if next_token[u'gr'][1] == u'p':
                        self.sentences[-1].tokens[-1].next_token_name = True
                elif next_token[u'gr'] == u'-':
                    self.sentences[-1].tokens[-1].next_token_title = False

    def add_word(self, token, next_token):
        if token[u'gr'] == u'Afpmpaf':
            if u'.' in token[u'text']:
                if token[u'text'][:-1:].isdigit():
                    self.sentences[-1].tokens[-1].pos = u'M'
                    self.sentences[-1].tokens[-1].end -= 1
                    self.sentences[-1].tokens.append(Token())
                    self.sentences[-1].tokens[-1].begin = self.sentences[-1].tokens[-2].end
                    self.sentences[-1].tokens[-1].end = self.sentences[-1].tokens[-1].begin + 1
                self.add_period(next_token)
            else:
                self.sentences[-1].tokens[-1].pos = token[u'gr']
                self.sentences[-1].tokens[-1].lex = token[u'lex']
        else:
            self.sentences[-1].tokens[-1].pos = token[u'gr']
            self.sentences[-1].tokens[-1].lex = token[u'lex']

    def add_token(self, token, next_token=None):
        self.sentences[-1].tokens.append(Token())
        self.sentences[-1].tokens[-1].begin = token[u'begin']
        self.sentences[-1].tokens[-1].end = token[u'end']
        self.sentences[-1].tokens[-1].content = token[u'text']
        if token[u'gr'][0].isalpha() and token[u'gr'] != u'SENT':
            self.add_word(token, next_token)
        else:
            self.add_punctuation(token, next_token)
        self.after_name()

    def write_clause_ann(self):
        i = 0
        j = 0

        write_name = self.path.replace(u'json', u'ann')
        # write_name = self.path.replace(u'txt', u'ann')
        w = codecs.open(write_name, u'w', u'utf-8')

        # for token in self.analysis:
        #     i += 1
        #     line = u'T' + str(i) + u'\t' + u'Base ' + str(token[u'begin']) + u' ' + str(token[u'end']) + u'\t' + u'\n'
        #     w.write(line)

        # for sentence in self.sentences:
        #     i += 1
        #     line = u'T' + str(i) + u'\t' + u'Base ' + str(sentence.tokens[0].begin) + u' '\
        #            + str(sentence.tokens[-1].end) + u'\t' + u'\n'
        #     w.write(line)

        for sentence in self.sentences:
            # for pair in sentence.pp:
            #     # print sentence.tokens[pair[0]].begin, sentence.tokens[pair[1]].end
            #     i += 1
            #     line = u'T' + str(i) + u'\t' + u'Base ' + str(sentence.tokens[pair[0]].begin) + u' ' + str(sentence.tokens[pair[1]].end) + u'\t' + u'\n'
            #     w.write(line)
            for span in sentence.spans:
                # i += 1
                # line = u'T' + str(i) + u'\t' + u'Base ' + str(span.begin) + u' ' + str(span.end) + u'\t' + u'\n'
                # w.write(line)
                if span.embedded:
                    # if span.embedded_type == u'gerund':
                    i += 1
                    line = u'T' + str(i) + u'\t' + u'Embedded ' + str(span.begin) + u' ' + str(span.end) + u'\t' + u'\n'
                    w.write(line)
                elif span.inserted:
                    i += 1
                    line = u'T' + str(i) + u'\t' + u'Inserted ' + str(span.begin) + u' ' + str(span.end) + u'\t' + u'\n'
                    w.write(line)
                # elif span.base:
                # elif not span.in_embedded:
                #     i += 1
                #     line = u'T' + str(i) + u'\t' + u'Base ' + str(span.begin) + u' ' + str(span.end) + u'\t' + u'\n'
                #     w.write(line)
                span.entity_number = i
            for r in sentence.relations:
                j += 1
                line = u'R' + str(j) + u'\t' + u'Split Arg1:T' + str(sentence.spans[r[0]].entity_number) +\
                       u' Arg2:T' + str(sentence.spans[r[1]].entity_number) + u'\t' + u'\n'
                w.write(line)

        w.close()

    def write_pos_ann(self):
        name = self.path[:-3:] + u'json'
        w = codecs.open(name, u'w', u'utf-8')
        json.dump(self.analysis, w, ensure_ascii=False, indent=2)
        w.close()


class Sentence:
    def __init__(self):
        self.tokens = []
        self.spans = []
        self.chunks = []
        self.relations = []
        self.np = []
        self.pp = []
        self.after_name = [False, 0]
        self.after_abbreviation = False
        self.span = False

    def contain_structure(self):
        for token in self.tokens:
            for var in token.inflection:
                if u'деепр' in var:
                    return True

    def add_token(self, token):
        self.spans[-1].tokens.append(token)

    def span_on(self, token):
        if not self.span:
            self.span = True
            self.spans.append(Span())

    def span_off(self):
        if self.span:
            self.span = False
            self.spans[-1].tokens.pop()
            if len(self.spans[-1].tokens) < 1:
                self.spans.pop()
            # self.spans[-1].content = u''.join(self.spans[-1].tokens)

    def span_splitter(self):
        for token in self.tokens:
            if token.content != u'\"':
                self.span_on(token)
                self.add_token(token)
            if token.end_of_span():
                self.span_off()
            elif token.content != u'\"':
                self.span_on(token)
        self.span_off()

    def eliminate_pair_comma(self):
        predicate = False
        begin = False
        end = False
        for i in xrange(len(self.tokens)):
            if self.tokens[i].pos == u'pairCOMMA' and not begin:
                left = i
                begin = True
                end = False
            elif self.tokens[i].pos[0] == u'V' and begin:
                predicate = True
            elif self.tokens[i].pos == u'pairCOMMA' and begin:
                right = i
                end = True
                begin = False
                predicate = False
            if begin and end and predicate:
                self.tokens[left].pos = self.tokens[right].pos = u'COMMA'

    def restore_embedded(self):
        for j in xrange(len(self.spans)-1, -1, -1):
            if self.spans[j].embedded:
                last_added = j
                last_connected = j
                for k in xrange(j+1, len(self.spans)):
                    if not self.spans[k].embedded and not self.spans[k].in_embedded and not self.spans[k].inserted:
                        # print self.spans[k].tokens[0].content
                        if self.spans[k].accept_embedded(self.spans[j]):
                            if k != last_added + 1:
                                if k != last_connected + 1:
                                    self.spans[k].embedded = True
                                    self.spans[k].embedded_type = self.spans[j].embedded_type
                                    self.relations.append((last_connected, k))
                                    last_connected = k
                                else:
                                    self.spans[last_connected].tokens += self.spans[k].tokens
                                    self.spans[k].in_embedded = True
                                    last_added = k
                            else:
                                self.spans[j].tokens += self.spans[k].tokens
                                self.spans[k].in_embedded = True
                                last_added = k
                        else:
                            break

    def restore_base(self):
        for j in xrange(len(self.spans)):
            if not self.spans[j].embedded and not self.spans[j].in_embedded and not self.spans[j].in_base and not self.spans[j].inserted:
                self.spans[j].base = True
                # for k in xrange(j+1, len(self.spans)):
                #     if self.spans[k].accept_base():
                #         if k != j+1:
                #             self.spans[k].base = True
                #             self.relations.append((j, k))
                #         else:
                #             self.spans[j].tokens += self.spans[k].tokens
                #             self.spans[k].in_base = True

    def split_embedded(self):
        new_spans = []
        for span in self.spans:
            new_spans.append(span)
            find_2nd_gerund = False
            if span.embedded:
                if span.embedded_type == u'gerund':
                    if span.gerund > 1:
                        for i in xrange(len(span.tokens)-1, -1, -1):
                            if len(span.tokens[i].pos) > 2:
                                if span.tokens[i].pos[0] == u'V':
                                    if span.tokens[i].pos[2] == u'g':
                                        find_2nd_gerund = True
                            elif span.tokens[i].lex == u'и':
                                if find_2nd_gerund:
                                    if i > 0:
                                        new_span = Span()
                                        new_span.embedded = True
                                        new_span.embedded_type = u'gerund'
                                        for j in xrange(i, len(span.tokens)):
                                            new_span.tokens.append(span.tokens[j])
                                        new_spans[-1].tokens = span.tokens[:i:]
                                        new_spans.append(new_span)
                                        break
        self.spans = copy.deepcopy(new_spans)

    def find_np(self):
        match = -1
        for i in xrange(len(self.tokens)):
            if i > match:
                if not self.tokens[i].in_pp:
                    if self.tokens[i].is_adj():
                        # print self.tokens[i].content
                        for j in xrange(i+1, len(self.tokens)):
                            # print self.tokens[j].content
                            if not self.tokens[j].in_pp:
                                if not self.tokens[j].in_np:
                                    # self.tokens[j].in_pp = True
                                    if self.tokens[j].pos == u'S':
                                        if self.tokens[i].agree_adj_noun(self.tokens[j]):
                                            self.np.append([i, j])
                                            # print self.tokens[j].content
                                            for k in xrange(i, j+1):
                                                self.tokens[k].in_np = True
                                                match = j
                                            break

    def find_pp(self):
        for i in xrange(len(self.tokens)-1, -1, -1):
            if self.tokens[i].pos[0] == u'S':
                # print self.tokens[i].content
                for j in xrange(i+1, len(self.tokens)):
                    # print self.tokens[j].content
                    if not self.tokens[j].in_pp:
                        if self.tokens[j].pos[0] in u'NP':
                            if self.tokens[i].agree_pr_noun(self.tokens[j]):
                                self.pp.append([i, j])
                                for token in self.tokens[i: j+1]:
                                    token.in_pp = True
                                    if token.pos == u'COMMA':
                                        token.pos = u'pseudoCOMMA'
                                break
                                # print self.tokens[j].content

        # for pair in self.pp:
        #     print self.tokens[pair[0]].content, self.tokens[pair[1]].content

    def eliminate_and_disambiguate(self):
        pass
        # for pair in self.np:
        #     for token in self.tokens[pair[0]+1: pair[1]]:
        #         if token.pos == u'COMMA':
        #             token.pos = u'pseudoCOMMA'


class Span:
    def __init__(self):
        self.tokens = []
        self.begin = 0
        self.end = 0
        self.embedded = False
        self.in_embedded = False
        self.embedded_type = None
        self.base = False
        self.in_base = False
        self.inserted = False
        self.indicative = False
        self.gerund = 0
        # self.finite = False

    def type(self):
        if self.is_embedded():
            self.embedded = True

    def type_inserted(self):
        if self.is_inserted():
            self.inserted = True

    def is_inserted(self):
        if len(self.tokens) < 10:
            if self.tokens[0].lex == u'по':
                if len(self.tokens) > 2:
                    if self.tokens[1].content == u'словам' or self.tokens[1].content ==\
                            u'мнению' or self.tokens[2].content == u'словам':
                        return True
            if self.tokens[0].content.lower() in inserted:
                # print self.tokens[0].content.lower()
                content = u''
                for token in self.tokens:
                    content += token.content.lower()
                    content += u' '
                for var in inserted[self.tokens[0].content.lower()]:
                    if var == content[:-1:]:
                        return True

    def is_embedded(self):
        if not self.inserted:
            if self.tokens[0].pos == u'C':
                if self.tokens[0].lex in complimentizers:
                    self.embedded_type = u'complement'
                    return True
            for token in self.tokens:
                if token.lex == u'который':
                    self.embedded_type = u'relative'
                    return True
                if len(token.pos) > 2:
                    if token.pos[0] == u'V':
                        if token.pos[2] == u'g':
                            self.gerund += 1
                        elif token.pos[2] == u'i':
                            self.indicative = True
            if self.gerund > 0 and not self.indicative:
                self.embedded_type = u'gerund'
                return True

    def accept_embedded(self, other):
        if other.embedded_type == u'gerund':  # or self.embedded_type == u'participle':
            # print 0
            return self.infinite()
        elif other.embedded_type == u'relative' or other.embedded_type == u'complement':
            return not(self.finite() and other.finite())

    def infinite(self):
        for token in self.tokens:
            if len(token.pos) > 2:
                if token.pos[0] == u'V':
                    if token.pos[2] in u'imc':
                        return False
                elif token.pos[0] == u'N':
                    if token.pos[4] == u'n':
                        return False
        return True

    def finite(self):
        for token in self.tokens:
            if len(token.pos) > 2:
                if token.pos[0] == u'V':
                    if token.pos[2] in u'imc':
                        return True

    def accept_base(self):
        for token in self.tokens:
            if u'V' in token.pos:
                return True

    def get_boundaries(self):
        if self.tokens[0].content == u'\"':
            self.tokens.remove(self.tokens[0])
        self.begin = self.tokens[0].begin
        self.end = self.tokens[-1].end


class Token:
    def __init__(self):
        self.content = u''
        self.lex = u''
        self.pos = u''
        self.inflection = []
        self.gender = u''
        self.begin = 0
        self.end = 0
        self.after_name = False
        self.after_abbreviation = False
        self.next_token_title = False
        self.next_token_name = False
        self.in_pp = False
        self.in_np = False

    def end_of_span(self):
        return self.pos == u'COMMA'

    def agree_adj_noun(self, other):
        for varI in self.inflection:
            if other.gender in varI or u'мн' in varI:
                for varJ in other.inflection:
                    try:
                        if varJ[0] in varI and varJ[1] in varI:
                            return True
                    except:
                        print varJ[0], other.content

    def agree_pr_noun(self, noun):
        if noun.pos[0] == u'N':
            if self.pos[3] == noun.pos[4]:
                return True
        else:
            if self.pos[3] == noun.pos[5]:
                return True

    def is_adj(self):
        if self.pos == u'A':
            return True
        elif self.pos == u'V':
            for var in self.inflection:
                if u'прич' in var:
                    return True


def write_brat_ann(path):  # text, path):
    name = path[:-3:] + u'ann'
    w = codecs.open(name, u'w', u'utf-8')
    # i = 1
    # for sent in text.sentences:
    #     for pp in sent.pp:
    #         w.write(u'T' + str(i) + u'\tSpan ' + str(sent.tokens[pp[0]].begin) + u' ' + str(sent.tokens[pp[1]].end) +
    #                 u'\n')
    #         i += 1
    #     for np in sent.np:
    #         w.write(u'T' + str(i) + u'\tSpan ' + str(sent.tokens[np[0]].begin) + u' ' + str(sent.tokens[np[1]].end) +
    #                 u'\n')
    #         i += 1
    w.close()


def write_brat_sent(text, path):
    name = path[:-4:] + u'ann'
    w = codecs.open(name, u'w', u'utf-8')
    i = 1
    for sentence in text.sentences:
        w.write(u'T' + str(i) + u'\tSpan ' + str(sentence.tokens[0].begin) + u' ' + str(sentence.tokens[-2].end) +
                u'\t' + u'\n')
        i += 1
    w.close()

