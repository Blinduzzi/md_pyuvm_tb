"""
Matrix Determinant Scoreboard
"""
import pyuvm
from pyuvm import *
from matrix_det_items import MatrixItem, DeterminantItem
from matrix_det_types import *

class MatrixScoreboard(uvm_component):
    """Scoreboard to compare expected vs actual determinant results"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.expected_queue = []
        
    def build_phase(self):
        super().build_phase()
        
        # Create TLM analysis FIFOs to receive data from monitors
        self.input_fifo = uvm_tlm_analysis_fifo("input_fifo", self)
        self.output_fifo = uvm_tlm_analysis_fifo("output_fifo", self)
        
        # Create get ports to retrieve data from FIFOs
        self.input_get_port = uvm_get_port("input_get_port", self)
        self.output_get_port = uvm_get_port("output_get_port", self)
        
        # Expose FIFO exports for external connections
        self.input_ap = self.input_fifo.analysis_export
        self.output_ap = self.output_fifo.analysis_export
        
        self.logger.info("Scoreboard build_phase completed")
        
    def connect_phase(self):
        super().connect_phase()
        
        # Connect get ports to FIFO get exports
        self.input_get_port.connect(self.input_fifo.get_export)
        self.output_get_port.connect(self.output_fifo.get_export)
        
        self.logger.info("Scoreboard connect_phase completed")
        
    def check_phase(self):
        """Check all collected transactions at end of test"""
        super().check_phase()
        
        # Process all input items first to generate expected results
        while self.input_get_port.can_get():
            _, input_item = self.input_get_port.try_get()
            self.process_input_item(input_item)
            
        # Process all output items and compare with expected results
        while self.output_get_port.can_get():
            _, output_item = self.output_get_port.try_get()
            self.compare_output_item(output_item)
            
        # Check if all expected items were processed
        if self.expected_queue:
            self.logger.error(f"End of test with {len(self.expected_queue)} unprocessed expected items")
        else:
            self.logger.info("All expected items processed successfully")
            
    def process_input_item(self, item):
        """Process input matrix item and generate expected result"""
        self.logger.info(f"Processing input item: {item.convert2string()}")
        
        # Calculate expected determinant
        expected_det = item.determinant_of_matrix()
        
        # Create expected output item
        expected_item = DeterminantItem("expected_item")
        
        # Handle overflow/saturation
        if expected_det < DET_UNDERFLOW_VALUE:
            expected_item.determinant = DET_UNDERFLOW_VALUE
            expected_item.overflow = True
        elif expected_det > DET_OVERFLOW_VALUE:
            expected_item.determinant = DET_OVERFLOW_VALUE
            expected_item.overflow = True
        else:
            expected_item.determinant = expected_det
            expected_item.overflow = False
            
        # Calculate expected delay (sum of all delays + matrix size^2 cycles)
        total_delay = 0
        for i in range(MAT_MATRIX_SIZE):
            for j in range(MAT_MATRIX_SIZE):
                total_delay += item.pre_element_delay[i][j]
        expected_item.pre_det_delay = total_delay + (MAT_MATRIX_SIZE * MAT_MATRIX_SIZE)
        
        # Add to expected queue
        self.expected_queue.append(expected_item)
        self.logger.info(f"Added expected item: {expected_item.convert2string()}")
        
    def compare_output_item(self, item):
        """Compare actual output item with expected"""
        self.logger.info(f"Comparing output item: {item.convert2string()}")
        
        if not self.expected_queue:
            self.logger.error("Unexpected output - no expected items in queue")
            return
            
        expected_item = self.expected_queue.pop(0)
        
        # Compare determinant values
        if expected_item.determinant != item.determinant:
            self.logger.error(
                f"Determinant mismatch - Expected: {expected_item.determinant}, Got: {item.determinant}")
        else:
            self.logger.info(f"Determinant match - Value: {item.determinant}")
            
        # Compare overflow flags
        if expected_item.overflow != item.overflow:
            self.logger.error(
                f"Overflow mismatch - Expected: {expected_item.overflow}, Got: {item.overflow}")
        else:
            self.logger.info(f"Overflow match - Value: {item.overflow}")
            
        # Compare delays (allow some tolerance)
        delay_diff = abs(expected_item.pre_det_delay - item.pre_det_delay)
        if delay_diff > 2:  # Allow small tolerance for timing differences
            self.logger.warning(
                f"Delay difference - Expected: {expected_item.pre_det_delay}, Got: {item.pre_det_delay}")
        else:
            self.logger.info(
                f"Delay acceptable - Expected: {expected_item.pre_det_delay}, Got: {item.pre_det_delay}")