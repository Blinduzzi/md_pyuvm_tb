"""
Matrix Determinant Types and Constants
"""
from enum import Enum
import pyuvm
from pyuvm import *

# Matrix and bus width constants
MAT_BUS_WIDTH = 16
MAT_MATRIX_SIZE = 3
DET_BUS_WIDTH = 16

# Value limits for signed 16-bit bus
MAT_UNDERFLOW_VALUE = -(2 ** (MAT_BUS_WIDTH - 1))
MAT_OVERFLOW_VALUE = (2 ** (MAT_BUS_WIDTH - 1)) - 1
DET_UNDERFLOW_VALUE = -(2 ** (DET_BUS_WIDTH - 1))
DET_OVERFLOW_VALUE = (2 ** (DET_BUS_WIDTH - 1)) - 1

class ResetStages(Enum):
    BEFORE_PACKET = "BEFORE_PACKET"
    DURING_PACKET = "DURING_PACKET"
    DURING_BACKPRESSURE = "DURING_BACKPRESSURE"

class TriangularType(Enum):
    NOT_TRIANGULAR = "NOT_TRIANGULAR"
    UPPER = "UPPER"
    LOWER = "LOWER"

class PermutationType(Enum):
    NOT_PERMUTATION = "NOT_PERMUTATION"
    IDENTITY = "IDENTITY"
    PERMUTATION = "PERMUTATION"