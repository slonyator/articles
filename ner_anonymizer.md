# Data Guardian: Empowering Privacy with NER-driven Text Anonymization

## Motivation 

In the contemporary landscape of Machine Learning development within the 
European Union, particularly under the looming shadow of the Artificial 
Intelligence Act (AIA), data privacy has become a paramount concern. Weather 
it's classical machine learning, deep learning, or LLMs (Large Language Models) 
is concerned about the impact of the AIA (Artificial Intelligence Act). The AIA 
is a proposal for a regulation of the European Union.

The AIA, in essence, serves as a regulatory framework for the ethical and 
responsible use of artificial intelligence. As companies grapple with the 
implications, one clear challenge stands out: safeguarding data privacy. The 
term "sensitive data" encompasses a spectrum, including names, addresses, phone 
numbers, email addresses, and more.

In this concise tutorial, we aim to demonstrate the practical application of 
Named Entity Recognition (NER) as a tool for anonymizing sensitive data within 
texts.

## Understanding Named Entity Recognition (NER)

Named Entity Recognition (NER) stands as a subtask within information 
extraction. Its primary objective is to identify and categorize named entities 
within unstructured text. These entities can span a variety of predefined 
categories, such as person names, organizations, locations, medical codes, time 
expressions, quantities, monetary values, percentages, and more.

By understanding and utilizing NER, we can effectively address the challenge of 
safeguarding sensitive information within textual data. 

## Implementation Walkthrough

### Prerequisites

To follow this tutorial, ensure you have Python version 3.8 or higher. Install 
the required libraries using the following commands:

```bash
pip install Faker
pip install flair
```

and that's it! You're ready to go.

### NER Code Implementation

Flair is a powerful Natural Language Processing (NLP) library that serves as a 
very simple framework for state-of-the-art NLP, developed by Humboldt University
of Berlin and friends. It empowers users with cutting-edge models for tasks like
Named Entity Recognition (NER), sentiment analysis, part-of-speech tagging 
(PoS), and more. Beyond its prowess in NLP, Flair operates as a versatile text 
embedding library, offering interfaces to seamlessly utilize and combine 
different word and document embeddings, including Flair embeddings and various 
transformers. As a PyTorch NLP framework, Flair leverages the power of PyTorch, 
facilitating the training of custom models and experimentation with innovative 
approaches using Flair embeddings and classes. With support for a diverse range 
of languages and special features for biomedical data, Flair emerges as a 
comprehensive solution for advanced natural language processing tasks.

Of course you could extend the model to include more entities, but for the sake
of this tutorial, we will focus on the pre-trained model for English, which you
can find on Huggingface. 

Here is an example text:

```python
text = (
        f"XYZ Solutions, is thrilled to announce the arrival of Jane "
        f"Smith as their new Project Manager. She'll be working at their "
        f"main office in Cityville."
    )
```

and this three lines of code build the nucleus of our anonymization tool. 

```python
# Loading the model from HuggingFace
ner_model = SequenceTagger.load("flair/ner-english-large")

# Create a sentence object
sentence = Sentence(text)

# run NER over the sentence
ner_model.predict(text)
```

The output looks as follows:

```python
print(sentence)
```

"Software Solutions, is thrilled to announce the arrival of Jane Smith as their new 
Project Manager. She'll be working at their main office in Cityville." 
→ ["Software Solutions"/ORG, "Jane Smith"/PER, "Cityville"/LOC]


As we see, model identified three entities. We will anonymize names and 
locations while, but the procedure would be the same for other entities. 

### Anonymizing Entities with Fake Names

```python
faked_text = text

# Use faker package to generate fake names & addresses
fake = Faker()

for entity in sentence.get_spans("ner"):
    if entity.tag == "PER":
        entity_text = entity.text
        replacement_text = fake.name()
        faked_text = faked_text.replace(entity_text, replacement_text)

    if entity.tag == "LOC":
        entity_text = entity.text
        replacement_text = fake.city()
        faked_text = faked_text.replace(entity_text, replacement_text)

print(faked_text)
```

The output would be:

Software Solutions, is thrilled to announce the arrival of Robert Rivera as 
their new Project Manager. She'll be working at their main office in New 
Kristin.

This result, though entirely fictitious, appears realistic.

## Conclusion

This tutorial demonstrates the practical use of Named Entity Recognition (NER) 
for anonymizing sensitive data within texts. The effectiveness of anonymization 
depends on the quality of the NER model used. While it cannot guarantee complete
anonymization, advancements in Large Language Models (LLMs) and NER models will 
likely enhance the efficiency of this technique over time.
