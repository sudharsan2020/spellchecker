
# coding: utf-8

# # Spelling Correction using Deep Learning
# 

# In[409]:


import os
import sys
import errno

# Global variable around input length
MIN_INPUT_LEN = 5 # minimum number of characters in a sentence
MAX_INPUT_LEN = 60 # maximum number of characters in a sentence

# Filenames
# FILE_NAME_CLEAN = os.path.join(os.path.expanduser("data"), "news.en.clean") # clean data file
# FILE_NAME_CLEAN = "C:\\Users\sundsudh\Documents\GitHub\spellchecker\data\correct_sentences.txt"
# FILE_NAME_FILTERED = "C:\Users\sundsudh\Documents\GitHub\spellchecker\data\wrong_words.txt"
# # FILE_NAME_TRAIN = os.path.join(os.path.expanduser("data"), "news.en.train")
# # FILE_NAME_VALIDATE = os.path.join(os.path.expanduser("data"), "news.en.validate")
# FILE_NAME_TRAIN = "C:\Users\sundsudh\Documents\GitHub\spellchecker\data\correct_words.txt"
# FILE_NAME_VALIDATE = "C:\Users\sundsudh\Documents\GitHub\spellchecker\data\wrong_sentences.txt"#

print("Using the small data.")
directory = "small_graph"
# This is where the small graph is going to be saved and reloaded
GRAPH_PARAMETERS = "small_graph/graph_params" # Filename for storing parameters associated with the graph
SOURCE_INT_TO_LETTER = "small_graph/sourceinttoletter.json" # Filename for INT to letter List for source sentences
TARGET_INT_TO_LETTER = "small_graph/targetinttoletter.json" # Filename for INT to letter List for target sentences
SOURCE_LETTER_TO_INT = "small_graph/sourcelettertoint.json" # Filename for letter to INT List for source sentences
TARGET_LETTER_TO_INT = "small_graph/targetlettertoint.json" # Filename for letter to INT List for source sentences
checkpoint = "small_graph/output/best_model.ckpt"

# create directory for data, large or small, if it does not already exist
try:
    os.makedirs(directory)
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise

# ## Clean the data
# Takes the `news.en.clean` and input and produces `news.en.shuffled`.

# In[412]:

def clean_data():
    
    import re

    NORMALIZE_WHITESPACE_REGEX = re.compile(r'[^\S\n]+', re.UNICODE) # match all whitespace except newlines
    RE_DASH_FILTER = re.compile(r'[\-\˗\֊\‐\‑\‒\–\—\⁻\₋\−\﹣\－]', re.UNICODE)
    RE_APOSTROPHE_FILTER = re.compile(r'&#39;|[ʼ՚＇‘’‛❛❜ߴߵ`‵´ˊˋ{}{}{}{}{}{}{}{}{}]'
                                      .format(chr(768), chr(769), chr(832), chr(833), chr(2387),
                                              chr(5151), chr(5152), chr(65344), chr(8242)), re.UNICODE)
    RE_LEFT_PARENTH_FILTER = re.compile(r'[\(\[\{\⁽\₍\❨\❪\﹙\（]', re.UNICODE)
    RE_RIGHT_PARENTH_FILTER = re.compile(r'[\)\]\}\⁾\₎\❩\❫\﹚\）]', re.UNICODE)
    ALLOWED_CURRENCIES = """¥£₪$€฿₨"""
    ALLOWED_PUNCTUATION = """-!?/;"'%&<>.()[]{}@#:,|=*"""
    RE_BASIC_CLEANER = re.compile(r'[^\w\s{}{}]'
                                  .format(re.escape(ALLOWED_CURRENCIES), re.escape(ALLOWED_PUNCTUATION)), re.UNICODE)

    def file_len(fname):
        with open(fname, encoding="utf8") as f:
            for i, l in enumerate(f):
                pass
        return i + 1

    def clean_text(text):
        # Clean the text - remove unwanted chars, fold punctuation etc.
        result = NORMALIZE_WHITESPACE_REGEX.sub(' ', text.strip())
        result = RE_DASH_FILTER.sub('-', result)
        result = RE_APOSTROPHE_FILTER.sub("'", result)
        result = RE_LEFT_PARENTH_FILTER.sub("(", result)
        result = RE_RIGHT_PARENTH_FILTER.sub(")", result)
        result = RE_BASIC_CLEANER.sub('', result)
        return result

# ## Analyze the characters
# 
# Get counts of all of the characters and select the top ones for processing and filter only sentences with the right charcters. Eliminate any sentences that are too small or too long.
# 
# Takes `news.en.shuffled` as input and produces `news.en.filtered` and `news.en.char_frequency.json`.

# In[413]:


def analyze_characters():
    
    from collections import Counter
    import json

    NUMBER_OF_CHARS = 75 # Quantity of most popular characters to keep. Was 100 in original code.
    CHAR_FREQUENCY_FILE_NAME = os.path.join("data", "news.en.char_frequency.json")

    # create character frequency file
    if (os.path.isfile(CHAR_FREQUENCY_FILE_NAME)):
        print("Character frequency file already created.")
    else:
        counter = Counter()
        print("Reading data file:")
        for line in open(FILE_NAME_CLEAN, encoding="utf8"):
            counter.update(line)
        print("Done. Writing to file:")
        with open(CHAR_FREQUENCY_FILE_NAME, 'wb') as output_file:
            output_file.write(json.dumps(counter).encode("utf-8"))
        most_popular_chars = {key for key, _value in counter.most_common(NUMBER_OF_CHARS)}

    # Read top characters that were saved to file
    chars = json.loads(open(CHAR_FREQUENCY_FILE_NAME).read())
    counter = Counter(chars)
    most_popular_chars = {key for key, _value in counter.most_common(NUMBER_OF_CHARS)}
    print("The top %s chars are:", NUMBER_OF_CHARS)
    print("".join(sorted(most_popular_chars)))

    # Filter only sentences with the right chars
    print("\nReading and filtering data:")
    num_lines = 0
    with open(FILE_NAME_FILTERED, "wb") as output_file:
        for line in open(FILE_NAME_CLEAN, encoding="utf8"):
            if line and (not bool(set(line) - most_popular_chars)) and (MAX_INPUT_LEN >= len(line) > MIN_INPUT_LEN):
                output_file.write(line.encode("utf8"))
                num_lines += 1
                if (num_lines % 1000000 == 0):
                    print("{0:10,d}".format(num_lines), ": ", line, end="")
    print("Done. Filtered file contains {:,} lines.".format(num_lines))


# ## Split the data into training and validation sets
# Takes `news.en.filtered` as input and produces `news.en.train` and `news.en.validate`.
# 

# In[414]:


def split_data():
    
    from numpy.random import shuffle as random_shuffle

    if (os.path.isfile(FILE_NAME_TRAIN)):
        print("Training and Validation files already created.")
    else:
        answers = open(FILE_NAME_FILTERED, encoding="utf8").read().split("\n")
        print('shuffle', end=" ")
        random_shuffle(answers)
        print("Done")
        # Explicitly set apart 10% for validation data that we never train over
        # skip if files already exist
        split_at = len(answers) - len(answers) // 10
        with open(FILE_NAME_TRAIN, "wb") as output_file:
            output_file.write("\n".join(answers[:split_at]).encode('utf-8'))
        with open(FILE_NAME_VALIDATE, "wb") as output_file:
            output_file.write("\n".join(answers[split_at:]).encode('utf-8'))
        print("\nTraining and Validation files written.")


# ## Load the target data and generate source data by injecting mistakes

# In[415]:


def add_noise_to_string(a_string, amount_of_noise): # Add artificial spelling mistakes to string    
    
    from numpy.random import choice as random_choice, randint as random_randint, seed as random_seed, rand

    CHARS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .")

    if rand() < amount_of_noise * len(a_string):
        # Replace a character with a random character
        random_char_position = random_randint(len(a_string))
        a_string = a_string[:random_char_position] + random_choice(CHARS[:-1]) + a_string[random_char_position + 1:]
    if rand() < amount_of_noise * len(a_string):
        # Delete a character
        random_char_position = random_randint(len(a_string))
        a_string = a_string[:random_char_position] + a_string[random_char_position + 1:]
    if len(a_string) < MAX_INPUT_LEN and rand() < amount_of_noise * len(a_string):
        # Add a random character
        random_char_position = random_randint(len(a_string))
        a_string = a_string[:random_char_position] + random_choice(CHARS[:-1]) + a_string[random_char_position:]
    if rand() < amount_of_noise * len(a_string):
        # Transpose 2 characters
        random_char_position = random_randint(len(a_string) - 1)
        a_string = (a_string[:random_char_position] + a_string[random_char_position + 1] + 
                    a_string[random_char_position] + a_string[random_char_position + 2:])
    return a_string


# In[416]:

# Run this cell to grab the small data sets that came with this model. Otherwise skip it.
# The dataset lives in the /data/ folder. At the moment, it is made up of the following files:
# letters_source.txt: The list of input letter sequences. Each sequence is its own line.
# letters_target.txt: The list of target sequences we'll use in the training process.
# Each sequence here is a response to the input sequence in letters_source.txt with the same line number.

def load_dict_data():

    import helper

    source_path = "C:\\Users\sundsudh\Documents\GitHub\spellchecker\data\wrong_words.txt"
    target_path = "C:\\Users\sundsudh\Documents\GitHub\spellchecker\data\correct_words.txt"

    source_sentences = helper.load_data(source_path).split('\n') # added .split('\n) to be consistent with big data
    target_sentences = helper.load_data(target_path).split('\n')

    # source_sentences contains the entire input sequence file as text delimited by newline symbols.
    print("Source: {}".format(source_sentences[:10]))
    # target_sentences contains the entire output sequence file as text delimited by newline symbols.
    # Each line corresponds to the line from source_sentences. target_sentences contains sorted characters of the line.
    print("Target: {}".format(target_sentences[:10]))

    print("\nThe source is comprised of {:,} sentences.".format(len(source_sentences)))

    return source_sentences, target_sentences

# ## Run this cell to get the tiny data set
# **Start here if you are going to run with the small dataset** If you are using the big dataset, make sure to skip this.

# In[417]:

# # Load the Data - Big of Small
# If the command line switch "small" is set then load the small data. Otherwise load the big data.

# In[418]:

print("Load the Dictionary data....")
wrong_sentencess, correct_sentencess = load_dict_data()

# ## Preprocess
# To do anything useful with it, turn the each string into a list of characters. Then convert the characters to their int values as declared in the vocabulary.

# In[419]:

import json

# Define global variables
source_int_to_letter = []
target_int_to_letter = []
source_letter_to_int = []
target_letter_to_int = []

def extract_character_vocab(data):
    special_words = ['<PAD>', '<UNK>', '<GO>',  '<EOS>']

    #set_words = set([character for line in data.split('\n') for character in line])
    set_words = set([character for line in data for character in line])
    int_to_vocab = {word_i: word for word_i, word in enumerate(special_words + list(set_words))}
    vocab_to_int = {word: word_i for word_i, word in int_to_vocab.items()}

    return int_to_vocab, vocab_to_int
    
def load_int_letter_translations(source, target):
    
    global source_int_to_letter, target_int_to_letter, source_letter_to_int, target_letter_to_int
    
    # Check to see if conversion files have already been created
    if (os.path.isfile(SOURCE_INT_TO_LETTER)):

        print()
        # Load up all of the conversion files
        with open(SOURCE_INT_TO_LETTER, 'r') as file:
            try:
                source_int_to_letter = json.load(file)
                print("Read {} data from file.".format(SOURCE_INT_TO_LETTER))
            except ValueError: # if the file is empty the ValueError will be thrown
                data = {}
        source_int_to_letter = {int(k):v for k,v in source_int_to_letter.items()}
        with open(TARGET_INT_TO_LETTER, 'r') as file:
            try:
                target_int_to_letter = json.load(file)
                print("Read {} data from file.".format(TARGET_INT_TO_LETTER))
            except ValueError: # if the file is empty the ValueError will be thrown
                data = {}
        target_int_to_letter = {int(k):v for k,v in target_int_to_letter.items()}
        with open(SOURCE_LETTER_TO_INT, 'r') as file:
            try:
                source_letter_to_int = json.load(file)
                print("Read {} data from file.".format(SOURCE_LETTER_TO_INT))
            except ValueError: # if the file is empty the ValueError will be thrown
                data = {}
        source_letter_to_int = {k:int(v) for k,v in source_letter_to_int.items()}
        with open(TARGET_LETTER_TO_INT, 'r') as file:
            try:
                target_letter_to_int = json.load(file)
                print("Read {} data from file.".format(TARGET_LETTER_TO_INT))
            except ValueError: # if the file is empty the ValueError will be thrown
                data = {}
        target_letter_to_int = {k:int(v) for k,v in target_letter_to_int.items()}

    else:

        # Build int2letter and letter2int dicts
        source_int_to_letter, source_letter_to_int = extract_character_vocab(source)
        target_int_to_letter, target_letter_to_int = extract_character_vocab(target)
        print("Source INT to letter: {}".format(source_int_to_letter))
        print("Target INT to letter: {}\n".format(target_int_to_letter))

        # Save source_int_to_letter, target_int_to_letter & source_letter_to_int for loading later after graph is saved
        with open(SOURCE_INT_TO_LETTER, 'w') as output_file:
            json.dump(source_int_to_letter, output_file)
        print("Wrote {} data to file.".format(SOURCE_INT_TO_LETTER))
        with open(TARGET_INT_TO_LETTER, 'w') as output_file:
            json.dump(target_int_to_letter, output_file)
        print("Wrote {} data to file.".format(TARGET_INT_TO_LETTER))
        with open(SOURCE_LETTER_TO_INT, 'w') as output_file:
            json.dump(source_letter_to_int, output_file)
        print("Wrote {} data to file.".format(SOURCE_LETTER_TO_INT))
        with open(TARGET_LETTER_TO_INT, 'w') as output_file:
            json.dump(target_letter_to_int, output_file)
        print("Wrote {} data to file.".format(TARGET_LETTER_TO_INT))

def produce_letter_ids(source, target):
    
    if (not source_int_to_letter):
        load_int_letter_translations(source, target)
    
    # Convert characters to ids
    source_ids = [[source_letter_to_int.get(letter, source_letter_to_int['<UNK>']) for letter in line]                          for line in source]
    target_ids = [[target_letter_to_int.get(letter, target_letter_to_int['<UNK>']) for letter in line]                          + [target_letter_to_int['<EOS>']] for line in target]
    
    return source_ids, target_ids


# In[420]:


# Convert source and target sentences into IDs
source_letter_ids, target_letter_ids = produce_letter_ids(wrong_sentencess, correct_sentencess)

print("\nExample source sequences")
print(source_letter_ids[:3])
print("\nExample target sequences")
print(target_letter_ids[:3])
print()


# In[421]:


print('\nFirst 10 sentence:')
for i in range (0, 10):
    print("\nSource --> {}".format(source_letter_ids[i]))
    print("Target --> {}".format(target_letter_ids[i]))


# ## Character Sequence to Sequence Model
# This model was updated to work with TensorFlow 1.1 and builds on the work of Dave Currie. Check out Dave's post [Text Summarization with Amazon Reviews](https://medium.com/towards-data-science/text-summarization-with-amazon-reviews-41801c2210b).
# <img src="images/sequence-to-sequence.jpg"/>
# #### Check the Version of TensorFlow and wether or not there's a GPU

# In[422]:


import tensorflow as tf

# Check TensorFlow Version
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    print('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


# ### Hyperparameters

# In[423]:


if (len(wrong_sentencess) > 10000):
    
    # We are using the big data
    print("Using hyperparameters for the big data with {:,} source sentences.".format(len(wrong_sentencess)))
    epochs = 4       # Number of Epochs
    batch_size = 128 # Batch Size

    rnn_size = 512   # RNN Size
    num_layers = 2   # Number of Layers
    encoding_embedding_size = 512 # Encoding embedding Size
    decoding_embedding_size = 512 # Decoding embedding Size
    keep_probability = 0.7 # keep probability

    learning_rate = 0.001 # Learning Rate
    
else:
    
    # We are using the small data
    print("Using hyperparameters for the small data with {:,} source sentences.".format(len(wrong_sentencess)))
    epochs = 60 # Number of Epochs (normally 60 but reduced to test retraining model)
    batch_size = 128 # Batch Size
    rnn_size = 50 # RNN Size    
    num_layers = 2 # Number of Layers    
    encoding_embedding_size = 15 # Embedding Size
    decoding_embedding_size = 15 # Embedding Size
    keep_probability = 0.7 # keep probability
    learning_rate = 0.001 # Learning Rate

def get_hyperparameters_message():
    message  = "Batch size: {}\n".format(batch_size)
    message += "RNN size  : {}\n".format(rnn_size)
    message += "Num layers: {}\n".format(num_layers)
    message += "Enc. size : {}\n".format(encoding_embedding_size)
    message += "Dec. size : {}\n".format(decoding_embedding_size)
    message += "Keep prob.: {}\n".format(keep_probability)
    message += "Learn rate: {}\n\n".format(learning_rate)
    return message

# Write batch_size to file for loading after graph has been saved
with open(GRAPH_PARAMETERS, 'w') as file:
  file.write('%d' % batch_size)

print("Load up the dict data.")
validation_source_sentences, validation_target_sentences = load_dict_data()
# ### Input

# In[424]:


def get_model_inputs():
    input_data = tf.placeholder(tf.int32, [None, None], name='input')
    targets = tf.placeholder(tf.int32, [None, None], name='targets')
    keep_probability = tf.placeholder(tf.float32,name='keep_prob')
    lr = tf.placeholder(tf.float32, name='learning_rate')

    target_sequence_length = tf.placeholder(tf.int32, (None,), name='target_sequence_length')
    max_target_sequence_length = tf.reduce_max(target_sequence_length, name='max_target_len')
    source_sequence_length = tf.placeholder(tf.int32, (None,), name='source_sequence_length')
    
    return input_data, targets, keep_probability, lr, target_sequence_length, max_target_sequence_length, source_sequence_length


# ### Sequence to Sequence Model
# 
# We can now start defining the functions that will build the seq2seq model. We are building it from the bottom up with the following components:
# 
#     2.1 Encoder
#         - Embedding
#         - Encoder cell
#     2.2 Decoder
#         1- Process decoder inputs
#         2- Set up the decoder
#             - Embedding
#             - Decoder cell
#             - Dense output layer
#             - Training decoder
#             - Inference decoder
#     2.3 Seq2seq model connecting the encoder and decoder
#     2.4 Build the training graph hooking up the model with the 
#         optimizer

# ### 2.1 Encoder
# 
# The first bit of the model we'll build is the encoder. Here, we'll embed the input data, construct our encoder, then pass the embedded data to the encoder.
# 
# - Embed the input data using [`tf.contrib.layers.embed_sequence`](https://www.tensorflow.org/api_docs/python/tf/contrib/layers/embed_sequence)
# <img src="images/embed_sequence.png" />
# 
# - Pass the embedded input into a stack of RNNs.  Save the RNN state and ignore the output.
# <img src="images/encoder.png" />

# In[425]:


def encoding_layer(input_data, rnn_size, num_layers, keep_prob, source_sequence_length, source_vocab_size, 
                   encoding_embedding_size):

    # Encoder embedding
    enc_embed_input = tf.contrib.layers.embed_sequence(input_data, source_vocab_size, encoding_embedding_size)

    # RNN cell
    def make_cell(rnn_size):
        enc_cell = tf.contrib.rnn.LSTMCell(rnn_size, initializer=tf.random_uniform_initializer(-0.1, 0.1, seed=2))
        enc_cell = tf.contrib.rnn.DropoutWrapper(enc_cell, output_keep_prob=keep_prob)
        return enc_cell

    enc_cell = tf.contrib.rnn.MultiRNNCell([make_cell(rnn_size) for _ in range(num_layers)])
    
    enc_output, enc_state = tf.nn.dynamic_rnn(enc_cell, enc_embed_input, 
                                              sequence_length=source_sequence_length, dtype=tf.float32)
    
    return enc_output, enc_state


# ## 2.2 Decoder
# 
# The decoder is probably the most involved part of this model. The following steps are needed to create it:
# 
#     1- Process decoder inputs
#     2- Set up the decoder components
#         - Embedding
#         - Decoder cell
#         - Dense output layer
#         - Training decoder
#         - Inference decoder
# 
# 
# ### Process Decoder Input
# 
# 
# In the training process, the target sequences will be used in two different places:
# 
#  1. Using them to calculate the loss
#  2. Feeding them to the decoder during training to make the model more robust.
# 
# Now we need to address the second point. Let's assume our targets look like this in their letter/word form (we're doing this for readibility. At this point in the code, these sequences would be in int form):
# 
# 
# <img src="images/targets_1.png"/>
# 
# We need to do a simple transformation on the tensor before feeding it to the decoder:
# 
# 1- We will feed an item of the sequence to the decoder at each time step. Think about the last timestep -- where the decoder outputs the final word in its output. The input to that step is the item before last from the target sequence. The decoder has no use for the last item in the target sequence in this scenario. So we'll need to remove the last item. 
# 
# We do that using tensorflow's tf.strided_slice() method. We hand it the tensor, and the index of where to start and where to end the cutting.
# 
# <img src="images/strided_slice_1.png"/>
# 
# 2- The first item in each sequence we feed to the decoder has to be GO symbol. So We'll add that to the beginning.
# 
# 
# <img src="images/targets_add_go.png"/>
# 
# 
# Now the tensor is ready to be fed to the decoder. It looks like this (if we convert from ints to letters/symbols):
# 
# <img src="images/targets_after_processing_1.png"/>

# In[426]:


# Process the input we'll feed to the decoder
def process_decoder_input(target_data, vocab_to_int, batch_size):
    '''Remove the last word id from each batch and concat the <GO> to the begining of each batch'''
    ending = tf.strided_slice(target_data, [0, 0], [batch_size, -1], [1, 1])
    dec_input = tf.concat([tf.fill([batch_size, 1], vocab_to_int['<GO>']), ending], 1)

    return dec_input

#
# ### Set up the decoder components
# 
#         - Embedding
#         - Decoder cell
#         - Dense output layer
#         - Training decoder
#         - Inference decoder
# 
# #### 1- Embedding
# Now that we have prepared the inputs to the training decoder, we need to embed them so they can be ready to be passed to the decoder. 
# 
# We'll create an embedding matrix like the following then have tf.nn.embedding_lookup convert our input to its embedded equivalent:
# <img src="images/embeddings.png" />
# 
# #### 2- Decoder Cell
# Then we declare our decoder cell. Just like the encoder, we'll use an tf.contrib.rnn.LSTMCell here as well.
# 
# We need to declare a decoder for the training process, and a decoder for the inference/prediction process. These two decoders will share their parameters (so that all the weights and biases that are set during the training phase can be used when we deploy the model).
# 
# First, we'll need to define the type of cell we'll be using for our decoder RNNs. We opted for LSTM.
# 
# #### 3- Dense output layer
# Before we move to declaring our decoders, we'll need to create the output layer, which will be a tensorflow.python.layers.core.Dense layer that translates the outputs of the decoder to logits that tell us which element of the decoder vocabulary the decoder is choosing to output at each time step.
# 
# #### 4- Training decoder
# Essentially, we'll be creating two decoders which share their parameters. One for training and one for inference. The two are similar in that both created using tf.contrib.seq2seq.**BasicDecoder** and tf.contrib.seq2seq.**dynamic_decode**. They differ, however, in that we feed the the target sequences as inputs to the training decoder at each time step to make it more robust.
# 
# We can think of the training decoder as looking like this (except that it works with sequences in batches):
# <img src="images/sequence-to-sequence-training-decoder.png"/>
# 
# The training decoder **does not** feed the output of each time step to the next. Rather, the inputs to the decoder time steps are the target sequence from the training dataset (the orange letters).
# 
# #### 5- Inference decoder
# The inference decoder is the one we'll use when we deploy our model to the wild.
# 
# <img src="images/sequence-to-sequence-inference-decoder.png"/>
# 
# We'll hand our encoder hidden state to both the training and inference decoders and have it process its output. TensorFlow handles most of the logic for us. We just have to use the appropriate methods from tf.contrib.seq2seq and supply them with the appropriate inputs.
# 

# In[427]:


def decoding_layer(target_letter_to_int, decoding_embedding_size, num_layers, rnn_size, keep_prob,
                   target_sequence_length, max_target_sequence_length, enc_state, dec_input):
    
    # 1. Decoder Embedding
    target_vocab_size = len(target_letter_to_int)
    dec_embeddings = tf.Variable(tf.random_uniform([target_vocab_size, decoding_embedding_size]))
    dec_embed_input = tf.nn.embedding_lookup(dec_embeddings, dec_input)

    # 2. Construct the decoder cell
    def make_cell(rnn_size):
        dec_cell = tf.contrib.rnn.LSTMCell(rnn_size,
                                           initializer=tf.random_uniform_initializer(-0.1, 0.1, seed=2))
        dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, output_keep_prob=keep_prob)
        return dec_cell

    dec_cell = tf.contrib.rnn.MultiRNNCell([make_cell(rnn_size) for _ in range(num_layers)])
     
    # 3. Dense layer to translate the decoder's output at each time 
    # step into a choice from the target vocabulary
    output_layer = Dense(target_vocab_size,
                         kernel_initializer = tf.truncated_normal_initializer(mean = 0.0, stddev=0.1))

    # 4. Set up a training decoder and an inference decoder
    # Training Decoder
    with tf.variable_scope("decode"):

        # Helper for the training process. Used by BasicDecoder to read inputs.
        training_helper = tf.contrib.seq2seq.TrainingHelper(inputs=dec_embed_input,
                                                            sequence_length=target_sequence_length,
                                                            time_major=False)

        # Basic decoder
        training_decoder = tf.contrib.seq2seq.BasicDecoder(dec_cell, training_helper, enc_state, output_layer) 
        
        # Perform dynamic decoding using the decoder
        training_decoder_output = tf.contrib.seq2seq.dynamic_decode(training_decoder, impute_finished=True, 
                                                                    maximum_iterations=max_target_sequence_length)[0]

    # 5. Inference Decoder
    # Reuses the same parameters trained by the training process
    with tf.variable_scope("decode", reuse=True):
        start_tokens = tf.tile(tf.constant([target_letter_to_int['<GO>']], dtype=tf.int32), 
                               [batch_size], name='start_tokens')

        # Helper for the inference process.
        inference_helper = tf.contrib.seq2seq.GreedyEmbeddingHelper(dec_embeddings, 
                                                                    start_tokens, 
                                                                    target_letter_to_int['<EOS>'])

        # Basic decoder
        inference_decoder = tf.contrib.seq2seq.BasicDecoder(dec_cell, inference_helper, enc_state, output_layer)
        
        # Perform dynamic decoding using the decoder
        inference_decoder_output = tf.contrib.seq2seq.dynamic_decode(inference_decoder,
                                                            impute_finished=True,
                                                            maximum_iterations=max_target_sequence_length)[0]

    return training_decoder_output, inference_decoder_output


# ## 2.3 Seq2seq model 
# Let's now go a step above, and hook up the encoder and decoder using the methods we just declared

# In[428]:


def seq2seq_model(input_data, targets, lr, target_sequence_length, max_target_sequence_length, source_sequence_length,
                  source_vocab_size, target_vocab_size, enc_embedding_size, dec_embedding_size, rnn_size, num_layers, 
                  keep_prob):
    
    # Pass the input data through the encoder. We'll ignore the encoder output, but use the state
    _, enc_state = encoding_layer(input_data, 
                                  rnn_size, 
                                  num_layers,
                                  keep_prob,
                                  source_sequence_length,
                                  source_vocab_size, 
                                  encoding_embedding_size)

    # Prepare the target sequences we'll feed to the decoder in training mode
    dec_input = process_decoder_input(targets, target_letter_to_int, batch_size)
    
    # Pass encoder state and decoder inputs to the decoders
    training_decoder_output, inference_decoder_output = decoding_layer(target_letter_to_int, 
                                                                       decoding_embedding_size, 
                                                                       num_layers, 
                                                                       rnn_size,
                                                                       keep_prob,
                                                                       target_sequence_length,
                                                                       max_target_sequence_length,
                                                                       enc_state, 
                                                                       dec_input) 
    
    return training_decoder_output, inference_decoder_output


# Model outputs *training_decoder_output* and *inference_decoder_output* both contain a 'rnn_output' logits tensor that looks like this:
# 
# <img src="images/logits.png"/>
# 
# The logits we get from the training tensor we'll pass to tf.contrib.seq2seq.**sequence_loss()** to calculate the loss and ultimately the gradient.
# 
# 
# 

# In[429]:


from tensorflow.python.layers.core import Dense

# Build the graph
train_graph = tf.Graph()
# Set the graph to default to ensure that it is ready for training
with train_graph.as_default():
    
    # Load the model inputs    
    input_data, targets, keep_prob, lr, target_sequence_length, max_target_sequence_length, source_sequence_length     = get_model_inputs()
    
    # Create the training and inference logits
    training_decoder_output, inference_decoder_output = seq2seq_model(input_data, 
                                                                      targets, 
                                                                      lr, 
                                                                      target_sequence_length, 
                                                                      max_target_sequence_length, 
                                                                      source_sequence_length,
                                                                      len(source_letter_to_int),
                                                                      len(target_letter_to_int),
                                                                      encoding_embedding_size, 
                                                                      decoding_embedding_size, 
                                                                      rnn_size, 
                                                                      num_layers,
                                                                      keep_prob)    
    
    # Create tensors for the training logits and inference logits
    training_logits = tf.identity(training_decoder_output.rnn_output, 'logits')
    inference_logits = tf.identity(inference_decoder_output.sample_id, name='predictions')
    
    # Create the weights for sequence_loss
    masks = tf.sequence_mask(target_sequence_length, max_target_sequence_length, dtype=tf.float32, name='masks')

    with tf.name_scope("optimization"):
        
        # Loss function
        cost = tf.contrib.seq2seq.sequence_loss(training_logits, targets, masks)

        # Optimizer
        optimizer = tf.train.AdamOptimizer(lr)

        # Gradient Clipping
        gradients = optimizer.compute_gradients(cost)
        capped_gradients = [(tf.clip_by_value(grad, -5., 5.), var) for grad, var in gradients if grad is not None]
        train_op = optimizer.apply_gradients(capped_gradients)
        
        # Add variables to collection in order to load them up when retraining a saved graph
        tf.add_to_collection("cost", cost)
        tf.add_to_collection("train_op", train_op)


# ## Get Batches
# 
# There's little processing involved when we retreive the batches. This is a simple example assuming batch_size = 2
# 
# Target sequences (it's actually in int form, we're showing the characters for clarity):
# 
# <img src="images/source_batch.png" />
# 
# Source sequences (also in int, but showing letters for clarity):
# 
# <img src="images/target_batch.png" />

# In[430]:


import numpy as np

def pad_sentence_batch(sentence_batch, pad_int):
    """Pad sentences with <PAD> so that each sentence of a batch has the same length"""
    max_sentence = max([len(sentence) for sentence in sentence_batch])
    return [sentence + [pad_int] * (max_sentence - len(sentence)) for sentence in sentence_batch]

def get_batches(targets, sources, batch_size, source_pad_int, target_pad_int):
    """Batch targets, sources, and the lengths of their sentences together"""
    for batch_i in range(0, len(sources)//batch_size):
        start_i = batch_i * batch_size
        sources_batch = sources[start_i:start_i + batch_size]
        targets_batch = targets[start_i:start_i + batch_size]
        pad_sources_batch = np.array(pad_sentence_batch(sources_batch, source_pad_int))
        pad_targets_batch = np.array(pad_sentence_batch(targets_batch, target_pad_int))
        
        # Need the lengths for the _lengths parameters
        pad_targets_lengths = []
        for target in pad_targets_batch:
            pad_targets_lengths.append(len(target))
        
        pad_source_lengths = []
        for source in pad_sources_batch:
            pad_source_lengths.append(len(source))
        
        yield pad_targets_batch, pad_sources_batch, pad_targets_lengths, pad_source_lengths


# ## Training function
# We're now ready to train our model. If you run into OOM (out of memory) issues during training, try to decrease the batch_size.

# In[431]:


# Split data to training and validation sets
train_source = source_letter_ids[batch_size:]
train_target = target_letter_ids[batch_size:]
valid_source = source_letter_ids[:batch_size]
valid_target = target_letter_ids[:batch_size]
(valid_targets_batch, valid_sources_batch, valid_targets_lengths, valid_sources_lengths) = next(get_batches(valid_target, valid_source, batch_size, 
                   source_letter_to_int['<PAD>'], target_letter_to_int['<PAD>']))

if (len(wrong_sentencess) > 10000):
    display_step = 100 # Check training loss after each of this many batches with large data
else:
    display_step = 20 # Check training loss after each of this many batches with small data

def train(epoch_i):
    
    global train_graph, train_op, cost, input_data, targets, lr
    global source_sequence_length, target_sequence_length, keep_prob
    
    # Test to see if graph already exists
    if os.path.exists(checkpoint + ".meta"):
        print("Reloading existing graph to continue training.")
        reloading = True    
        train_graph = tf.Graph()
    else:
        print("Starting with new graph.")
        reloading = False
        with train_graph.as_default():
            saver = tf.train.Saver()
    
    with tf.Session(graph=train_graph) as sess:    

        if reloading:
            saver = tf.train.import_meta_graph(checkpoint + '.meta')
            saver.restore(sess, checkpoint) 

            # Restore variables
            input_data = train_graph.get_tensor_by_name('input:0')
            targets = train_graph.get_tensor_by_name('targets:0')
            lr = train_graph.get_tensor_by_name('learning_rate:0')
            source_sequence_length = train_graph.get_tensor_by_name('source_sequence_length:0')
            target_sequence_length = train_graph.get_tensor_by_name('target_sequence_length:0')
            keep_prob = train_graph.get_tensor_by_name('keep_prob:0')

            # Grab the optimizer variables that were added to the collection during build
            cost = tf.get_collection("cost")[0]
            train_op = tf.get_collection("train_op")[0]

        else:
            sess.run(tf.global_variables_initializer())

        message = "" # Clear message to be sent in body of email
        
        for batch_i, (targets_batch, sources_batch, targets_lengths, sources_lengths) in enumerate(
                get_batches(train_target, train_source, batch_size,
                           source_letter_to_int['<PAD>'],
                           target_letter_to_int['<PAD>'])):

            # Training step
            _, loss = sess.run(
                [train_op, cost],
                {input_data: sources_batch,
                 targets: targets_batch,
                 lr: learning_rate,
                 target_sequence_length: targets_lengths,
                 source_sequence_length: sources_lengths,
                 keep_prob: keep_probability})

            batch = batch_i + 1 # batch_i starts at zero so batch is the batch number
            
            # Debug message updating us on the status of the training
            if (batch % display_step == 0 and batch > 0) or batch == (len(train_source) // batch_size):

                # Calculate validation cost
                validation_loss = sess.run(
                [cost],
                {input_data: valid_sources_batch,
                 targets: valid_targets_batch,
                 lr: learning_rate,
                 target_sequence_length: valid_targets_lengths,
                 source_sequence_length: valid_sources_lengths,
                 keep_prob: 1.0})

                line = 'Epoch {:>3}/{} Batch {:>6}/{} Inputs (000) {:>7} - Loss: {:>6.3f} - Validation loss: {:>6.3f}'                .format(epoch_i, epochs, batch, len(train_source) // batch_size, 
                        (((epoch_i - 1) * len(train_source)) + batch_i * batch_size) // 1000, loss, validation_loss[0])
                print(line)
                message += line + "\n"

        # Save model at the end of each epoch
        print("Saving graph...")
        saver.save(sess, checkpoint)
        
        return message # return message to be sent in body of email


# ## Prediction
# **Start here to use a saved and pre-trained graph.** Load the saved graph and compute some preditions.

# In[432]:


# Read batch_size from file
with open(GRAPH_PARAMETERS, 'r') as file:
    try:
        batch_size = int(file.read())
        print("Loaded batch_size = {}".format(batch_size))
    except ValueError:
        batch_size = 128
        print("Unable to load batch_size from file so using default 128.")
            
# In[433]:


# def source_to_seq(text, length):
#     '''Prepare the text for the model'''
# #     sequence_length = 7 # don't understand why set to 7
# #     sequence_length = 60
#     return [source_letter_to_int.get(word, source_letter_to_int['<UNK>']) for word in text] \
# + [source_letter_to_int['<PAD>']]*(length-len(text))


# In[434]:


def get_accuracy(wrong_sentencess, correct_sentencess):
    
    # Convert sentences to IDs
    source_letter_ids, target_letter_ids = produce_letter_ids(wrong_sentencess, correct_sentencess)

    pad = source_letter_to_int["<PAD>"]
    eos = source_letter_to_int["<EOS>"]
    matches = 0
    total = 0
    display_step = 10

    loaded_graph = tf.Graph()
    with tf.Session(graph=loaded_graph) as sess:

        # Load saved model
        loader = tf.train.import_meta_graph(checkpoint + '.meta')
        loader.restore(sess, checkpoint)

        # Load graph variables
        input_data = loaded_graph.get_tensor_by_name('input:0')
        logits = loaded_graph.get_tensor_by_name('predictions:0')
        source_sequence_length = loaded_graph.get_tensor_by_name('source_sequence_length:0')
        target_sequence_length = loaded_graph.get_tensor_by_name('target_sequence_length:0')
        keep_prob = loaded_graph.get_tensor_by_name('keep_prob:0')

        for batch_i,(targets_batch, sources_batch, targets_lengths, sources_lengths)         in enumerate(get_batches(target_letter_ids, source_letter_ids, batch_size, 
                                 source_letter_to_int['<PAD>'], target_letter_to_int['<PAD>'])):

            # Multiply by batch_size to match the model's input parameters
            answer_logits = sess.run(logits, {input_data: sources_batch, 
                                              target_sequence_length: targets_lengths, 
                                              source_sequence_length: sources_lengths,
                                              keep_prob: 1.0})

            for n in range(batch_size):
                answer = "".join([target_int_to_letter[i] for i in answer_logits[n] if (i != pad and i != eos)])
                target = correct_sentencess[batch_i * batch_size + n]
                total += 1
                if (answer == target):
                    matches += 1

            if batch_i % display_step == 0 and batch_i > 0:
                print('Batch {:>6}/{} - Accuracy: {:.1%}'.format(batch_i, 
                                                                 len(wrong_sentencess)//batch_size,
                                                                 matches/total))

        print("Final accuracy = {:.1%}\n".format(matches/total))
        
        return matches/total


# # Train graph by looping through epochs
# Compute accuracy after each epoch and return in email

# In[435]:

import time

start = time.time()

# Run through all the epoch, computing the accuracy after each and sending the results via email
for epoch_i in range(1, epochs + 1):
    
    message = get_hyperparameters_message()
    message += train(epoch_i)

    # Print time spent training the model
    end = time.time()
    seconds = end - start
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    print("Model Trained in {}h:{}m:{}s and Saved".format(int(h), int(m), int(s)))
    message += "\nModel training for {}h:{}m:{}s and saved.".format(int(h), int(m), int(s))
    
    # Get current accuracy
    accuracy = get_accuracy(validation_source_sentences, validation_target_sentences)
    message += "\nCurrent accuracy = {:.1%}".format(accuracy)

print("\nTraining completed.")
