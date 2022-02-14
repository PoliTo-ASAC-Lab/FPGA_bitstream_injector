# bitflip function [By Sarah Azimi]

def bitflip(golden_number, bit_pos, inject_ones_only):
    if ((golden_number >> bit_pos)%2 == 0):
        if inject_ones_only:
            return -1 #injection has to be repeated
    	# force to 1
        mask = 1 << bit_pos
        faulty_number = golden_number | mask
    else:
    	# force to 0
        mask = ~(1 << bit_pos)
        faulty_number = golden_number & mask
    #print (f"faulty number:{bin(faulty_number)}")
    return faulty_number
