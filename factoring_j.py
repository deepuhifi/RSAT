# Copyright (C) 2011 by Henry Yuen, Joseph Bebel

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.



# ToughSat Project
# http://toughsat.appspot.com

#!/usr/bin/env python
import math

def num_var(cnf):
    vars = set()
    for clause in cnf:
        for literal in clause:
            vars.add(abs(literal))
    return len(vars)

def cnf_to_dimacs(cnf, n):
    dimacs = "p cnf " + str(num_var(cnf)) + " " + str(len(cnf)) + "\n"
    dimacs += "c Factors encoded in variables 1-" + str(n) + " and " + str(n+1) + "-" + str(2*n) + "\n"
    for clause in cnf:
        for literal in clause:
            dimacs += str(literal) + " "
        dimacs += "0\n"
    return dimacs

def circuit_to_cnf(circuit, n):
    #make a dict of the variables used
    variables = dict()
    cnf_formula = []

    next_var = 1
    #add inputs so they're the first
    for i in range(n):
        variables["x" + str(i)] = next_var
        next_var += 1
    for i in range(n):
        variables["y" + str(i)] = next_var
        next_var += 1

    cnf_formula.append( tuple(variables["x" + str(i)] for i in range(1,n)) )
    cnf_formula.append( tuple(variables["y" + str(i)] for i in range(1,n)) )

    variables["zero"] = next_var
    cnf_formula.append( (-next_var,) )
    next_var += 1
    variables["one"] = next_var
    cnf_formula.append( (next_var,) )
    next_var += 1
    # circuit
    for line in circuit:
        op = line[1]
        if op in ("equal", "not"): #(op1, "equal", op2) ) set op1 = op2
            if line[0] not in variables:
                variables[line[0]] = next_var
                next_var += 1
            if line[2] not in variables:
                variables[line[2]] = next_var
                next_var += 1
        if op in ("and", "or", "xor"): #(op1, "and", op2, op3) op1 = op2 and op3
            if line[0] not in variables:
                variables[line[0]] = next_var
                next_var += 1
            if line[2] not in variables:
                variables[line[2]] = next_var
                next_var += 1
            if line[3] not in variables:
                variables[line[3]] = next_var
                next_var += 1
        if op == "plus": #(op1, "plus", op2, op3, op4, op5) where op1 = op2+op3+op4 and op5 is carryout
            if line[0] not in variables:
                variables[line[0]] = next_var
                next_var += 1
            if line[2] not in variables:
                variables[line[2]] = next_var
                next_var += 1
            if line[3] not in variables:
                variables[line[3]] = next_var
                next_var += 1
            if line[4] not in variables:
                variables[line[4]] = next_var
                next_var += 1
            if line[5] not in variables:
                variables[line[5]] = next_var
                next_var += 1
        if op == "halfplus": #(op1, "halfplus", op2, op3, op4) where op1 = op2+op3 and op4 is carryout
            if line[0] not in variables:
                variables[line[0]] = next_var
                next_var += 1
            if line[2] not in variables:
                variables[line[2]] = next_var
                next_var += 1
            if line[3] not in variables:
                variables[line[3]] = next_var
                next_var += 1
            if line[4] not in variables:
                variables[line[4]] = next_var
                next_var += 1

    #implement circuit operations

    for line in circuit:
        op = line[1]
        if op == "plus": #(op1, "plus", op2, op3, op4, op5) where op1 = op2+op3+op4 and op5 is carryout
            cnf_formula.append( (-variables[line[0]], variables[line[2]], variables[line[3]], variables[line[4]]) )
            cnf_formula.append( (-variables[line[0]], -variables[line[2]], -variables[line[3]], variables[line[4]]) )
            cnf_formula.append( (-variables[line[0]], -variables[line[2]], variables[line[3]], -variables[line[4]]) )
            cnf_formula.append( (-variables[line[0]], variables[line[2]], -variables[line[3]], -variables[line[4]]) )

            cnf_formula.append( (variables[line[0]], -variables[line[2]], -variables[line[3]], -variables[line[4]]) )
            cnf_formula.append( (variables[line[0]], variables[line[2]], variables[line[3]], -variables[line[4]]) )
            cnf_formula.append( (variables[line[0]], variables[line[2]], -variables[line[3]], variables[line[4]]) )
            cnf_formula.append( (variables[line[0]], -variables[line[2]], variables[line[3]], variables[line[4]]) )

            cnf_formula.append( (-variables[line[2]], -variables[line[3]], variables[line[5]]) )
            cnf_formula.append( (-variables[line[2]], -variables[line[4]], variables[line[5]]) )
            cnf_formula.append( (-variables[line[3]], -variables[line[4]], variables[line[5]]) )

            cnf_formula.append( (variables[line[2]], variables[line[3]], -variables[line[5]]) )
            cnf_formula.append( (variables[line[2]], variables[line[4]], -variables[line[5]]) )
            cnf_formula.append( (variables[line[3]], variables[line[4]], -variables[line[5]]) )
        if op == "halfplus": #(op1, "plus", op2, op3, op4) where op1 = op2+op3 and op4 is carryout
            cnf_formula.append( (-variables[line[0]], variables[line[2]], variables[line[3]]) )
            cnf_formula.append( (-variables[line[0]], -variables[line[2]], -variables[line[3]]) )
            cnf_formula.append( (variables[line[0]], variables[line[2]], -variables[line[3]]) )
            cnf_formula.append( (variables[line[0]], -variables[line[2]], variables[line[3]]) )

            cnf_formula.append( (-variables[line[2]], -variables[line[3]], variables[line[4]]) )
            cnf_formula.append( (variables[line[2]], variables[line[3]], -variables[line[4]]) )
            cnf_formula.append( (variables[line[2]], -variables[line[4]]) )
            cnf_formula.append( (variables[line[3]], -variables[line[4]]) )

    for line in circuit:
        op = line[1]
        if op == "xor": #(op1, "xor", op2, op3) where op1 = op2 xor op3
            not_a = next_var
            variables["dummy" + str(not_a) + "not_a"] = not_a
            next_var += 1
            circuit.append( ("dummy" + str(not_a) + "not_a", "not", line[2]) )
            not_b = next_var
            variables["dummy" + str(not_b) + "not_b"] = not_b
            circuit.append( ("dummy" + str(not_b) + "not_b", "not", line[3],) )
            next_var += 1
            and1 = next_var
            variables["dummy" + str(and1) + "and1"] = and1
            circuit.append( ("dummy" + str(and1) + "and1", "and", line[2], "dummy" + str(not_b) + "not_b" ) )
            next_var += 1
            and2 = next_var
            variables["dummy" + str(and2) + "and2"] = and2
            circuit.append( ("dummy" + str(and2) + "and2", "and", line[3], "dummy" + str(not_a) + "not_a") )
            next_var += 1
            circuit.append( (line[0], "or", "dummy" + str(and1) + "and1", "dummy" + str(and2) + "and2") )

    for line in circuit:
        op = line[1]
        if op == "equal": #(op1, "equal", op2)
            # x = a iff
            # (x or -a) AND (-x or a)
            cnf_formula.append( (variables[line[0]], -variables[line[2]]) )
            cnf_formula.append( (-variables[line[0]], variables[line[2]]) )
        if op == "not": #(op1, "not", op2) op1 = not op2
            # x = -a iff
            # (x or a) AND (-x or -a)
            cnf_formula.append( (variables[line[0]], variables[line[2]]) )
            cnf_formula.append( (-variables[line[0]], -variables[line[2]]) )
        if op == "and": #(op1, "and", op2, op3)
            #add in dummy_variable = (dummy_variable-1) AND v
            # x = a AND B iff
            # (x or -a or -b) AND (-x or a) AND (-x or b)
            cnf_formula.append( (variables[line[0]], -variables[line[2]], -variables[line[3]]) )
            cnf_formula.append( (-variables[line[0]], variables[line[2]]) )
            cnf_formula.append( (-variables[line[0]], variables[line[3]]) )
        if op == "or": #(op1, "or", op2, op3)
            #add in dummy_variable = (dummy_variable-1) AND v
            # x = a OR B iff
            # (-x or a or b) AND (x or -a) AND (x or -b)
            cnf_formula.append( (-variables[line[0]], variables[line[2]], variables[line[3]]) )
            cnf_formula.append( (variables[line[0]], -variables[line[2]]) )
            cnf_formula.append( (variables[line[0]], -variables[line[3]]) )

    return cnf_formula

def convert_to_3cnf(cnf):
    good_clauses = [c for c in cnf if len(c) <= 3]
    bad_clauses = [c for c in cnf if len(c) > 3]
    tmp_var = num_var(cnf) + 1

    def reduce_clause(clause, tmp_var):
        cur_var = tmp_var
        if len(clause) <= 3:
            return [clause], tmp_var
        tmp_clause = list(clause[2:])
        tmp_clause.append(cur_var)
        tmp_clause2, tmp_var = reduce_clause(tmp_clause, tmp_var+1)
        tmp_clause2.append( [clause[0], clause[1], -cur_var])
        return tmp_clause2, tmp_var
        
    for c in bad_clauses:
        tmp_clause3, tmp_var = reduce_clause(c, tmp_var)
        good_clauses.extend(tmp_clause3)

    return good_clauses

def generate_instance2(target, op_3cnf):
    n = int(math.ceil(math.log(target)/math.log(2)))

    circuit = []
    n = 1+n/2
	
    for i in range(n):
        pp = "pp" + str(i) #n'th partial product
        for j in range(n):
            #j'th bit of the i'th partial product = x_j AND y_i
            circuit.append( (pp + "," + str(j), "and", "x" + str(j), "y" + str(i)) ) #ppi,j = x

    partial_products = [ (["pp" + str(i) + "," + str(j) for j in range(n)], i) for i in range(n) ]

    def sum_pair(vec1, vec2, offset, tmp_id):
        output = []
        #vectors offset
        for j in range(offset):
            output.append(vec1[j])
        prev_carry = "zero"
        for j in range(offset, len(vec1)):
            #sum jth bit of vec1 and (j+offset)th bit of vec2
            output.append("tmpsum" + str(tmp_id) + "," + str(j))
            #print j, offset, len(vec1), len(vec2)
            if j == offset:
                circuit.append( ("tmpsum" + str(tmp_id) + "," + str(j), "halfplus", vec1[j], vec2[j-offset], "carry" + str(tmp_id) + "," + str(j) ) )
            elif offset < j < len(vec2) + offset:
                circuit.append( ("tmpsum" + str(tmp_id) + "," + str(j), "plus", vec1[j], vec2[j-offset], prev_carry, "carry" + str(tmp_id) + "," + str(j) ) )
            else:
                circuit.append( ("tmpsum" + str(tmp_id) + "," + str(j), "halfplus", vec1[j], prev_carry, "carry" + str(tmp_id) + "," + str(j) ) )
            prev_carry = "carry" + str(tmp_id) + "," + str(j)

        for j in range(len(vec1), len(vec2) + offset):
            output.append("tmpsum" + str(tmp_id) + "," + str(j))
            circuit.append( ("tmpsum" + str(tmp_id) + "," + str(j), "halfplus", vec2[j-offset], prev_carry, "carry" + str(tmp_id) + "," + str(j) ) )
            prev_carry = "carry" + str(tmp_id) + "," + str(j)
        output.append(prev_carry)
        return output

    cur_id = 0
    while len(partial_products) > 1:
        (p1, i1) = partial_products[0]
        (p2, i2) = partial_products[1]
        if i2 < i1:
            p1,p2 = p2,p1
            i1,i2 = i2,i1
        tmpsum = sum_pair(p1, p2, i2 - i1, cur_id)
        cur_id += 1
        del partial_products[1]
        del partial_products[0]
        partial_products.append( (tmpsum, i1) )

    #partial_products[0][0] contains the target product
    bt = bin(target)[:1:-1]
    bt = bt + '0' * ( len(partial_products[0][0]) - len(bt) )
    last = 0
    for i, t in enumerate(bt):
        if t == '0':
            circuit.append( (partial_products[0][0][i], "equal", "zero",) )
        elif t == '1':
            circuit.append( (partial_products[0][0][i], "equal", "one") )

    #circuit now contains the description of a circuit
    cnf = circuit_to_cnf(circuit, n)
    #now cnf formula has a 3-cnf (4-cnf?) formula (should always be satisfiable) that gives a factorization (possibly the n = 1*n one)
    if op_3cnf:
        cnf = convert_to_3cnf(cnf)
    return cnf_to_dimacs(cnf, n)
	
def generate_instance(a,b, op_3cnf):
    target = a*b
    n = int(max(math.ceil(math.log(a)/math.log(2)),
                 math.ceil(math.log(b)/math.log(2))))

    n = 1+n/2
    circuit = []

    for i in range(n):
        pp = "pp" + str(i) #n'th partial product
        for j in range(n):
            #j'th bit of the i'th partial product = x_j AND y_i
            circuit.append( (pp + "," + str(j), "and", "x" + str(j), "y" + str(i)) ) #ppi,j = x

    partial_products = [ (["pp" + str(i) + "," + str(j) for j in range(n)], i) for i in range(n) ]

    def sum_pair(vec1, vec2, offset, tmp_id):
        output = []
        #vectors offset
        for j in range(offset):
            output.append(vec1[j])
        prev_carry = "zero"
        for j in range(offset, len(vec1)):
            #sum jth bit of vec1 and (j+offset)th bit of vec2
            output.append("tmpsum" + str(tmp_id) + "," + str(j))
            #print j, offset, len(vec1), len(vec2)
            if j == offset:
                circuit.append( ("tmpsum" + str(tmp_id) + "," + str(j), "halfplus", vec1[j], vec2[j-offset], "carry" + str(tmp_id) + "," + str(j) ) )
            elif offset < j < len(vec2) + offset:
                circuit.append( ("tmpsum" + str(tmp_id) + "," + str(j), "plus", vec1[j], vec2[j-offset], prev_carry, "carry" + str(tmp_id) + "," + str(j) ) )
            else:
                circuit.append( ("tmpsum" + str(tmp_id) + "," + str(j), "halfplus", vec1[j], prev_carry, "carry" + str(tmp_id) + "," + str(j) ) )
            prev_carry = "carry" + str(tmp_id) + "," + str(j)

        for j in range(len(vec1), len(vec2) + offset):
            output.append("tmpsum" + str(tmp_id) + "," + str(j))
            circuit.append( ("tmpsum" + str(tmp_id) + "," + str(j), "halfplus", vec2[j-offset], prev_carry, "carry" + str(tmp_id) + "," + str(j) ) )
            prev_carry = "carry" + str(tmp_id) + "," + str(j)
        output.append(prev_carry)
        return output

    cur_id = 0
    while len(partial_products) > 1:
        (p1, i1) = partial_products[0]
        (p2, i2) = partial_products[1]
        if i2 < i1:
            p1,p2 = p2,p1
            i1,i2 = i2,i1
        tmpsum = sum_pair(p1, p2, i2 - i1, cur_id)
        cur_id += 1
        del partial_products[1]
        del partial_products[0]
        partial_products.append( (tmpsum, i1) )

    #partial_products[0][0] contains the target product
    bt = bin(target)[:1:-1]
    bt = bt + '0' * ( len(partial_products[0][0]) - len(bt) )
    last = 0
    for i, t in enumerate(bt):
        if t == '0':
            circuit.append( (partial_products[0][0][i], "equal", "zero",) )
        elif t == '1':
            circuit.append( (partial_products[0][0][i], "equal", "one") )

    #circuit now contains the description of a circuit
    cnf = circuit_to_cnf(circuit, n)
    #now cnf formula has a 3-cnf (4-cnf?) formula (should always be satisfiable) that gives a factorization (possibly the n = 1*n one)
    if op_3cnf:
        cnf = convert_to_3cnf(cnf)
    return cnf_to_dimacs(cnf, n)

