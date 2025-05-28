"""
Matrix Determinant Sequences
"""
import pyuvm
from pyuvm import *
import random
from matrix_det_items import MatrixItem

class MatrixSequence(uvm_sequence):
    """Basic sequence to generate random matrix items"""
    
    def __init__(self, name="MatrixSequence"):
        super().__init__(name)
        self.num_items = 5 # Default setting
        
    async def body(self):
        print(f"Starting sequence with {self.num_items} items")
        
        for i in range(self.num_items):
            # Create and randomize matrix item
            item = MatrixItem(f"matrix_item_{i}")
            item.randomize()
            
            print(f"Sending item {i}: {item.convert2string()}")
            
            # Send item to driver
            await self.start_item(item)
            await self.finish_item(item)
            
        print(f"Sequence completed - sent {self.num_items} items")

class SimpleMatrixSequence(uvm_sequence):
    """Simple sequence with known values for initial testing"""
    
    def __init__(self, name="SimpleMatrixSequence"):
        super().__init__(name)
        
    async def body(self):
        print("Starting simple sequence")
        
        # Create a simple identity matrix
        item = MatrixItem("identity_matrix")
        item.matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        item.pre_element_delay = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        
        print(f"Sending identity matrix: {item.convert2string()}")
        await self.start_item(item)
        await self.finish_item(item)
        
        # Create a simple 2x2 determinant test (with 0 in bottom row)
        item2 = MatrixItem("simple_matrix")
        item2.matrix = [[2, 1, 0], [1, 2, 0], [0, 0, 1]]
        item2.pre_element_delay = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        
        print(f"Sending simple matrix: {item2.convert2string()}")
        await self.start_item(item2)
        await self.finish_item(item2)
        
        print("Simple sequence completed")

class StressMatrixSequence(uvm_sequence):
    """Stress test sequence - all delays set to 0 for maximum throughput"""
    
    def __init__(self, name="StressMatrixSequence"):
        super().__init__(name)
        self.num_items = 100  # Default number of stress test items
        
    async def body(self):
        print(f"Starting stress sequence with {self.num_items} items (zero delays)")
        
        for i in range(self.num_items):
            # Create matrix item with random values but zero delays
            item = MatrixItem(f"stress_item_{i}")
            
            # Randomize matrix values normally
            for row in range(3):
                for col in range(3):
                    # Random signed 16-bit values
                    item.matrix[row][col] = random.randint(-32768, 32767)
                    # All delays set to 0 for stress testing
                    item.pre_element_delay[row][col] = 0
            
            print(f"Sending stress item {i}: Det={item.determinant_of_matrix()}")
            
            # Send item to driver
            await self.start_item(item)
            await self.finish_item(item)
            
        print(f"Stress sequence completed - sent {self.num_items} items with zero delays")

class SmallMatrixSequence(uvm_sequence):
    """Small value sequence - matrix elements limited to -32 to 32 range"""
    
    def __init__(self, name="SmallMatrixSequence"):
        super().__init__(name)
        self.num_items = 50  # Default number of small test items
        
    async def body(self):
        print(f"Starting small value sequence with {self.num_items} items (values -32 to 32)")
        
        for i in range(self.num_items):
            # Create matrix item with small random values
            item = MatrixItem(f"small_item_{i}")
            
            # Randomize matrix values in small range
            for row in range(3):
                for col in range(3):
                    # Random values between -32 and 32
                    item.matrix[row][col] = random.randint(-32, 32)
                    # Random delays
                    item.pre_element_delay[row][col] = random.randint(0, 5)
            
            print(f"Sending small item {i}: {item.convert2string()}")
            
            # Send item to driver
            await self.start_item(item)
            await self.finish_item(item)
            
        print(f"Small sequence completed - sent {self.num_items} items with small values")

class MultipleResetSequence(uvm_sequence):
    """Sequence that sends items while resets occur randomly during transmission"""
    
    def __init__(self, name="MultipleResetSequence"):
        super().__init__(name)
        self.num_items = 30  # Fewer items since resets will interrupt
        self.num_resets = 20  # Number of random resets to apply
        
    async def body(self):
        print(f"Starting multiple reset sequence with {self.num_items} items and {self.num_resets} random resets")
        
        # Start the reset task in parallel
        import cocotb
        reset_task = cocotb.start_soon(self._apply_random_resets())
        
        try:
            for i in range(self.num_items):
                # Create and randomize matrix item
                item = MatrixItem(f"reset_item_{i}")
                item.randomize()
                
                print(f"Attempting to send item {i}: {item.convert2string()}")
                
                try:
                    # Send item to driver (may be interrupted by reset)
                    await self.start_item(item)
                    await self.finish_item(item)
                    print(f"Successfully sent item {i}")
                    
                    # Small delay between items to allow for reset opportunities
                    await cocotb.triggers.Timer(100, units='ns')
                    
                except Exception as e:
                    print(f"Item {i} interrupted (likely by reset): {e}")
                    # Continue with next item
                    continue
                    
        finally:
            # Cancel the reset task when sequence is done
            reset_task.kill()
            
        print(f"Multiple reset sequence completed")
        
    async def _apply_random_resets(self):
        """Apply random resets during sequence execution"""
        import cocotb
        from cocotb.triggers import Timer, FallingEdge, RisingEdge
        
        # Get DUT handle from the test environment
        dut = cocotb.top
        
        for reset_num in range(self.num_resets):
            try:
                # Wait random time between resets (500ns to 2000ns)
                wait_time = random.randint(500, 2000)
                await Timer(wait_time, units='ns')
                
                print(f"Applying random reset #{reset_num + 1}")
                
                # Apply reset
                dut.rst_n.value = 0
                await Timer(50, units='ns')  # Hold reset for 50ns
                dut.rst_n.value = 1
                await Timer(20, units='ns')  # Wait for reset recovery
                
                print(f"Reset #{reset_num + 1} completed")
                
            except Exception as e:
                print(f"Error during reset #{reset_num + 1}: {e}")
                break