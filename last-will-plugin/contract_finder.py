from .last_will_contract import LastWillContract
from electroncash.address import Address, ScriptOutput
from itertools import permutations
from electroncash.transaction import Transaction


def find_contract(wallet,a = 'network'):
    """Searching transactions for the one maching contract
    by creating contracts from outputs"""
    contracts=[]
    for hash, t in wallet.transactions.items():
        out = t.outputs()
        address = ''
        if len(out) > 3:
            address = get_contract_address(out)
            candidates = get_candidates(out)
            for c in candidates:
                will = LastWillContract(c)
                if will.address.to_ui_string()==address:
                        response = wallet.network.synchronous_get(
                            ("blockchain.scripthash.listunspent", [will.address.to_scripthash_hex()]))
                        if unfunded_contract(response) : #skip unfunded and ended contracts
                            continue
                        if a == 'network':
                            contracts.append(( response, will, find_my_role(c, wallet)))
                        else:
                            contracts.append(t.as_dict())
    return contracts

def extract_contract_data(tx):
    transaction=Transaction(tx)
    address = get_contract_address(transaction.outputs())
    candidates = get_candidates(transaction.outputs())
    for c in candidates:
        will = LastWillContract(c)
        if will.address.to_ui_string()==address:
            return will

def unfunded_contract(r):
    """Checks if the contract is funded"""
    s = False
    if len(r) == 0:
        s = True
    for t in r:
        if t.get('value') == 0: # when contract was drained by fees it's still in utxo
            s = True
    return s


def get_contract_address(outputs):
    """Finds p2sh output"""
    for o in outputs:
        if isinstance(o[1], ScriptOutput):
            try:
                return o[1].to_ui_string().split("'")[1]
            except:
                pass

def get_candidates(outputs):
    """Creates all permutations of addresses that are not p2sh type"""
    candidates = []
    for o1, o2, o3 in permutations(outputs, 3):
        if not (isinstance(o1[1], Address) and isinstance(o2[1], Address) and isinstance(o3[1], Address)):
            continue
        if o1[1].kind or o2[1].kind or o3[1].kind:
            continue
        candidates.append([o1[1], o2[1], o3[1]])
    return candidates

def find_my_role(candidates, wallet):
    """Returns my role in this contract. 1 if this is refreshing wallet,
    2 if cold and 3 if it's inheritors wallet"""
    for counter, a in enumerate(candidates, start=0):
        if wallet.is_mine(a):
            return counter

