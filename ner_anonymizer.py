import hashlib

from faker import Faker
from flair.data import Sentence
from flair.models import SequenceTagger

if __name__ == "__main__":
    text = (
        f"Software Solutions, is thrilled to announce the arrival of Jane "
        f"Smith as their new Project Manager. She'll be working at their "
        f"main office in Cityville."
    )

    # Loading the model from HuggingFace
    ner_model = SequenceTagger.load("flair/ner-english-large")

    # Make a sentence object
    sentence = Sentence(text)

    # run NER over the sentence
    ner_model.predict(sentence)

    print(sentence)

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

    hashed_text = text

    for entity in sentence.get_spans("ner"):
        if entity.tag == "PER":
            entity_text = entity.text
            replacement_text = hashlib.sha256(entity_text.encode()).hexdigest()
            hashed_text = hashed_text.replace(entity_text, replacement_text)

        if entity.tag == "LOC":
            entity_text = entity.text
            replacement_text = hashlib.sha256(entity_text.encode()).hexdigest()
            hashed_text = hashed_text.replace(entity_text, replacement_text)

    print(hashed_text)
