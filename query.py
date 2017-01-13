__author__ = 'xiaolisong'

import utility

class query_sentence:

    def __init__(self):
        self.sentence = ''
        self.types = {}
        self.topics = {}
        self.topic_prior = False
        self.types = {}
        self.topic_priors = {}
        self.type_priors = {}
        self.topic = ''
        self.words = {}

    def query(self,query):
        self.sentence = query
        query_words = query.split()
        for index in range(0,len(query_words)):
            self.words[index] = query_words[index]
        return self.query

    def set_topic(self,topic_id):
        self.topic = topic_id

    def set_topics(self,word_id,topic_id):
        self.topics[word_id] = topic_id

    def set_topic_prior(self):
        self.topic_prior = True

    def set_topic_priors(self,word_id,ture_false):
        self.topic_priors[word_id] = ture_false

    def set_type_priors(self,word_id,true_false):
        self.type_priors[word_id] = true_false

    # def set_ty


    def set_type(self,w_index,word_type):
        self.types[w_index] = word_type

    def get_length(self):
        return len(self.words)




