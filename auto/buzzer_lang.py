###############################################################################
#
# Copyright (c) 2017-2023 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
A small parser to be able to use the Buzzer language on the Fleet 2 and Virtual Cars.
"""

NOTE_NAMES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
LEN_MULTIPLIER = 2000
TEMPO = 0
STACCATO = 1
VELOCITY = 2
OCTAVE = 3
DEFAULT_DURATION = 4
DEFAULT_SETTINGS = [120, False, 127, 4, 4]

## CMD TYPES:
## 0: note
## 1: octave
## 2: tempo
## 3: default durations
## 4: velocity
## 5: staccato/legato
## 6: rest

class BuzzParser:
    def __init__(self):
        self.cmd_type = None
        self.config = [*DEFAULT_SETTINGS]

    def get_note(self, note_letter, octave, accidentals):
        note_pitches = {
            'C': 0,
            'D': 2,
            'E': 4,
            'F': 5,
            'G': 7,
            'A': 9,
            'B': 11,
        }
        return 12 + (octave * 12) + note_pitches[note_letter] + accidentals

    def get_freq(self, note_letter, octave, accidentals):
        return (2 ** ((self.get_note(note_letter, octave, accidentals) - 69) / 12.0)) * 440

    def calculate_note_duration(self, base_duration, num_dots):
        return sum(base_duration / (2**i) for i in range(num_dots + 1))

    def process_cmd(self):
        if self.cmd_type is None:
            self.args.clear()
            return
        if self.cmd_type == 0:
            try:
                note_len = int(self.args[1])
            except ValueError:
                note_len = self.config[DEFAULT_DURATION]
            t = self.calculate_note_duration(4 / note_len, self.args[4]) * (60 / (self.config[TEMPO]) * 1000)
            self.notes.append((
                self.get_freq(self.args[0], self.config[OCTAVE] + self.args[3], self.args[2]),
                t / 2 if self.config[STACCATO] else t,
                self.config[VELOCITY],
            ))
            if self.config[STACCATO]:
                self.notes.append((
                    None,
                    t / 2,
                    None,
                ))
            self.total_ms += t
        elif self.cmd_type == 1:
            self.config[OCTAVE] = int(self.args[1])
        elif self.cmd_type == 2:
            self.config[TEMPO] = int(self.args[1])
        elif self.cmd_type == 3:
            self.config[DEFAULT_DURATION] = int(self.args[1])
        elif self.cmd_type == 4:
            self.config[VELOCITY] = int(0.2 / 3 * 127 * int(self.args[1]))
        elif self.cmd_type == 5:
            ## This is already handled
            pass
        elif self.cmd_type == 6:
            try:
                rest_len = int(self.args[1])
            except ValueError:
                rest_len = self.config[DEFAULT_DURATION]
            t = self.calculate_note_duration(4 / rest_len, self.args[4]) * (60 / (self.config[TEMPO]) * 1000)
            self.notes.append((
                None,
                t,
                None,
            ))
            self.total_ms += t
        self.args.clear()

    def convert(self, notes_str):
        self.notes = []
        self.total_ms = 0
        self.cmd_type = None
        self.args = []
        octave_diff = 0
        for c in notes_str.upper():
            if c == '!':
                self.config = [*DEFAULT_SETTINGS]
            elif c in NOTE_NAMES:
                self.process_cmd()
                self.cmd_type = 0
                self.args = [c, '', 0, octave_diff, 0]
                octave_diff = 0
            elif c == 'O':
                self.process_cmd()
                self.cmd_type = 1
                self.args = [None, '']
            elif c == 'T':
                self.process_cmd()
                self.cmd_type = 2
                self.args = [None, '']
            elif c == 'L':
                if self.cmd_type == 5:
                    self.config[STACCATO] = False
                    self.cmd_type = None
                else:
                    self.process_cmd()
                    self.cmd_type = 3
                    self.args = [None, '']
            elif c == 'V':
                self.process_cmd()
                self.cmd_type = 4
                self.args = [None, '']
            elif c == 'M':
                self.process_cmd()
                self.cmd_type = 5
            elif c == 'S' and self.cmd_type == 5:
                self.config[STACCATO] = True
                self.cmd_type = None
            elif c == 'R':
                self.process_cmd()
                self.cmd_type = 6
                self.args = [None, '', None, None, 0]
            elif c.isnumeric():
                if len(self.args) >= 2:
                    self.args[1] += c
            elif c == '>':
                octave_diff = 1
            elif c == '<':
                octave_diff = -1
            elif (c == '+' or c == '#') and self.cmd_type == 0:
                self.args[2] += 1
            elif c == '-' and self.cmd_type == 0:
                self.args[2] -= 1
            elif c == '.' and (self.cmd_type == 0 or self.cmd_type == 6):
                self.args[4] += 1

        self.process_cmd()

        return self.notes, self.total_ms / 1000