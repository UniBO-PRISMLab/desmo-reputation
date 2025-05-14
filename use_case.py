import numpy as np

from typing import List

from Source import Producers
import constants

from Indexer import Indexer


def define_start_attack_epoch(
    number_of_epochs: int = constants.N_EPOCHS, start_epoch_chunk: int = 2, epoch_chunks: float = 3.0
) -> int:
    """
    Randomly selects the start epoch for an attack after a reputation-building phase.

    The simulation timeline is divided into `epoch_chunks` equal parts.
    The attack can start randomly within the `start_epoch_chunk`-th chunk,
    where counting starts from 1. For example, if `epoch_chunks` = 3 and
    `start_epoch_chunk` = 2, the attack will occur randomly between epochs
    N/3 and 2N/3.

    Parameters
    ----------
    number_of_epochs : int, optional
        Total number of epochs in the simulation (default is constants.N_EPOCHS).
    start_epoch_chunk : int, optional
        The chunk index (1-based) from which the attack can start (default is 2).
    epoch_chunks : float, optional
        Total number of equal-length chunks the simulation is divided into (default is 3.0).

    Returns
    -------
    int
        A randomly selected epoch number within the target chunk for the attack to begin.

    Raises
    ------
    ValueError
        If start_epoch_chunk is less than 1 or greater than epoch_chunks.

    Examples
    --------
    >>> define_start_attack_epoch(90, 2, 3)
    37  # random value between 30 and 59
    """
    if start_epoch_chunk < 1 or start_epoch_chunk > epoch_chunks:
        raise ValueError("start_epoch_chunk must be between 1 and epoch_chunks (inclusive).")

    chunk_size = int(number_of_epochs / epoch_chunks)
    start_epoch = (start_epoch_chunk - 1) * chunk_size
    return np.random.randint(chunk_size) + start_epoch


def turn_indexers(indexers: List[Indexer], owner: int = 0) -> int:
    """
    Turns a subset of trusted indexers into malicious ones and the malicious ones in trusted. 

    returns the number of turned indexers
    """ 
    turned_indexers = 0
    for indexer in indexers:
        if indexer.owner == owner:
            turned_indexers+=1
            indexer.trusted = not indexer.trusted
            for source_id in indexer.indexed_sources:
                Producers[source_id].trusted = indexer.trusted
    return turned_indexers