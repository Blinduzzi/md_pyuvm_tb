"""
Matrix Determinant Coverage Collector
"""
import pyuvm
from pyuvm import *
from matrix_det_items import MatrixItem, DeterminantItem
from matrix_det_types import *

class CoverageCollector(uvm_subscriber):
    """Block coverage collector for matrix determinant operations"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        
        # Coverage bins
        self.matrix_value_bins = {}
        self.determinant_value_bins = {}
        self.overflow_bins = {"true": 0, "false": 0}
        self.delay_bins = {"short": 0, "medium": 0, "long": 0}
        self.matrix_type_bins = {
            "triangular_upper": 0,
            "triangular_lower": 0, 
            "diagonal": 0,
            "identity": 0,
            "general": 0
        }
        
        # We'll create two separate coverage collectors
        self.input_items = []
        self.output_items = []
        
    def build_phase(self):
        super().build_phase()
        
        # Create analysis FIFOs for input and output data
        self.input_fifo = uvm_tlm_analysis_fifo("input_fifo", self)
        self.output_fifo = uvm_tlm_analysis_fifo("output_fifo", self)
        
        # Create get ports
        self.input_get_port = uvm_get_port("input_get_port", self)  
        self.output_get_port = uvm_get_port("output_get_port", self)
        
        # Expose FIFO exports
        self.input_ap = self.input_fifo.analysis_export
        self.output_ap = self.output_fifo.analysis_export
        
        self.logger.info("Coverage Collector build_phase completed")
        
    def connect_phase(self):
        super().connect_phase()
        
        # Connect get ports to FIFO exports
        self.input_get_port.connect(self.input_fifo.get_export)
        self.output_get_port.connect(self.output_fifo.get_export)
        
        self.logger.info("Coverage Collector connect_phase completed")
        
    def write(self, item):
        """Generic write method - not used in FIFO-based approach"""
        # This method is required by uvm_subscriber but we use FIFOs instead
        pass
        
    def report_phase(self):
        """Collect coverage from all items and report statistics"""
        super().report_phase()
        
        # Process all input items for coverage
        while self.input_get_port.can_get():
            _, input_item = self.input_get_port.try_get()
            self.collect_input_coverage(input_item)
            
        # Process all output items for coverage  
        while self.output_get_port.can_get():
            _, output_item = self.output_get_port.try_get()
            self.collect_output_coverage(output_item)
            
        # Report coverage statistics
        self.logger.info("=== COVERAGE REPORT ===")
        
        self.logger.info("Matrix Value Coverage:")
        for range_name, count in self.matrix_value_bins.items():
            self.logger.info(f"  {range_name}: {count}")
            
        self.logger.info("Determinant Value Coverage:")
        for range_name, count in self.determinant_value_bins.items():
            self.logger.info(f"  {range_name}: {count}")
            
        self.logger.info("Overflow Coverage:")
        for overflow, count in self.overflow_bins.items():
            self.logger.info(f"  {overflow}: {count}")
            
        self.logger.info("Delay Coverage:")
        for delay_range, count in self.delay_bins.items():
            self.logger.info(f"  {delay_range}: {count}")
            
        self.logger.info("Matrix Type Coverage:")
        for matrix_type, count in self.matrix_type_bins.items():
            self.logger.info(f"  {matrix_type}: {count}")
            
        self.logger.info("=== END COVERAGE REPORT ===")
        
    def collect_input_coverage(self, item):
        """Collect coverage from input matrix item"""
        self.logger.info(f"Collecting input coverage for: {item.convert2string()}")
        
        # Collect matrix element value coverage
        for i in range(MAT_MATRIX_SIZE):
            for j in range(MAT_MATRIX_SIZE):
                value = item.matrix[i][j]
                value_range = self._get_value_range(value)
                if value_range not in self.matrix_value_bins:
                    self.matrix_value_bins[value_range] = 0
                self.matrix_value_bins[value_range] += 1
                
        # Collect delay coverage
        total_delay = sum(sum(row) for row in item.pre_element_delay)
        delay_range = self._get_delay_range(total_delay)
        self.delay_bins[delay_range] += 1
        
        # Collect matrix type coverage
        matrix_type = self._classify_matrix(item.matrix)
        self.matrix_type_bins[matrix_type] += 1
        
        self.logger.info(f"Input coverage updated - Matrix type: {matrix_type}")
        
    def collect_output_coverage(self, item):
        """Collect coverage from output determinant item"""
        self.logger.info(f"Collecting output coverage for: {item.convert2string()}")
        
        # Collect determinant value coverage
        det_range = self._get_value_range(item.determinant)
        if det_range not in self.determinant_value_bins:
            self.determinant_value_bins[det_range] = 0
        self.determinant_value_bins[det_range] += 1
        
        # Collect overflow coverage
        overflow_key = "true" if item.overflow else "false"
        self.overflow_bins[overflow_key] += 1
        
        self.logger.info(f"Output coverage updated - Det range: {det_range}, Overflow: {overflow_key}")
        
    def _get_value_range(self, value):
        """Categorize value into range bins"""
        if value == DET_UNDERFLOW_VALUE:
            return "min"
        elif value == DET_OVERFLOW_VALUE:
            return "max" 
        elif -1000 <= value <= 1000:
            return "small"
        elif -10000 <= value <= 10000:
            return "medium"
        else:
            return "large"
            
    def _get_delay_range(self, delay):
        """Categorize delay into range bins"""
        if delay <= 5:
            return "short"
        elif delay <= 20:
            return "medium"
        else:
            return "long"
            
    def _classify_matrix(self, matrix):
        """Classify matrix type for coverage"""
        # Check if identity matrix
        is_identity = True
        for i in range(MAT_MATRIX_SIZE):
            for j in range(MAT_MATRIX_SIZE):
                expected = 1 if i == j else 0
                if matrix[i][j] != expected:
                    is_identity = False
                    break
            if not is_identity:
                break
        if is_identity:
            return "identity"
            
        # Check if diagonal matrix
        is_diagonal = True
        for i in range(MAT_MATRIX_SIZE):
            for j in range(MAT_MATRIX_SIZE):
                if i != j and matrix[i][j] != 0:
                    is_diagonal = False
                    break
            if not is_diagonal:
                break
        if is_diagonal:
            return "diagonal"
            
        # Check if upper triangular
        is_upper = True
        for i in range(MAT_MATRIX_SIZE):
            for j in range(i):
                if matrix[i][j] != 0:
                    is_upper = False
                    break
            if not is_upper:
                break
        if is_upper:
            return "triangular_upper"
            
        # Check if lower triangular
        is_lower = True
        for i in range(MAT_MATRIX_SIZE):
            for j in range(i+1, MAT_MATRIX_SIZE):
                if matrix[i][j] != 0:
                    is_lower = False
                    break
            if not is_lower:
                break
        if is_lower:
            return "triangular_lower"
            
        return "general"