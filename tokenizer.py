import nltk
from nltk import RegexpTokenizer
import string
import re
import getpass

# Tokenize text into words, punctuation, and whitespace tokens

fopen = open("/home/%s/nltk_data/corpora/stopwords/english" %(getpass.getuser(),))
stopwords = fopen.readlines()
stopwords = set([x.strip() for x in stopwords]).union((list(string.lowercase)))

class ModifiedTrainingTokenizer(RegexpTokenizer):
    def __init__(self):
        RegexpTokenizer.__init__(self, r'\w+\[.,]+|[\[\]\(\)\{\}"\-\<\>\=]+|[^\w\s]')

class ModifiedWPTokenizer(RegexpTokenizer):
    def __init__(self):
        RegexpTokenizer.__init__(self, r'\w+|\s+|\[,.]+|\,+|[\{\}\-\<\>\=]+|(?!\')[^\w\s]')


# Based on O'Reilly, pp234 but also uses whitespace information
class SentenceTokenizer():

    # extract punctuation features from word list for position i
    # Features are: this word; previous word (lower case);
    # is the next word capitalized?; previous word only one char long?
    def punct_features(self, tokens, i):
        return {'next-word-capitalized': (i < len(tokens)-1) and tokens[i+1][0].isupper(),
                'prevword': tokens[i-1].lower(),
                'punct': tokens[i],
                'prev-word-is-one-char': len(tokens[i-1]) == 1}

    # Same as punct_features, but works with a list of
    # (word,bool) tuples for the tokesn. Word is used as above, but the bool
    # flag (whitespace separator?) is ignored
    # This allows the same features to be extracted from tuples instead of
    # words
    def punct_features2(self,tokens, i):
        return {'next-word-capitalized': (i < len(tokens)-1) and tokens[i+1][0][0].isupper(),
                'prevword': tokens[i-1][0].lower(),
                'punct': tokens[i][0],
                'prev-word-is-one-char': len(tokens[i-1][0]) == 1}

    # The constructor builds a classifier using treebank training data
    # Naive Bayes is used for fast training
    # The entire dataset is used for training
    def __init__(self):
        self.tokenizer = ModifiedWPTokenizer()
        training_tok = ModifiedTrainingTokenizer()
        training_path = "/home/%s/nltk_data/corpora/treebank/raw/" %(getpass.getuser(),)

        training_sents = nltk.corpus.treebank_raw.sents()
        tokens = []
        boundaries = set()
        offset = 0
        training_sents = nltk.corpus.PlaintextCorpusReader(training_path, ".*", training_tok, encoding='latin-1').sents()

        for sent in training_sents:
            bSkip = (len(sent) == 2)
            if (bSkip):
                bSkip = bSkip and sent[0] == "."  and sent[1] == "START"
            if (not bSkip):
                tokens.extend(sent)
                offset += len(sent)
                boundaries.add(offset-1)
        # Create training features
        featuresets = [(self.punct_features(tokens,i), (i in boundaries))
                       for i in range(1, len(tokens)-1)
                       if tokens[i] in '.?!']

        train_set = featuresets
        self.classifier = nltk.NaiveBayesClassifier.train(train_set)

    # Use the classifier to segment word tokens into sentences
    # words is a list of (word,bool) tuples
    def classify_segment_sentences(self,words):
        start = 0
        sents = []
        for i, word in enumerate(words):
            #print word, self.classifier.classify(self.punct_features2(words,i))
            if word[0] in ',.?!"()[]{}' and self.classifier.classify(self.punct_features2(words,i)) == True:
                sents.append(words[start:i+1])
                start = i+1
        if start < len(words):
            sents.append(words[start:])
        return sents

    # Segment text into sentences and words
    # returns a list of sentences, each sentence is a list of words
    # punctuation chars are classed as word tokens (except abbreviations)
    def segment_text(self,full_text):
        ReUrl = re.compile('(href=)?[\(\[]?(http?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*\/?[\)\]]?')
        ReShortUrl = re.compile('[\(\[]?(http://(bit\.ly|t\.co|lnkd\.in|tcrn\.ch)\S*)\b[\)\]]?')
        ReNumber = re.compile('^[0-9]+([,.][0-9]+)?$')
        ReImage = re.compile('<img([^>]*[^/])>')
        ReTagsLt = re.compile('&gt;?')
        ReTagsGt = re.compile('&gt;?')
        ReTagsAmps = re.compile('&amp;?')
        ReTagsQuote = re.compile('&quot;?')
        ReTagsTilde = re.compile('&tilde;?')
        ReTagsDash = re.compile('&mdash;?')
        ReTagsHtml = re.compile('&\w;')

        # Split (tokenize) text into words. Count whitespace as
        # words. Keeping this information allows us to distinguish between
        # abbreviations and sentence terminators
        full_text = full_text.lower()
        full_text = ReUrl.sub("URLsub", full_text)
        full_text = ReShortUrl.sub("shortURLsub", full_text)
        full_text = ReNumber.sub("NUMBERsub", full_text)

        full_text = ReTagsLt.sub("<", full_text)
        full_text = ReTagsGt.sub(">", full_text)
        full_text = ReTagsAmps.sub("&", full_text)
        full_text = ReTagsQuote.sub("IMGsub", full_text)
        full_text = ReTagsTilde.sub("~", full_text)
        full_text = ReTagsDash.sub("-", full_text)
        full_text = ReTagsHtml.sub("HTMLTags", full_text)

        full_text = ReImage.sub("IMGsub", full_text)

        text_words_sp = self.tokenizer.tokenize(full_text)

        # Take tokenized words+spaces and create tuples of (token,bool)
        # with the bool entry indicating if the token is whitespace.
        # All whitespace is collapsed down to single sp chars
        word_tuples = []
        i = 0
        while (i<len(text_words_sp)):
            word = text_words_sp[i]
            if (word.isspace()):
                word = " "    # convert all whitespace to a single sp char
            if (i == len(text_words_sp) - 1):
                word_tuples.append((word, False))
            else:
                word2 = text_words_sp[i+1]
                if (word2.isspace()):
                    i = i +1
                    word_tuples.append( (word, True) )
                else:
                    word_tuples.append( (word, False) )
            i = i +1

        delChars = set('.,?![]:;\/\\()"{}-$%^&*<>~-*')
        # Create list of sentence using the classifier
        sentences = []
        for sent in self.classify_segment_sentences(word_tuples):
            # sent holds the next sentence list of tokens
            # this is actually a list of (token,bool) tuples as above
            sentence = []
            i = 0
            tok = ""
            # loop over each token tuple, using separator boolean
            # to collapse abbreviations into single word tokens
            for i,tup in enumerate(sent):
                if (tup[0][0] in string.punctuation and not tup[0][0] in '.?!'):
                    # punctuation that should be kept as a single token
                    if (len(tok) > 0):
                        sentence.append(tok)
                        tok=""
                    sentence.append(tup[0])
                elif (tup[1]):
                    # space character - finish a word token
                    sentence.append( tok+tup[0] )
                    tok = ""
                elif (i == len(sent)-2):
                    # penultimate end of the sentence - break off the punctuation
                    sentence.append( tok+tup[0] )
                    tok = ""
                else:
                    # no space =&gt; accumulate a token in tok
                    tok = tok + tup[0]
            # Add this token to the current sentence
            if len(tok) > 0:
                sentence.append(tok)
            # The sentence has been procssed =&gt; save it
            sentences.append(filter(lambda x: not(x in delChars), sentence))

        # return the resulting list of sentences
        return sentences

    def ngrams(self,text, N = 1):
        words = []
        for sentence in text:
            for k in range(0,len(sentence)-(N-1)):
                b = set(sentence[k:k+N])
                if len(b.intersection(stopwords)) > 0:
                    continue
                words.append(" ".join(sentence[k:k+N]))
        if N == 1:
            words = filter(lambda x: len(x)> 1, words)
        return words
import unittest

class TestTokenizerMethods(unittest.TestCase):
    def test_ngrams(self):
        text = """If you are using the NLTK library for Python, you might have faced a situation where you need to reduce the size of your text to improve the performance of your algorithms. - See more at: [url](http://blog.adlegant.com/how-to-install-nltk-corporastopwords/#sthash.6UYHoR9R.dpuf)"""
        tokenizer = SentenceTokenizer()
        text = tokenizer.segment_text(text.encode('utf-8'))
        self.assertEqual(['using', 'nltk', 'library', 'python', 'might', 'faced', 'situation', 'need', 'reduce', 'size', 'text', 'improve', 'performance', 'algorithms', 'see', 'url', 'URLsub', 'URLsub']
, tokenizer.ngrams(text, 1))
        text = """I signed an open letter earlier this year imploring researchers to balance the benefits of AI with the risks. The letter acknowledges that AI might one day help eradicate disease and poverty, but it also puts the onus on scientists at the forefront of this technology to keep the human factor front and center of their innovations. I'm part of a campaign enabled by Nokia and hope you will join the conversation on http://www.wired.com/maketechhuman. Learn more about my foundation here: http://stephenhawkingfoundation.org/
Due to the fact that I will be answering questions at my own pace, working with the moderators of /r/Science we are opening this thread up in advance to gather your questions.
My goal will be to answer as many of the questions you submit as possible over the coming weeks. I appreciate all of your understanding, and taking the time to ask me your questions."""
        tokenizer = SentenceTokenizer()
        text = tokenizer.segment_text(text.encode('utf-8'))
        self.assertEqual(['signed', 'open', 'letter', 'earlier', 'year', 'imploring', 'researchers', 'balance', 'benefits', 'ai', 'risks', 'letter', 'acknowledges', 'ai', 'might', 'one', 'day', 'help', 'eradicate', 'disease', 'poverty', 'also', 'puts', 'onus', 'scientists', 'forefront', 'technology', 'keep', 'human', 'factor', 'front', 'center', 'innovations', 'im', 'part', 'campaign', 'enabled', 'nokia', 'hope', 'join', 'conversation', 'URLsub', 'learn', 'foundation', 'URLsub', 'due', 'fact', 'answering', 'questions', 'pace', 'working', 'moderators', 'science', 'opening', 'thread', 'advance', 'gather', 'questions', 'goal', 'answer', 'many', 'questions', 'submit', 'possible', 'coming', 'weeks', 'appreciate', 'understanding', 'taking', 'time', 'ask', 'questions'], tokenizer.ngrams(text, 1))
        self.assertEqual(
['open letter', 'letter earlier', 'year imploring', 'imploring researchers', 'letter acknowledges', 'ai might', 'might one', 'one day', 'day help', 'help eradicate', 'eradicate disease', 'also puts', 'human factor', 'factor front', 'im part', 'campaign enabled', 'URLsub learn', 'URLsub due', 'answering questions', 'coming weeks'], tokenizer.ngrams(text, 2))

if __name__ == "__main__":
    unittest.main()
