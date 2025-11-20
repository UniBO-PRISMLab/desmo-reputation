import random
from typing import List

from Indexer import Indexer
from Source import Producers
import constants


def turn_indexers(indexers: List[Indexer]) -> int:
   
    turnable_indexers = [indexer for indexer in indexers if not Producers[indexer.indexed_sources[0]].is_virtual]
    to_turn = random.sample(turnable_indexers, min(constants.NUMBER_OF_MALICIOUS_SOURCES, len(turnable_indexers)))
    for indexer in to_turn:
        indexer.trusted = not indexer.trusted
        for source_id in indexer.indexed_sources:
            Producers[source_id].trusted = indexer.trusted
    return len(to_turn)

def turn_indexers_good(indexers: List[Indexer]) -> int:
    counter = 0
    for indexer in indexers:
        if not indexer.trusted:
            counter+=1
        indexer.trusted = True
        for source_id in indexer.indexed_sources:
            Producers[source_id].trusted = indexer.trusted
    return counter