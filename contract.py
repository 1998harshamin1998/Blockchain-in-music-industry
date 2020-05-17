from time import time


class Contract:

    def __init__(self, distributorAPI, producerID, albumID, amount_per_access):
        self.distributorAPI = distributorAPI
        self.producerID = producerID
        self.albumID = albumID
        self.amount_per_access = amount_per_access
        self.timestamp = time()