# Grammar Module – Natural Language Command Parsing

## Introduction

The Grammar Module implements Context-Free Grammar (CFG) parsing for English imperative commands.


### Its primary responsibility is to:
	•	Identify the syntactic structure of a sentence
	•	Validate whether the sentence is a valid command
	•	Enable structure enumeration (multiple sentence forms → same intent)
	•	Support syntax-directed translation into executable code

This module does not decide which method to execute.
It only determines the sentence structure.



## Table of Contents 
	•	Overview￼
	•	Grammar Symbols￼
	•	Grammar Rules (BNF)￼
	•	Examples￼

# Grammar Symbols

We compress tokens into simplified structural symbols:

### Symbol	Meaning
	•	V	Verb / Action head
	•	O	Object noun phrase
	•	IO	Indirect object (pronoun)
	•	A	Adverbial (adverb or prepositional phrase)
	•	C	Complement (usually adjective)

Numbers are ignored in structural shape (they are values inside noun phrases).

### Example:
```
walk 3 steps slowly
```

Compressed sequence:

```
V O A
```

# Grammar Rules (BNF Style)
```
<command> ::= <verb_phrase>
```

```
<verb_phrase> ::= 

      <verb>                                               → SV
      <verb> <object>                                      → SVO
      <verb> <adverbial>                                   → SVA
      <verb> <object> <adverbial>                          → SVOA
      <verb> <indirect_object> <object>                    → SVOO 
      <verb> <object> <complement>                         → SVOC 
      <verb> <indirect_object> <object> <adverbial>
```

## Supporting rules: 

```
<object>          ::= NOUN_PHRASE
<indirect_object> ::= PRONOUN | NOUN_PHRASE
<complement>      ::= ADJECTIVE | NOUN_PHRASE 
<adverbial>       ::= ADVERB | PREPOSITIONAL_PHRASE
```

# Examples
`
SV
`

Sentence:
`
walk
`

Structure:
`
V
`

Label:
`
SV
`

`
SVO
`

Sentence:
`
show transactions
`

Structure:
`
V O
`

Label:
`
SVO
`

`
SVA
`

Sentence:
`
walk slowly
`

Structure:
`
V A
`

Label:
`
SVA
`

`
SVOA
`

Sentence:
`
walk 3 steps slowly
`

Structure:
`
V O A
`

Label:
`
SVOA`

`
SVOO
`

Sentence:
`
give me the book
`

Structure:
`V IO O`


Label:
`
SVOO`

`
SVOC
`

Sentence:
`
make it warmer
`

Structure:
`
V O C
`

Label:
`
SVOC
`