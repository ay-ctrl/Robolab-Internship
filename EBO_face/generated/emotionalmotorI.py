#
#    Copyright (C) 2026 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#

import sys, os, Ice

ROBOCOMP = ''
try:
    ROBOCOMP = os.environ['ROBOCOMP']
except:
    print('$ROBOCOMP environment variable not set, using the default value /opt/robocomp')
    ROBOCOMP = '/opt/robocomp'
if len(ROBOCOMP)<1:
    raise RuntimeError('ROBOCOMP environment variable not set! Exiting.')


Ice.loadSlice("-I ./generated/ --all ./generated/EmotionalMotor.ice")

from RoboCompEmotionalMotor import *

class EmotionalMotorI(EmotionalMotor):
    def __init__(self, worker, id:str):
        self.worker = worker
        self.id = id


    def expressAnger(self, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_expressAnger")()

    def expressDisgust(self, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_expressDisgust")()

    def expressFear(self, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_expressFear")()

    def expressJoy(self, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_expressJoy")()

    def expressSadness(self, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_expressSadness")()

    def expressSurprise(self, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_expressSurprise")()

    def isanybodythere(self, isAny, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_isanybodythere")(isAny)

    def listening(self, setListening, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_listening")(setListening)

    def pupposition(self, x, y, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_pupposition")(x, y)

    def talking(self, setTalk, texto, ice):
        return getattr(self.worker, f"EmotionalMotor{self.id}_talking")(setTalk, texto)
