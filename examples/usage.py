from mrs_logic import parse, Solver

import logging
logging.basicConfig(level=logging.INFO)

sentences = [
    'every man loves a woman',
    'some man loves every woman',
]

for sentence in sentences:
    for i, mrs in enumerate(parse(sentence)):
        print(f'#{i}\t{sentence}')
        solver = Solver(mrs)
        n = solver.count_solutions()
        for j, solution in enumerate(solver.iterate_solutions()):
            print(f'\t({j}/{n}) {solution.to_ulkb(sense_as_label=True)}')
