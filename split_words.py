# -*- coding: utf-8 -*-
"""
Created on Mon Jul  9 14:09:19 2018

@author: sundsudh
"""
#Import the required libraries
import re
import time
import os

#Functional Utilities

#Display time
intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
    )

def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        if value := seconds // count:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append(f"{value} {name}")
    return ', '.join(result[:granularity])

#Check for duplicates before adding to dict
def addToDict(self, key, val):
    try:
        self[key] = val
    except KeyError:
        self[key].append(val)

class parseTextFile:
    
    def __init__(self):
        self.my_lang_dict = {} #Dictionary to store exact word to word matches
        self.my_issue_list = []
        self.misMatchCount = 0
        self.sourceListLen = 0
        self.targetListLen = 0
        
    def readFromFile(self, fileName):
        with open(fileName, encoding='UTF-8') as file:
            
            for line in file:
                
                # Skip the header lines
                if not line.startswith("*$*OVERPROOF*$*"):

                    # Process the words into dictionary
                    wordList, correctedList = line.split("||@@||")
                    
                    #Tokenize the list elements
                    tmpwordList = wordList.split(" ")
                    #wordList = [re.sub('[^a-zA-Z0-9]+', '', _) for _ in wordList.split(" ")]
                    tmpcorrectedList = correctedList.split(" ")
                    #correctedList = [re.sub('[^\w\s]', '', _) for _ in correctedList.split(" ")]
                    self.sourceListLen = len(tmpwordList)
                    self.targetListLen = len(tmpcorrectedList)
                    if self.sourceListLen == self.targetListLen:
                        
                        #Frame the language dictionary
                        for key,value in zip(tmpwordList, tmpcorrectedList):
                            
                            #This is to assert that string with only special characters are not used
                            #It should be a combination of strings with special characters
                            #EX.Ignore "," accept "Hello,"
                            tmp_value = re.sub(r'[^\w\s]','',value)
                            if (key != value) and len(tmp_value.strip()) > 0:
                                addToDict(self.my_lang_dict, key.strip(), value.strip())

                    # Write lines to file that differ by one word
                    elif self.sourceListLen + 1 == self.targetListLen:

                        self.my_issue_list.append(wordList)
                        self.my_issue_list.append(correctedList)

           
        #print ("Total number of mismatched lines:", self.misMatchCount)      
        return self.my_lang_dict, self.my_issue_list
 
def printDict(myDict):
    for k,v in myDict.items():
        print(f"{k}:{v}")
        
def writeToFile(fileName, my_list):

    filePath = os.path.dirname(os.path.realpath(__file__)) + "\\" + str(fileName)

    ctr = 0
    #Write the contents to file
    with open(filePath, "wb") as file:
        for value in my_list:
            if ctr != 0:
                file.write(b"\n")
            file.write(value.encode('utf8'))
            ctr += 1

# Main function wrapper
if __name__ == "__main__":  

    #Start time
    startTime = time.time()    

    dir_path = r"C:\\Users\\sundsudh\\Downloads\\dataset1\\dataset1\\rawTextAndHumanCorrectionPairs"
    os.chdir(dir_path)
    text_files = [file for file in os.listdir() if os.path.isfile(file) and file.endswith(".txt")]

    #Call the Text file parser
    pt = parseTextFile()

    # Read the files sequentially
    for file in text_files:

        my_dict,my_issue_list = pt.readFromFile(file)

    #Write the contents to file
    writeToFile("wrong_words.txt", list(my_dict.keys()))
    writeToFile("correct_words.txt", list(my_dict.values()))

    writeToFile("files_differ_by_1_word.txt", my_issue_list)

    #Print the result
    runTime = int(time.time() - startTime)
    print(f"Parsing completed in :{display_time(runTime)} ")
    
