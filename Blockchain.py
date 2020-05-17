from Block import *
from flask import Flask
import logging, sys
import json
from textwrap import dedent
from time import time
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask import Flask, jsonify,request, render_template, redirect
from uuid import uuid4
from new_contract import ContractForm
from contract import Contract
# from urlparse import urlparse
import requests

class Blockchain:
    __Difficulty = 2

    def __init__(self):


        self.chain = []
        self.create_genesis_block()
        self.list_of_contracts = []
        self.pending_transaction = []
        self.nodes_set = set()


    def create_genesis_block(self):
        """
                A function to generate genesis block and appends it to
                the chain. The block has index 0, previous_hash as 0, and
                a valid hash.
                """
        genesis_block = Block(0, [], "0")
        genesis_block.blockHash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        """
        A quick python way to retrieve the most recent block in the chain. Note that
        the chain will always consist of at least one block (i.e., genesis block)
        """
        return self.chain[-1]

    def proof_of_work(self, block):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.proof = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.__Difficulty):
            block.proof += 1
            computed_hash = block.compute_hash()

        return computed_hash

    @staticmethod
    def is_valid_proof(block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.__Difficulty) and
                block_hash == block.compute_hash())

    def add_block(self, Block, proof):

        previousHash = self.last_block.blockHash
        if previousHash != Block.previousHash:
            return False

        if not Blockchain.is_valid_proof(Block, proof):
            return False
        else:
            Block.blockHash = proof
        self.chain.append(Block)
        for node in blockchain.nodes_set:
            url = node + "resolve"
            response = requests.get(url)

        return True

    def add_contract(self, contract):
        self.list_of_contracts.append(contract)

    def contract_to_chain(self, transaction):
        last_block = self.last_block
        new_block = Block(last_block.index + 1,
                          transaction,
                          last_block.blockHash)
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        return new_block.index

    def mine_blocks(self, transaction, transaction_id):
        last_block = self.last_block
        new_block = Block(last_block.index + 1,
                          transaction,
                          last_block.blockHash)
        proof = self.proof_of_work(new_block)
        if Blockchain.update_Semaphore(transaction_id):
            self.add_block(new_block, proof)
            return new_block.index



    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print('{last_block}')
            print('{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previousHash'] != last_block['blockHash']:
                return False

            # # Check that the Proof of Work is correct
            # if not self.is_valid_proof(last_block, block['blockHash']):
            #     return False

            last_block = block
            current_index += 1

        return True

    def resolve_chain_conflicts(self):
        neighbours = self.nodes_set
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            app.logger.info('NODE IS: ' + node)
            print(node, sys.stderr)
            url = node + 'getchain'
            response = requests.get(url)

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                print(length, sys.stderr)
                print(chain, sys.stderr)

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

            # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = Blockchain.chain_decode(new_chain)
            return True

        return False

    def chain_encode(self):
        chain_data = []
        for block in self.chain:
            chain_data.append(block.__dict__)
        return chain_data


    @staticmethod
    def chain_decode(dchain):
        chain_data = []
        for block in dchain:
            new_block = Block(block['index'],
                              block['transactions'],
                              block['previousHash'])

            new_block.timestamp = block['timestamp']
            new_block.blockHash = block['blockHash']
            new_block.proof = block['proof']
            chain_data.append(new_block)

        return chain_data

    def getNodes(self, sUrl):
        url = 'http://localhost:5000/sendnodes'
        data = {"node_address": sUrl}
        headers = {'Content-Type': "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)

        if response.status_code == 200:
            length = response.json()['length']
            self.nodes_set.update(response.json()['nodes'])
            return True
        else:
            return False

    @staticmethod
    def update_Semaphore(transaction_id):
        url = 'http://localhost:5000/semaphore'
        data = {
                "transaction_id": transaction_id
                }

        headers = {'Content-Type': "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            #length = response.json()['length']
            return response.json()['entry']
        else:
            return False


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
app.config['SECRET_KEY'] = 'you-will-never-guess'


# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/generate_contracts', methods=['POST', 'GET'])
def new_contract():
    form = ContractForm()

    if form.validate_on_submit():
        distributorAPI = form.distributorAPI.data
        producerID = form.producerID.data
        albumID = form.albumID.data
        amount_per_access = form.amount_per_access.data

        c = Contract(distributorAPI, producerID, albumID, amount_per_access)

        cont = [{
            'distributorAPI': distributorAPI,
            'producerID': producerID,
            'albumID': albumID,
            'amount_per_access': amount_per_access,
            'timestamp': time()
        }]

        blockchain.add_contract(c)

        blockchain.contract_to_chain(cont)

        return redirect('/chain')

    return render_template('newContract.html', form=form)

    # return "We'll add a new transaction"


@app.route('/chain', methods=['GET'])
def full_chain():
    # response = {
    #     'chain': blockchain.chain,
    #     'length': len(blockchain.chain),
    # }
    chain = blockchain.chain
    return render_template('chain.html', chain=chain)


@app.route('/getchain', methods=['GET'])
def get_chain():

    response = {
        'chain': blockchain.chain_encode(),
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/sendnodes', methods=['POST', 'GET'])
def register_new_peers():
    blockchain.nodes_set.add(request.host_url)
    blockchain.nodes_set.add(request.get_json()["node_address"])
    response = {
        'nodes': list(blockchain.nodes_set),
        'length': len(blockchain.nodes_set),
    }

    return jsonify(response), 200


@app.route('/register_with_node', methods=['POST', 'GET'])
def register_nodes():
    print(request.host_url, sys.stderr)

    # node = request.get_json()['node_address']
    #
    # #nodes = values.get('nodes')
    # if node is None:
    #     return "Error: Please supply a valid list of nodes", 400
    #
    #
    # nodes_set.add(node)
    #
    # response = {
    #     'message': 'New nodes have been added',
    #     'total_nodes': list(nodes_set),
    # }
    # return jsonify(response), 201

    # node_address = request.get_json()["node_address"]
    # if not node_address:
    #     return "Invalid data", 400


    # data = {"node_address": request.host_url}
    # headers = {'Content-Type': "application/json"}
    # response = requests.post("http://127.0.0.1:5000" + "/register_node",
    #                          data=json.dumps(data), headers=headers)
    blockchain.getNodes(request.host_url)
    response = {
        'nodes': list(blockchain.nodes_set),
        'length': len(blockchain.nodes_set),
    }

    for node in blockchain.nodes_set:
        url = node + "resolve_nodes"
        response2 = requests.get(url)

    return jsonify(response), 200


@app.route('/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_chain_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain_encode()
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain_encode()
        }

    return jsonify(response), 200

@app.route('/mine', methods=['POST', 'GET'])
def Mine():
    transaction = request.get_json()["transaction"]
    transaction_id = request.get_json()["transaction_id"]
    blockchain.mine_blocks(transaction, transaction_id)

    return redirect('/chain')


@app.route('/resolve_nodes', methods=['GET'])
def Nodesconsensus():
    transaction_id = request.get_json()["transaction_id"]
    response = blockchain.getNodes(request.host_url)
    response = {
        'nodes': list(Blockchain.nodes_set),
        'length': len(Blockchain.nodes_set),
    }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
