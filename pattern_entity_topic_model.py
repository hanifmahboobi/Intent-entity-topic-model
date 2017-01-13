__author__ = 'xiaolisong'

import random
import math
import sys
import csv
import operator

from query import query_sentence
import utility

PATTERN = 0
ENTITY = 1

class pattern_entity_model:

    def __init__(self, num_topic, num_of_iter, file):
        self.input_file = file
        self.mapping_file = 'mapping.txt'
        self.file_id = 'file_id.txt'
        self.file_result_pattern = 'pattern_word.csv'
        self.file_result_entity = 'entity_word.csv'
        self.file_result_classification = 'result.csv'
        self.num_of_iter = num_of_iter
        self.T = num_topic
        self.V = 0
        self.queries = []
        self.count_pattern_topic_word = {}
        self.total_pattern_topic = {}
        self.count_entity_topic_word = {}
        self.total_entity_topic = {}
        self.count_topic = {}
        self.total_topic = 0
        self.alpha = 50.0/self.T
        self.beta = 0.01

    def __get_mapping(self, dict):
        mapping = {}
        index = 0

        for word in dict:
            mapping[word] = index
            index += 1
        return mapping

    def __get_dict(self):
        dict = set([])

        with open(self.input_file, 'rb') as input:
            queries = input.readlines()
            for query in queries:
                query = utility.remove_punctuation(query)
                query = query.replace('\n', '')
                words = query.split(' ')
                for eachword in words:
                    if len(eachword) != 0:
                        dict.add(eachword)
        return dict


    def __write_mapping_to_file(self, mapping):
        with open(self.mapping_file, 'wb') as output:
            for word in mapping:
                word_id = mapping[word]
                map = str(word_id) + ' ' + str(word)
                map = map.strip()
                output.write(map+'\n')

    def __write_id_file(self, mapping):
        with open(self.input_file, 'rb') as input, open(self.file_id, 'wb') as output:
            queries = input.readlines()
            for query in queries:
                query = utility.remove_punctuation(query)
                query = query.replace('\n', '')
                words = query.split(' ')
                query_id = ''
                for eachword in words:
                    if len(eachword) != 0:
                        query_id += ' ' + str(mapping[eachword])
                query_id = query_id.strip()
                output.write(query_id + '\n')

    def __set_topic(self, query):
        topic = int(random.random() * self.T)
        query.set_topic(topic)
        self.count_topic[topic] = self.count_topic.get(topic, 0) + 1
        self.total_topic += 1
        return topic


    def __set_type(self, query, topic, w_index):
        word = query.words[w_index]
        type = int(random.random() * 2)
        query.set_type(w_index, type)
        if type == PATTERN:
            if topic in self.count_pattern_topic_word:
                self.count_pattern_topic_word[topic][word] = self.count_pattern_topic_word[topic].get(word, 0) + 1
            else:
                self.count_pattern_topic_word[topic] = {}
                self.count_pattern_topic_word[topic][word] = 1
            self.total_pattern_topic[topic] = self.total_pattern_topic.get(topic, 0) + 1
        elif type == ENTITY:
            if topic in self.count_entity_topic_word:
                self.count_entity_topic_word[topic][word] = self.count_entity_topic_word[topic].get(word, 0) + 1
            else:
                self.count_entity_topic_word[topic] = {}
                self.count_entity_topic_word[topic][word] = 1
            self.total_entity_topic[topic] = self.total_entity_topic.get(topic, 0) + 1


    def __remove_topic_counts_part1(self, topic):
        self.count_topic[topic] -= 1
        if self.count_topic[topic] == 0:
            del self.count_topic[topic]
        self.total_topic -= 1

    def __calculate_statistics_perquery(self, query, topic):
        num_pattern_word = {}
        num_entity_word = {}
        total_num_pattern_word = 0
        total_num_entity_word = 0
        for w_index in range(0, query.get_length()):
            word = query.words[w_index]
            if query.types[w_index] == 0:
                num_pattern_word[word] = num_pattern_word.get(word, 0) + 1
                total_num_pattern_word += 1
            elif query.types[w_index] == 1:
                num_entity_word[word] = num_entity_word.get(word, 0) + 1
                total_num_entity_word += 1
        return num_pattern_word, num_entity_word, total_num_pattern_word, total_num_entity_word

    def __remove_topic_counts_part2(self, query, topic):
        for w_index in range(0,query.get_length()):
            word = query.words[w_index]
            if query.types[w_index] == 0:
                self.count_pattern_topic_word[topic][word] -= 1
                if self.count_pattern_topic_word[topic][word] == 0:
                    del self.count_pattern_topic_word[topic][word]
                self.total_pattern_topic[topic] -= 1
                if self.total_pattern_topic[topic] == 0:
                    del self.total_pattern_topic[topic]
            elif query.types[w_index] == 1:
                self.count_entity_topic_word[topic][word] -= 1
                if self.count_entity_topic_word[topic][word] == 0:
                    del self.count_entity_topic_word[topic][word]
                self.total_entity_topic[topic] -= 1
                if self.total_entity_topic[topic] == 0:
                    del self.total_entity_topic[topic]

    def __resample(self, topic, num_pattern_word, num_entity_word, total_num_pattern_word, total_num_entity_word):
        probs = []
        min_prob = sys.float_info.max
        for t_index in range(0, self.T):
            count_topic = 0
            if topic in self.count_topic:
                count_topic = self.count_topic[topic]
            prob = math.log((count_topic + self.alpha) / self.total_topic)
            total_pattern_topic = 0
            if topic in self.total_pattern_topic:
                total_pattern_topic = self.total_pattern_topic[topic]
            prob -= utility.Gamma(total_pattern_topic + self.beta+total_num_pattern_word,
                                  total_pattern_topic + self.beta)
            for pattern_word in num_pattern_word:
                freq = num_pattern_word[pattern_word]
                count_pattern_topic_word = 0
                if topic in self.count_pattern_topic_word:
                    if pattern_word in self.count_pattern_topic_word[topic]:
                        count_pattern_topic_word = self.count_pattern_topic_word[topic][pattern_word]
                prob += utility.Gamma(count_pattern_topic_word + self.beta+freq,
                                      count_pattern_topic_word + self.beta)
            total_entity_topic = 0
            if topic in self.total_entity_topic:
                total_entity_topic = self.total_entity_topic[topic]
            prob -= utility.Gamma(total_entity_topic+self.beta+total_num_entity_word,
                                  total_entity_topic+self.beta)
            for entity_word in num_entity_word:
                freq = num_entity_word[entity_word]
                count_entity_topic_word = 0
                if topic in self.count_entity_topic_word:
                    if entity_word in self.count_entity_topic_word[topic]:
                        count_entity_topic_word = self.count_entity_topic_word[topic][entity_word]
                prob += utility.Gamma(count_entity_topic_word + self.beta+freq,
                                      count_entity_topic_word + self.beta)
            probs.append(prob)
            min_prob = min(min_prob,prob)
        for t_index in range(0, self.T):
            probs[t_index] -= min_prob
            probs[t_index] = math.exp(probs[t_index])
        for t_index in range(1, self.T):
            probs[t_index] += probs[t_index-1]
        r = random.random() * probs[self.T-1]
        for t_index in range(0, self.T):
            if probs[t_index] >= r:
                break
        topic_new = t_index
        return topic_new

    def __topic_recount(self, query, topic_new):
        self.count_topic[topic_new] = self.count_topic.get(topic_new, 0) + 1
        self.total_topic += 1
        query.set_topic(topic_new)
        for w_index in range(0,query.get_length()):
            word = query.words[w_index]
            if query.types[w_index] == 0:
                if topic_new in self.count_pattern_topic_word:
                    self.count_pattern_topic_word[topic_new][word] = self.count_pattern_topic_word[topic_new].get(word, 0) + 1
                else:
                    self.count_pattern_topic_word[topic_new] = {}
                    self.count_pattern_topic_word[topic_new][word] = 1
                self.total_pattern_topic[topic_new] = self.total_pattern_topic.get(topic_new) + 1
            elif query.types[w_index] == 1:
                if topic_new in self.count_entity_topic_word:
                    self.count_entity_topic_word[topic_new][word] = self.count_entity_topic_word[topic_new].get(word, 0) + 1
                else:
                    self.count_entity_topic_word[topic_new] = {}
                    self.count_entity_topic_word[topic_new][word] = 1
                self.total_entity_topic[topic_new] = self.total_entity_topic.get(topic_new, 0) + 1

    def __remove_indicator(self, topic, type, word):
        if type == PATTERN:
            self.count_pattern_topic_word[topic][word] -= 1
            if self.count_pattern_topic_word[topic][word] == 0:
                del self.count_pattern_topic_word[topic][word]
            self.total_pattern_topic[topic] -= 1
            if self.total_pattern_topic[topic] == 0:
                del self.total_pattern_topic[topic]
        if type == ENTITY:
            self.count_entity_topic_word[topic][word] -= 1
            if self.count_entity_topic_word[topic][word] == 0:
                del self.count_entity_topic_word[topic][word]
            self.total_entity_topic[topic] -= 1
            if self.total_entity_topic[topic] == 0:
                del self.total_entity_topic[topic]

    def __type_resample(self, topic, word):
        probs = [0.0, 0.0]
        count_pattern_topic_word = 0

        if topic in self.count_pattern_topic_word:
            if word in self.count_pattern_topic_word[topic]:
                count_pattern_topic_word = self.count_pattern_topic_word[topic][word]
        total_pattern_topic = 0
        if topic in self.total_pattern_topic:
            total_pattern_topic = self.total_pattern_topic[topic]
        count_entity_topic_word = 0
        if topic in self.count_entity_topic_word:
            if word in self.count_entity_topic_word[topic]:
                count_entity_topic_word = self.count_entity_topic_word[topic][word]
        total_entity_topic = 0
        if topic in self.total_entity_topic:
            total_entity_topic = self.total_entity_topic[topic]
        probs[0] = (count_pattern_topic_word+self.beta) / (total_pattern_topic+self.V*self.beta)
        probs[1] = (count_entity_topic_word+self.beta) / (total_entity_topic+self.V*self.beta)
        probs[1] += probs[0]
        rd = random.random() * probs[1]
        r = 0
        for index in range(0, 2):
            if probs[index] >= rd:
                r = index
                break
        type_new = r
        return type_new

    def __recount_indicator(self, query, w_index, topic, word, type_new):
        query.set_type(w_index, type_new)
        if type_new == PATTERN:
            if topic in self.count_pattern_topic_word:
                self.count_pattern_topic_word[topic][word] = self.count_pattern_topic_word[topic].get(word, 0) + 1
            else:
                self.count_pattern_topic_word[topic] = {}
                self.count_pattern_topic_word[topic][word] = 1
            self.total_pattern_topic[topic] = self.total_pattern_topic.get(topic, 0) + 1
        if type_new == ENTITY:
            if topic in self.count_entity_topic_word:
                self.count_entity_topic_word[topic][word] = self.count_entity_topic_word[topic].get(word, 0) + 1
            else:
                self.count_entity_topic_word[topic] = {}
                self.count_entity_topic_word[topic][word] = 1
            self.total_entity_topic[topic] = self.total_entity_topic.get(topic, 0) + 1

    def __save_classification_to_file(self, mapping):
        with open(self.file_result_classification,'wb') as output:
            writer = csv.writer(output)
            for query in self.queries:
                row = []
                sentence_id = query.sentence.replace('\n','').split(' ')
                sentence_word = ''
                for word_id in sentence_id:
                    if len(word_id) != 0:
                        word = mapping[word_id]
                        sentence_word += ' '+word
                sentence_word = sentence_word.strip()
                row.append(sentence_word)
                row.append(query.topic)
                pattern_words = []
                entity_words = []
                for index in range(0,query.get_length()):
                    word_id = query.words[index]
                    type = query.types[index]
                    if type == PATTERN:
                        pattern_words.append(mapping[word_id])
                    elif type == ENTITY:
                        entity_words.append(mapping[word_id])
                row.append(pattern_words)
                row.append(entity_words)
                writer.writerow(row)

    def __get_top_words(self, topic_word_statistics, topic_statistics, t_index):
        prob_pattern_words = {}
        sum = 0.0
        for w_index in range(0,self.V):
            prob_pattern_words[w_index] = 0
            if t_index in topic_word_statistics:
                w_word_index = str(w_index)
                if w_word_index in topic_word_statistics[t_index]:
                    prob_pattern_words[w_index] = float(topic_word_statistics[t_index][w_word_index]) \
                                                  /float(topic_statistics[t_index])
        sorted_x = sorted(prob_pattern_words.iteritems(), key=operator.itemgetter(1),reverse=True)
        return sorted_x


    def __write_type_words(self, sorted_xy, mapping, handler):
        row = []
        for index in range(0,100):
            word = mapping[str(sorted_xy[index][0])]
            prob = sorted_xy[index][1]
            if prob == 0:
                break
            result = str(word) + ' ' + str(prob)
            row.append(result)
        handler.writerow(row)

    def __read_from_mapping_file(self):
        mapping = {}
        with open(self.mapping_file,'rb') as input:
            lines = input.readlines()
            for line in lines:
                id = line.split(' ')[0]
                word = line.split(' ')[1].replace('\n','')
                mapping[id] = word
        return mapping

    def __save_type_file(self, mapping):
        with open(self.file_result_pattern,'wb') as output1, open(self.file_result_entity,'wb') as output2:
            writer1 = csv.writer(output1)
            writer2 = csv.writer(output2)
            for t_index in range(0, self.T):
                sorted_x = self.__get_top_words(self.count_pattern_topic_word, self.total_pattern_topic, t_index)
                sorted_y = self.__get_top_words(self.count_entity_topic_word, self.total_entity_topic, t_index)
                self.__write_type_words(sorted_x, mapping, writer1)
                self.__write_type_words(sorted_y, mapping, writer2)

    def load_dictionary(self):
        dict = self.__get_dict()
        self.V = len(dict)
        mapping = self.__get_mapping(dict)
        self.__write_mapping_to_file(mapping)
        self.__write_id_file(mapping)


    def load_query(self):
        with open(self.file_id, 'rb') as input:
            sentences = input.readlines()
            for query_each in sentences:
                query_obj = query_sentence()
                query_obj.query(query_each)
                self.queries.append(query_obj)

    def init_state(self):
        for q_index in range(0, len(self.queries)):
            query = self.queries[q_index]
            topic = self.__set_topic(query)
            for w_index in range(0, self.queries[q_index].get_length()):
                self.__set_type(query, topic, w_index)

    def sample_topic(self,q_index):
        query = self.queries[q_index]
        topic = query.topic
        self.__remove_topic_counts_part1(topic)
        num_pattern_word, num_entity_word, total_num_pattern_word, total_num_entity_word = self.__calculate_statistics_perquery(query, topic)
        self.__remove_topic_counts_part2(query, topic)
        topic_new = self.__resample(topic, num_pattern_word, num_entity_word, total_num_pattern_word, total_num_entity_word)
        self.__topic_recount(query, topic_new)


    def sample_indicator(self, q_index, w_index):
        query = self.queries[q_index]
        word = query.words[w_index]
        type = query.types[w_index]
        topic = query.topic
        self.__remove_indicator(topic, type, word)
        type_new = self.__type_resample(topic, word)
        self.__recount_indicator(query, w_index, topic, word, type_new)

    def save_query_topic_pattern_entity(self):
        mapping = self.__read_from_mapping_file()
        self.__save_classification_to_file(mapping)

    def save_pattern_topic_word(self):
        mapping = self.__read_from_mapping_file()
        self.__save_type_file(mapping)

    def main(self):
        self.load_dictionary()
        self.load_query()
        self.init_state()
        for _ in range(0, self.num_of_iter):
            for q_index in range(0,len(self.queries)):
                query = self.queries[q_index]
                self.sample_topic(q_index)
                for w_index in range(0,query.get_length()):
                    self.sample_indicator(q_index,w_index)
        self.save_query_topic_pattern_entity()
        self.save_pattern_topic_word()


if __name__ == "__main__":
    test = pattern_entity_model(2, 10, 'example.txt')
    test.main()







