"""
Matrix Determinant Transaction Items
"""
import pyuvm
from pyuvm import *
import random
from matrix_det_types import *

class MatrixItem(uvm_sequence_item):
    """Input matrix item containing 3x3 matrix and delays"""
    
    def __init__(self, name="MatrixItem"):
        super().__init__(name)
        # 3x3 matrix of signed 16-bit values
        self.matrix = [[0 for _ in range(MAT_MATRIX_SIZE)] for _ in range(MAT_MATRIX_SIZE)]
        # Delay before each element
        self.pre_element_delay = [[0 for _ in range(MAT_MATRIX_SIZE)] for _ in range(MAT_MATRIX_SIZE)]
        
    def randomize(self):
        """Randomize matrix values and delays"""
        for i in range(MAT_MATRIX_SIZE):
            for j in range(MAT_MATRIX_SIZE):
                # Random signed 16-bit values
                self.matrix[i][j] = random.randint(MAT_UNDERFLOW_VALUE, MAT_OVERFLOW_VALUE)
                # Random delays
                self.pre_element_delay[i][j] = random.randint(0, 10)
        return True
        
    def determinant_of_matrix(self):
        """Calculate determinant of 3x3 matrix using cofactor expansion"""
        mat = self.matrix
        det = (mat[0][0] * mat[1][1] * mat[2][2] + 
               mat[0][1] * mat[1][2] * mat[2][0] + 
               mat[0][2] * mat[1][0] * mat[2][1] - 
               mat[0][2] * mat[1][1] * mat[2][0] - 
               mat[0][1] * mat[1][0] * mat[2][2] - 
               mat[0][0] * mat[1][2] * mat[2][1])
        return det
        
    def convert2string(self):
        """Convert item to string representation"""
        result = f"Matrix: {self.matrix}\n"
        result += f"Delays: {self.pre_element_delay}\n"
        result += f"Expected Det: {self.determinant_of_matrix()}"
        return result
    
    def __str__(self):
        return self.convert2string()

class DeterminantItem(uvm_sequence_item):
    """Output determinant item"""
    
    def __init__(self, name="DeterminantItem"):
        super().__init__(name)
        self.determinant = 0
        self.overflow = False
        self.pre_det_delay = 0
        
    def convert2string(self):
        """Convert item to string representation"""
        return f"Det: {self.determinant}, Overflow: {self.overflow}, Delay: {self.pre_det_delay}"
    
    def __str__(self):
        return self.convert2string()