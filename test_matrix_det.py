"""
Matrix Determinant Test - Fixed for PyUVM 3.x with proper objections
"""
import cocotb
import pyuvm
from pyuvm import *
from cocotb.triggers import Timer, RisingEdge, FallingEdge

# Import our components
from matrix_det_env import MatrixDetEnv
from matrix_sequence import MatrixSequence, SimpleMatrixSequence, StressMatrixSequence, SmallMatrixSequence, MultipleResetSequence

class MatrixDetTest(uvm_test):
    """Base test for matrix determinant"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.env = None
        
    def build_phase(self):
        super().build_phase()
        self.logger.info("Test build_phase started")
        
        # Create environment
        self.env = MatrixDetEnv("env", self)
        
        self.logger.info("Test build_phase completed")
        
    def connect_phase(self):
        super().connect_phase()
        # Set DUT handles in agents
        dut = cocotb.top
        self.env.input_agent.driver.dut = dut
        self.env.input_agent.monitor.dut = dut
        self.env.output_agent.monitor.dut = dut
        self.logger.info("Test connect_phase completed")
        
    async def run_phase(self):
        self.raise_objection()
        
        await super().run_phase()
        self.logger.info("Test run_phase started")
        
        try:
            # Apply reset
            await self.apply_reset()
            
            # Start sequence
            seq = SimpleMatrixSequence("simple_seq")
            await seq.start(self.env.input_agent.sequencer)
            
            # Wait a bit for processing
            await Timer(2000, units='ns')
            
            self.logger.info("Test run_phase completed")
            
        except Exception as e:
            self.logger.error(f"Test failed with exception: {e}")
            raise
        finally:
            # IMPORTANT: Drop objection to allow test to end
            self.drop_objection()
        
    async def apply_reset(self):
        """Apply reset to DUT"""
        dut = cocotb.top
        self.logger.info("Applying reset")
        
        # Initialize signals
        dut.rst_n.value = 1
        dut.mat_valid.value = 0
        dut.mat_in.value = 0
        
        # Apply reset
        dut.rst_n.value = 0
        await Timer(105, units='ns')
        dut.rst_n.value = 1
        await Timer(10, units='ns')
        self.logger.info("Reset completed")

class RandomMatrixTest(MatrixDetTest):
    """Test with random matrices"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        
    async def run_phase(self):
        # IMPORTANT: Raise objection to keep test running
        self.raise_objection()
        
        # Call parent's run_phase but without the objection handling
        # since we're handling it here
        await uvm_component.run_phase(self)
        self.logger.info("Random Matrix Test run_phase started")
        
        try:
            # Apply reset
            await self.apply_reset()
            
            # Start random sequence
            seq = MatrixSequence("random_seq")
            seq.num_items = 1000  # Start with fewer items for initial testing
            await seq.start(self.env.input_agent.sequencer)
            
            # Wait for processing
            await Timer(3000, units='ns')
            
            self.logger.info("Random Matrix Test run_phase completed")
            
        except Exception as e:
            self.logger.error(f"Random test failed with exception: {e}")
            raise
        finally:
            # IMPORTANT: Drop objection to allow test to end
            self.drop_objection()

class StressMatrixTest(MatrixDetTest):
    """Stress test with zero delays for maximum throughput"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        
    async def run_phase(self):
        self.raise_objection()
        
        await uvm_component.run_phase(self)
        self.logger.info("Stress Matrix Test run_phase started")
        
        try:
            # Apply reset
            await self.apply_reset()
            
            # Start stress sequence
            seq = StressMatrixSequence("stress_seq")
            seq.num_items = 100  # High throughput test
            await seq.start(self.env.input_agent.sequencer)
            
            # Shorter wait time since there are no delays
            await Timer(5000, units='ns')
            
            self.logger.info("Stress Matrix Test run_phase completed")
            
        except Exception as e:
            self.logger.error(f"Stress test failed with exception: {e}")
            raise
        finally:
            self.drop_objection()

class SmallMatrixTest(MatrixDetTest):
    """Test with small matrix values (-32 to 32)"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        
    async def run_phase(self):
        self.raise_objection()
        
        await uvm_component.run_phase(self)
        self.logger.info("Small Matrix Test run_phase started")
        
        try:
            # Apply reset
            await self.apply_reset()
            
            # Start small value sequence
            seq = SmallMatrixSequence("small_seq")
            seq.num_items = 50  # Reasonable number for small value testing
            await seq.start(self.env.input_agent.sequencer)
            
            # Wait for processing
            await Timer(4000, units='ns')
            
            self.logger.info("Small Matrix Test run_phase completed")
            
        except Exception as e:
            self.logger.error(f"Small test failed with exception: {e}")
            raise
        finally:
            self.drop_objection()

class MultipleResetTest(MatrixDetTest):
    """Test with multiple random resets during traffic"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        
    async def run_phase(self):
        self.raise_objection()
        
        await uvm_component.run_phase(self)
        self.logger.info("Multiple Reset Test run_phase started")
        
        try:
            # Apply initial reset
            await self.apply_reset()
            
            # Start sequence that includes random resets
            seq = MultipleResetSequence("reset_seq")
            seq.num_items = 30  # Moderate number since resets will interrupt
            seq.num_resets = 20  # Number of random resets
            await seq.start(self.env.input_agent.sequencer)
            
            # Longer wait time to accommodate resets and recovery
            await Timer(10000, units='ns')
            
            self.logger.info("Multiple Reset Test run_phase completed")
            
        except Exception as e:
            self.logger.error(f"Multiple reset test failed with exception: {e}")
            raise
        finally:
            self.drop_objection()

# Cocotb test functions
@cocotb.test()
async def simple_matrix_test(dut):
    """Simple matrix determinant test"""
    
    # Initialize clock
    cocotb.start_soon(clock_gen(dut.clk))
    
    # Initialize PyUVM and run test
    await uvm_root().run_test("MatrixDetTest")

@cocotb.test()
async def random_matrix_test(dut):
    """Random matrix determinant test"""
    
    # Initialize clock  
    cocotb.start_soon(clock_gen(dut.clk))
    
    # Initialize PyUVM and run test
    await uvm_root().run_test("RandomMatrixTest")

@cocotb.test()
async def stress_matrix_test(dut):
    """Stress test with zero delays"""
    
    # Initialize clock
    cocotb.start_soon(clock_gen(dut.clk))
    
    # Initialize PyUVM and run test
    await uvm_root().run_test("StressMatrixTest")

@cocotb.test()
async def small_matrix_test(dut):
    """Test with small matrix values"""
    
    # Initialize clock
    cocotb.start_soon(clock_gen(dut.clk))
    
    # Initialize PyUVM and run test
    await uvm_root().run_test("SmallMatrixTest")

@cocotb.test()
async def multiple_reset_test(dut):
    """Test with multiple random resets"""
    
    # Initialize clock
    cocotb.start_soon(clock_gen(dut.clk))
    
    # Initialize PyUVM and run test
    await uvm_root().run_test("MultipleResetTest")

async def clock_gen(clk):
    """Generate clock signal"""
    while True:
        clk.value = 0
        await Timer(5, units='ns')
        clk.value = 1
        await Timer(5, units='ns')