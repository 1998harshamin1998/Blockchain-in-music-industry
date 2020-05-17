import time
from hashlib import sha256
import json


class Block:

    def __init__(self, index, transactions, previousHash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previousHash = previousHash
        self.blockHash = None
        self.proof = None

    def compute_hash(self):
        """
        Returns the hash of the block instance by first converting it
        into JSON string.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


    def __repr__(self):
        return 'index: ' + str(self.index) + "Proof: " + str(self.proof) + "Transactions: " + str(self.transactions) + " timestamp: " + str(self.timestamp)  + " previousHash: " + str(self.previousHash)