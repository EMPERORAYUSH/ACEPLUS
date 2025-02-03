import petname
import random

def generate_memorable_name():
    return f"{''.join([i.capitalize().replace('hot', ' ') for i in petname.generate(2).split('-')])}-{random.randint(100, 999)}"
 
