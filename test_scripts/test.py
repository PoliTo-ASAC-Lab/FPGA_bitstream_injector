import os

i = 3
seed = 1644492424
original = './faulty_bitstreams/uB_results/uB_result_3.dat'
new = f"./fi_reports/strange_uB_results/s{seed}_#{i}.dat"
original = original.replace('/', '\\')
new = new.replace('/', '\\')
os.system(fr'copy "{original}" "{new}"')