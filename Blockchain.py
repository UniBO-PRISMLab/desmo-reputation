import constants, utils
import json
import os
import random
import sys
from datetime import datetime, timezone

# INDEXER_REGISTRATION_WINDOW = 12.0 # in seconds

# Hardcoded Blockchain List 
BLOCKCHAIN_STORE = {
    "ethereum": 12.0,
    "avalanche": 2.0,
    "polygon": 2.0,
    "optimism": 2.0,
    "binance": 3.0,
}

# Global variable to assign an ID to Blockchains
blockchain_incremental_idx = 1

# Blockchains Master Dictionary
Blockchains = {}

def initiateBlockchains( num_blockchains = len(BLOCKCHAIN_STORE), sequential = False):
    """
    Initializes the Blockchains dictionary with predefined blockchains.
    :param num_blockchains: Number of blockchains to initialize, defaults to the length of BLOCKCHAIN_STORE.
    :param sequential: If True, sets the average block time to 0 for ideal sequential processing.
    :param n_epochs: Number of epochs for which the blockchains are initialized (in seconds).
    """
    counter = 0
    for name, average_block_time in BLOCKCHAIN_STORE.items():
        if sequential:
            average_block_time = 0.0 # Set to 0 for IDEAL sequential processing
        generateNewBlockchain(name, average_block_time)
        counter += 1
        if counter >= num_blockchains:
            break

# Factory
def generateNewBlockchain(name, average_block_time = 10.0):
    """ Factory method to generate a new Blockchain and add it to the Blockchains dictionary. """
    global Blockchains, blockchain_incremental_idx
    _blockchain = Blockchain(name, average_block_time = average_block_time)
    Blockchains[_blockchain.idx] = _blockchain
    return _blockchain.idx

def calculateWaitingBlocks(base_fee):
    """
    Calculates the waiting time based on the base fee.
    This is a placeholder function that can be modified to implement actual waiting time calculation logic.
    
    :param base_fee: The base fee for the transaction.
    :return: The wating time in blocks (i.e. it is not really a time)
    """

    # FIXME: This is a placeholder function, actual waiting time calculation logic can be added later.
    if base_fee <= 15.0:
        return 0
    elif base_fee <= 25.0:
        return 1
    elif base_fee <= 100.0:
        return 2 + ((base_fee - 25.0) // 15) # floor
    else:
        return 6 + ((base_fee - 100.0) // 10) # floor
    

def generateTrace(name):
    """
    Generates a trace for the blockchain.
    This is a placeholder function that can be modified to implement actual trace generation logic.
    
    :param name: The name of the blockchain for which the trace is generated.
    :param n_epochs: The number of epochs for which the trace is generated.
    :return: A placeholder trace (can be modified to return actual data).
    :mult: A multiplier for conversion into ETH
    """
    trace = {}

    first_block_time = 0
    block_progressive = 0

    block_num = 0
    block_time = 0
    tx_count = 0
    temp_base_fee = 0.0
    base_fee = 0.0
    gas_price = 0.0
    max_fee = 0.0
    waiting_blocks = 0.0
    coin_price = 0.0

    for tracefile in sorted(os.listdir(f"traces_chain/merged/{name}_with_prices")):
        if tracefile.startswith(name):
            with open(os.path.join(f"traces_chain/merged/{name}_with_prices", tracefile), "r") as f:
                print(f"Processing trace file: {tracefile}")
                for _line in f.readlines():

                    # Skip title line
                    if _line.startswith("block_num"):
                        continue
                    line = _line.strip().split(",")

                    block_time = float(line[20])
                    #block_time = datetime.strptime(line[20], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp() #XXX
                    
                    # It's the first block
                    if block_num == 0:
                        # first block
                        block_num = int(line[0])
                        first_block_time = block_time

                    # It is a new block
                    if int(line[0]) != block_num:
                        # update numbers and append to dict
                        if tx_count > 0:
                            trace[block_progressive] = {
                                "block_time": block_time - first_block_time,
                                "tx_count": tx_count,
                                "base_fee": (base_fee / tx_count),
                                "gas_price": (gas_price / tx_count),
                                "max_fee": (max_fee / tx_count),
                                "waiting_blocks": int(waiting_blocks / tx_count),
                                "coin_price": (coin_price / tx_count)
                            }
                        else:
                            trace[block_progressive] = {
                                "block_time": block_time - first_block_time,
                                "tx_count": 0,
                                "base_fee": trace[block_progressive - 1]["base_fee"] if block_progressive > 0 else 0.0,
                                "gas_price": trace[block_progressive - 1]["gas_price"] if block_progressive > 0 else 0.0,
                                "max_fee": trace[block_progressive - 1]["max_fee"] if block_progressive > 0 else 0.0,
                                "waiting_blocks": trace[block_progressive - 1]["waiting_blocks"] if block_progressive > 0 else 0,
                                "coin_price": trace[block_progressive - 1]["coin_price"] if block_progressive > 0 else 0.0
                            }
                        # reset counters
                        tx_count = 0
                        base_fee = 0.0
                        gas_price = 0.0
                        max_fee = 0.0
                        waiting_blocks = 0.0
                        block_progressive += 1
                        coin_price = 0.0

                    # Record transaction data
                    block_num = int(line[0])
                    if line[16] == "True" and line[13] == "2": # if the transaction is valid and it follows the EIP-1559 standard
                        if float(line[12]) < float(line[15]): # if the max fee is not used, then the base fee is the difference between the gas price and max prio fee
                            temp_base_fee = (float(line[12]) - float(line[14]))  / 1e9
                        else:
                            if temp_base_fee == 0.0:
                                continue
                        tx_count += 1
                        #curr_base_fee = (float(line[12]) - float(line[14]))  / 1e9  
                        # # Convert to Chain-specific Gwei, base fee is the difference between the gas price and max prio fee if the max fee is not used, otherwise
                        base_fee += temp_base_fee
                        gas_price += float(line[12]) / 1e9  # Convert to Chain-specific Gwei
                        max_fee += float(line[15]) / 1e9  # Convert to Chain-specific Gwei
                        waiting_blocks += calculateWaitingBlocks(temp_base_fee)
                        coin_price += float(line[25])  # Coin price in USD
    with open(f"traces_chain/{name}_trace.json", "w") as f:
        json.dump(trace, f, indent=4)
    

def selectRelayChain(timestamp):
    """
    Selects a relay chain from the Blockchains dictionary.
    For now, it simply returns the first blockchain in the dictionary.
    This can be modified to implement more complex selection logic.
    
    :return: The selected relay chain and its expected objective value.
    :rtype: tuple (Blockchain, float)
    """

    # If a favourite chain is specified, return it
    if constants.FAV_CHAIN > 0:
        if constants.FAV_CHAIN in Blockchains.keys():
            return Blockchains[constants.FAV_CHAIN]
        else:
            raise ValueError(f"Favourite chain index {constants.FAV_CHAIN} does not exist in Blockchains.")
        
    # Otherwise, select the chain with the minimum expected delay based on the timestamp
    max_objective = 0
    relay_chain = None

    if Blockchains:
        for _blockchain in Blockchains.values():
            last_block_id = _blockchain.find_previous_block_id(timestamp) 
            if last_block_id is not None:
                expected_delay = ( ( _blockchain.trace[last_block_id]["waiting_blocks"] + 1 )  * _blockchain.average_block_time ) - ( _blockchain.average_block_time / 2.0 ) # Subtract half of the average block time to account for the current block being processed
                expected_cost = _blockchain.trace[last_block_id]["base_fee"] * _blockchain.trace[last_block_id]["coin_price"] # FIXME whait if zero transactions??
                expected_objective = utils.calculateObjectiveFunctionValue(expected_cost, expected_delay)
                if expected_objective > max_objective:
                    max_objective = expected_objective
                    relay_chain = _blockchain
            else:
                return random.choice(list(Blockchains.values())) # If no block is found, return a random blockchain with an objective of -1.0
    else:
        raise ValueError("No blockchains available to select as relay chain.")
    return relay_chain

def compute_optimal_response_timestamp_and_cost(timestamp_now):
    """
    Computes the optimal response timestamp and cost based on the current timestamp.
    
    :param timestamp_now: The current timestamp.
    :return: The optimal response timestamp and cost.
    """

    max_objective = 0.0

    for _relay_chain in Blockchains.values():
        _timestamp, _cost = _relay_chain.compute_response_timestamp_and_cost(timestamp_now)
        _delay = (_timestamp - timestamp_now) if _timestamp > timestamp_now else 0.0
        _objective = utils.calculateObjectiveFunctionValue(_cost, _delay)
        if _objective > max_objective:
            max_objective = _objective
            optimal_timestamp = _timestamp
            optimal_cost = _cost
    
    return optimal_timestamp, optimal_cost
    
def resolve_pending_transaction(transaction_id):
    """
    Resolves the pending transactions by popping it from the list.
    """

    # if transaction id is in the pending transactions, remove it
    for _blockchain_id in Blockchains.keys():
        for i, transaction in enumerate(Blockchains[_blockchain_id].pending_transactions):
            if transaction == transaction_id:
                return Blockchains[_blockchain_id].pending_transactions.pop(i)
    
    # If the transaction is not found, rais a ValueError
    raise ValueError(f"Transaction with ID {transaction_id} not found in pending transactions.")

class Blockchain:

    def __init__(self, name, average_block_time=10.0):
        """
        Initializes the Blockchain with a specified average block time.
        :param average_block_time: The average time between blocks in seconds.
        """

        # Assign incremental ID
        global blockchain_incremental_idx
        self.idx = blockchain_incremental_idx
        blockchain_incremental_idx += 1

        self.name = name
        self.average_block_time = BLOCKCHAIN_STORE[name] if name in BLOCKCHAIN_STORE else average_block_time
        self.pending_transactions = []
        if not os.path.exists(f"traces_chain/{name}_trace.json"):
            generateTrace(name)
        # Load the trace from the file if it exists
        json_trace = json.load(open(f"traces_chain/{name}_trace.json", "r")) 
        self.trace ={int(k): v for k, v in json_trace.items()}

    def add_transaction(self, transaction):
        """
        Adds a transaction to the pending transactions list.
        
        :param transaction: The transaction to be added.
        """
        self.pending_transactions.append(transaction)
    
    def find_previous_block_id(self, timestamp):
        """
        Finds the previous block based on the given timestamp.
        
        :param timestamp: The timestamp for which to find the previous block.
        :return: The previous block's timestamp or None if not found.
        """
        # Iterate through the trace to find the previous block
        for block_id in sorted(self.trace.keys(), reverse=True):
            if self.trace[block_id]["block_time"] <= timestamp:
                return block_id
        return None
    
    def compute_response_timestamp_and_cost(self, timestamp_now):
        """
        Computes the timestamp for the response based on the current timestamp.
        
        :param timestamp_now: The current timestamp.
        :return: The computed response timestamp and the cost.
        """

        last_block_id = self.find_previous_block_id(timestamp_now)
        if last_block_id is not None:
            commitreveal_block_id = last_block_id + 1 + self.trace[last_block_id]["waiting_blocks"]
            if commitreveal_block_id in self.trace:
                score_block_id = commitreveal_block_id + 1 + self.trace[commitreveal_block_id]["waiting_blocks"]
                if score_block_id in self.trace:
                    return self.trace[score_block_id]["block_time"], self.trace[score_block_id]["base_fee"] * self.trace[score_block_id]["coin_price"] # FIXME substitute base_fee with gas_cost?
                
        return timestamp_now + self.average_block_time * 2, self.trace[last_block_id]["base_fee"] * self.trace[last_block_id]["coin_price"]
    
if __name__ == "__main__":
    generateTrace("ethereum")
    generateTrace("avalanche")
    generateTrace("polygon")
    generateTrace("optimism")
    generateTrace("binance")

