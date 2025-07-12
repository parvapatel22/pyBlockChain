import hashlib 
import json 
from time import time 
from textwrap import dedent
from uuid import uuid4
from flask import Flask, jsonify, request
from markupsafe import Markup, escape




class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        
        #Create a genesis block 
        self.new_block(previous_hash = 1,proof = 100)
        
    def proof_of_work(self,last_proof):
        """
        Find a number p such that hash(pp') contains 
        leading 4 zeroes 
        p : prev proof
        p': new proof
        last_proof : int
        return : int 
        """
        proof = 0
        while self.valid_proof(last_proof,proof) is False:
            proof += 1
        return proof
    
    @staticmethod
    def valid_proof(last_proof,proof):
        """
        Validates the proof does it contain 4 leading zeroes
        param : last_proof : int
        proof : int 
        return : Bool  
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
        
    
    def new_block(self,proof,previous_hash = None):
        block = {
            'index' : len(self.chain) + 1,
            'timestamp' : time(),
            'transactions' : self.current_transactions,
            'proof' : proof,
            'previous_hash' : previous_hash or self.hash(self.chain[-1]),
        }
        #Reset the current list of transactions 
        self.current_transactions = [] 
        self.chain.append(block)
        return block 

    
    def new_transaction(self,sender,recipient,amount):
        #sender --> <str> Address Of the sender 
        #recipient --> <str> Address Of the recipient 
        #amount --> <int> Amount sent 
        #pass 
        self.current_transactions.append({
            'sender' : sender ,
            'recipient' : recipient,
            'amount' : amount,
        })
        #returns the index of the last block 
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        #Hashes a block 
        #Creates a SHA-256 hash 
        #Parameter is a block -> Dictionary 
        #Return -> <string> 
        block_string = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]
    
#Initiate our node 
app = Flask(__name__) 

#Generate a global unique address for this node 
node_identifier = str(uuid4()).replace('-','')

#Initiate the BlockChain 
blockchain = BlockChain() 

@app.route('/mine',methods = ['GET'])
def mine():
   #Run proof of work algorithm to get the next proof 
   last_block = blockchain.last_block
   last_proof = last_block['proof']
   proof = blockchain.proof_of_work(last_proof)
   
   #To recieve a reward for finding the proof 
   #The sender is 0 to show the sender has mined a new coin 
   blockchain.new_transaction(
       sender = "0",
       recipient = node_identifier,
       amount = 1,
   )
   #Forge the new block by adding it  to the new chain 
   previous_hash = blockchain.hash(last_block)
   block = blockchain.new_block(proof,previous_hash)
   
   response = {
       'message' : "New Block Forged",
       'index' : block['index'],
       'transactions' : block['transactions'],
       'proof' : block['proof'],
       'previous_hash' : block['previous_hash'],
   }
   return jsonify(response) , 200
   

@app.route('/transactions/new',methods = ['POST'])
def new_transaction():
   values = request.get_json()
   #Check if the required fields are in POST data
   required = ['sender','recipient','amount']
   
   if not all(k in values for k in required):
       return "Missing Values",400
   
   #Create a new transaction 
   index = blockchain.new_transaction(values['sender'],values['recipient'])
   response = {
       'message' : f'Transaction will be added to Block {index}'
   }
   return jsonify(response),201

@app.route('/chain',methods = ['GET'])
def full_chain():
    response = {
        'chain' : blockchain.chain,
        'length' : len(blockchain.chain),
    }
    return jsonify(response),200 

if __name__ == '__main__':
    app.run(host = '0.0.0.0',port = 5000)
    