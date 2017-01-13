__author__ = 'xiaolisong'
import string
import math


def remove_punctuation(str):

    exclude = set(string.punctuation)
    str =  ''.join(ch for ch in str if ch not in exclude)
    str = str.replace('.','')
    str = str.replace('\'','')

    return str

def double_range(start, end, step):
    while start <= end:
        yield start
        start += step

def Gamma(x,y):
    if x == y:
        return 0
    sum = 0.0
    for index_double in double_range(y,x,1.0):
        sum += math.log(index_double)
    return sum

def remove_stopwords(str):
    stopwords = set([])
    with open('stopwords.txt','rb') as input:
        lines = input.readlines()
        for stopword in lines:
            stopword = remove_punctuation(stopword).replace('\n','').lower()
            stopwords.add(stopword)
    str = str.replace('\n','')
    str = remove_punctuation(str).lower()
    words = str.split(' ')
    str_new = ''

    for word in words:
        if word not in stopwords:
            str_new += ' '+word
    str_new = str_new.strip()
    return str_new




