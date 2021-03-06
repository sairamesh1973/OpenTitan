# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, Iterator, List, Optional, Tuple

from .isa import OTBNInsn
from .state import OTBNState
from .stats import ExecutionStats
from .trace import Trace

_TEST_RND_DATA = \
    0x99999999_99999999_99999999_99999999_99999999_99999999_99999999_99999999

# A dictionary that defines a function of the form "address -> from -> to". If
# PC is the current PC and cnt is the count for the innermost loop then
# warps[PC][cnt] = new_cnt means that we should warp the current count to
# new_cnt.
LoopWarps = Dict[int, Dict[int, int]]


class OTBNSim:
    def __init__(self) -> None:
        self.state = OTBNState()
        self.program = []  # type: List[OTBNInsn]
        self.loop_warps = {}  # type: LoopWarps
        self.stats = None  # type: Optional[ExecutionStats]
        self._execute_generator = None  # type: Optional[Iterator[None]]

    def load_program(self, program: List[OTBNInsn]) -> None:
        self.program = program.copy()

    def add_loop_warp(self, addr: int, from_cnt: int, to_cnt: int) -> None:
        '''Add a new loop warp to the simulation'''
        self.loop_warps.setdefault(addr, {})[from_cnt] = to_cnt

    def load_data(self, data: bytes) -> None:
        self.state.dmem.load_le_words(data)

    def start(self) -> None:
        '''Prepare to start the execution.

        Use run() or step() to actually execute the program.

        '''
        self.stats = ExecutionStats(self.program)
        self._execute_generator = None
        self.state.start()

    def run(self, verbose: bool, collect_stats: bool) -> int:
        '''Run until ECALL.

        Return the number of cycles taken.

        '''
        insn_count = 0
        # ISS will stall at start until URND data is valid, immediately set it
        # valid when in free running mode as nothing else will.
        self.state.set_urnd_reseed_complete()
        while self.state.running:
            self.step(verbose, collect_stats)
            insn_count += 1

            if self.state.wsrs.RND.pending_request:
                # If an instruction requests RND data, make it available
                # immediately.
                self.state.wsrs.RND.set_unsigned(_TEST_RND_DATA)

        return insn_count

    def step(self,
             verbose: bool,
             collect_stats: bool) -> Tuple[Optional[OTBNInsn], List[Trace]]:
        '''Run a single cycle.

        Returns the instruction, together with a list of the architectural
        changes that have happened. If the model isn't currently running,
        returns no instruction and no changes.

        '''
        if not self.state.running:
            return (None, [])

        assert self.stats is not None

        # Program counter before commit
        pc_before = self.state.pc

        word_pc = self.state.pc >> 2
        if word_pc >= len(self.program):
            raise RuntimeError('Trying to execute instruction at address '
                               '{:#x}, but the program is only {:#x} '
                               'bytes ({} instructions) long. Since there '
                               'are no architectural contents of the '
                               'memory here, we have to stop.'
                               .format(self.state.pc,
                                       4 * len(self.program),
                                       len(self.program)))
        insn = self.program[word_pc]

        sim_stalled = self.state.non_insn_stall
        if not sim_stalled:
            if self._execute_generator is None:
                # This is the first cycle for an instruction. Run any setup for
                # the state object and then start running the instruction
                # itself.
                self.state.pre_insn(insn.affects_control)

                # Either execute the instruction directly (if it is a
                # single-cycle instruction without a `yield` in execute()), or
                # return a generator for multi-cycle instructions. Note that
                # this doesn't consume the first yielded value.
                self._execute_generator = insn.execute(self.state)

            if self._execute_generator is not None:
                # This is a cycle for a multi-cycle instruction (which possibly
                # started just above)
                try:
                    next(self._execute_generator)
                except StopIteration:
                    self._execute_generator = None

            sim_stalled = (self._execute_generator is not None)

        if sim_stalled:
            self.state.commit(sim_stalled=True)
            disasm = '(stall)'
            changes = []

            if collect_stats:
                self.stats.record_stall()
        else:
            assert self._execute_generator is None
            self.state.post_insn(self.loop_warps.get(self.state.pc, {}))

            if collect_stats:
                self.stats.record_insn(insn, self.state)

            if self.state.pending_halt:
                # We've reached the end of the run (either because of an ECALL
                # instruction or an error).
                self.state.stop()

            changes = self.state.changes()

            # Only commit() may change the program counter.
            assert pc_before == self.state.pc

            self.state.commit(sim_stalled=False)

            disasm = insn.disassemble(pc_before)

        if verbose:
            self._print_trace(pc_before, disasm, changes)

        return (None if sim_stalled else insn, changes)

    def dump_data(self) -> bytes:
        return self.state.dmem.dump_le_words()

    def _print_trace(self, pc: int, disasm: str, changes: List[Trace]) -> None:
        '''Print a trace of the current instruction'''
        changes_str = ', '.join([t.trace() for t in changes])
        print('{:08x} | {:45} | [{}]'.format(pc, disasm, changes_str))
