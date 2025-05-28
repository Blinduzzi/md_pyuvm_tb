"""
Matrix Input Agent Components - Updated with proper task cleanup
"""
import pyuvm
from pyuvm import *
import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from matrix_det_items import MatrixItem
from matrix_det_types import *

class MatrixDriver(uvm_driver):
    """Driver for matrix input interface - Multiple reset resistant with proper task killing"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut = None
        self.finished_item = False
        self.has_init_reset = False
        self.drive_task = None  # Track the active drive task
        self.reset_task = None  # Track the reset driver task
        self.idle_data = "HIGH_IMPEDANCE"  # Can be "HIGH_IMPEDANCE", "UNKNOWN", or "ZERO"
        
    def build_phase(self):
        super().build_phase()
        self.logger.info("Matrix Driver build_phase completed")
        
    async def run_phase(self):
        self.logger.info("Matrix Driver run_phase started")
        
        try:
            # Start the reset driver in the background - track the task
            self.reset_task = cocotb.start_soon(self.reset_driver())
            
            # Run main driving loop
            await self.main_drive_loop()
            
        except Exception as e:
            self.logger.error(f"Error in driver run_phase: {e}")
        finally:
            # Clean up reset task when main loop finishes
            if self.reset_task is not None and not self.reset_task.done():
                self.logger.info("Killing reset driver task")
                self.reset_task.kill()
                
            self.logger.info("Matrix Driver run_phase completed")
                
    async def main_drive_loop(self):
        """Main driving loop that handles reset properly"""
        # Handle initial reset
        if not self.has_init_reset:
            await FallingEdge(self.dut.rst_n)
            self.has_init_reset = True
            
        while True:
            try:
                # Wait for reset to be released before starting any new item
                while self.dut.rst_n.value == 0:
                    await RisingEdge(self.dut.clk)
                    
                # Make sure we have a clean state after reset
                await RisingEdge(self.dut.rst_n)
                await RisingEdge(self.dut.clk)  # One more clock to be safe
                
                # Get item from sequencer
                item = await self.seq_item_port.get_next_item()
                self.logger.debug(f"Driving item: {item.convert2string()}")
                
                # Mark as started
                self.finished_item = False
                
                # Start the drive task and keep reference to it
                self.drive_task = cocotb.start_soon(self.drive_matrix(item))
                
                # Wait for drive task to complete
                await self.drive_task
                
                # Mark as finished and signal done
                self.finished_item = True
                self.seq_item_port.item_done()
                
                self.logger.debug(f"Completed driving item")
                
            except cocotb.exceptions.Kill:
                # Task was killed due to reset
                self.logger.info("Drive task killed by reset")
                # Handle incomplete items
                if not self.finished_item:
                    self.finished_item = True
                    # Don't call item_done() when killed by reset, let sequencer handle it
                continue
            except Exception as e:
                self.logger.error(f"Error in main_drive_loop: {e}")
                # If we have an unfinished item, mark it as done
                if not self.finished_item:
                    self.finished_item = True
                    self.seq_item_port.item_done()
                await Timer(100, units='ns')  # Brief pause before retry
                
    async def drive_matrix(self, item):
        """Drive matrix elements to DUT with proper timing and reset checking"""
        if self.dut is None:
            self.logger.error("DUT handle not set")
            return

        await RisingEdge(self.dut.clk)

        # Drive each matrix element
        for i in range(MAT_MATRIX_SIZE):
            for j in range(MAT_MATRIX_SIZE):
                # Check for reset before each element
                if self.dut.rst_n.value == 0:
                    self.logger.info(f"Reset detected during element [{i}][{j}], aborting drive")
                    raise cocotb.exceptions.Kill()
                
                # Apply pre-element delay if specified
                if item.pre_element_delay[i][j] > 0:
                    # Deassert mat_valid during delay
                    self.dut.mat_valid.value = 0
                    
                    # Apply idle data during delay
                    for delay_cycle in range(item.pre_element_delay[i][j]):
                        # Check for reset during delay
                        if self.dut.rst_n.value == 0:
                            self.logger.info(f"Reset detected during delay for element [{i}][{j}], aborting drive")
                            raise cocotb.exceptions.Kill()
                            
                        self._drive_idle_data()
                        await RisingEdge(self.dut.clk)
                
                # Check for reset before driving element
                if self.dut.rst_n.value == 0:
                    self.logger.info(f"Reset detected before driving element [{i}][{j}], aborting drive")
                    raise cocotb.exceptions.Kill()
                
                # Drive the matrix element
                self.dut.mat_valid.value = 1
                self.dut.mat_in.value = item.matrix[i][j] & 0xFFFF  # Mask to 16 bits
                await RisingEdge(self.dut.clk)
                
                # Wait for mat_request to be asserted (handshake)
                while self.dut.mat_request.value != 1:
                    # Check for reset during handshake wait
                    if self.dut.rst_n.value == 0:
                        self.logger.info(f"Reset detected during handshake for element [{i}][{j}], aborting drive")
                        raise cocotb.exceptions.Kill()
                        
                    self.dut.mat_valid.value = 0
                    self._drive_idle_data()
                    await RisingEdge(self.dut.clk)
        
        # Deassert mat_valid at the end of the item
        self.dut.mat_valid.value = 0
        self._drive_idle_data()
        
    def _drive_idle_data(self):
        """Drive appropriate idle data based on configuration"""
        if self.idle_data == "HIGH_IMPEDANCE":
            # PyUVM/Cocotb doesn't support high-Z, so we'll use 0
            self.dut.mat_in.value = 0
        elif self.idle_data == "UNKNOWN":
            # Drive unknown/X state - use random pattern
            self.dut.mat_in.value = 0xAAAA  # Alternating pattern
        else:  # Default to zero
            self.dut.mat_in.value = 0
            
    async def reset_driver(self):
        """Handle reset events and cleanup - runs forever in background"""
        while True:
            try:
                # Wait for reset assertion
                await FallingEdge(self.dut.rst_n)
                
                self.logger.info("Reset detected in driver")
                
                # Kill any active drive task
                if self.drive_task is not None and not self.drive_task.done():
                    self.logger.info("Killing active drive task due to reset")
                    self.drive_task.kill()
                    
                # Reset interface signals immediately
                self.reset_interface_signals()
                
                # Handle incomplete items
                if not self.finished_item:
                    self.logger.info("Marking incomplete item as finished due to reset")
                    self.finished_item = True
                    
            except Exception as e:
                self.logger.error(f"Error in reset_driver: {e}")
                await Timer(10, units='ns')
        
    def reset_interface_signals(self):
        """Reset interface signals to idle state"""
        if self.dut is not None:
            self.dut.mat_valid.value = 0
            self._drive_idle_data()
            self.logger.debug("Interface signals reset to idle state")

class MatrixMonitor(uvm_monitor):
    """Matrix Monitor based on SystemVerilog reference implementation - Updated with proper task cleanup"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut = None
        self.ap = uvm_analysis_port("ap", self)
        self.has_init_reset = False
        self.valid_process = None
        self.reset_task = None  # Track the reset monitor task
        
    def build_phase(self):
        super().build_phase()
        self.logger.info("Matrix Monitor build_phase completed")
        
    async def run_phase(self):
        self.logger.info("Matrix Monitor run_phase started")
        
        try:
            while True:
                try:
                    # Fork reset detection and monitoring logic (like SystemVerilog)
                    self.reset_task = cocotb.start_soon(self.reset_monitor())
                    monitor_task = cocotb.start_soon(self.monitor_valid_item())
                    
                    # Wait for either to complete
                    await cocotb.triggers.First(self.reset_task, monitor_task)
                    
                except Exception as e:
                    self.logger.error(f"Monitor run_phase exception: {e}")
                    await Timer(100, units='ns')
                    
        except Exception as e:
            self.logger.error(f"Error in monitor run_phase: {e}")
        finally:
            # Clean up reset task when monitor finishes
            if self.reset_task is not None and not self.reset_task.done():
                self.logger.info("Killing reset monitor task")
                self.reset_task.kill()
                
            self.logger.info("Matrix Monitor run_phase completed")
                
    async def monitor_valid_item(self):
        """Monitor valid items - exact translation of SystemVerilog logic"""
        
        # Handle initial reset (like SystemVerilog)
        if not self.has_init_reset:
            await FallingEdge(self.dut.rst_n)
            
        await RisingEdge(self.dut.rst_n)
        
        while True:
            try:
                # Create the monitored item
                collected_valid_item = MatrixItem("collected_valid_item")
                
                # Monitor 3x3 matrix elements
                for i in range(MAT_MATRIX_SIZE):
                    for j in range(MAT_MATRIX_SIZE):
                        pre_delay = 0
                        
                        await RisingEdge(self.dut.clk)
                        
                        # Wait for both mat_request AND mat_valid to be high
                        while not (self.dut.mat_request.value == 1 and self.dut.mat_valid.value == 1):
                            await RisingEdge(self.dut.clk)
                            pre_delay += 1
                            
                        # Capture the data and delay
                        collected_valid_item.pre_element_delay[i][j] = pre_delay
                        
                        # Get raw value and handle signed conversion
                        raw_value = int(self.dut.mat_in.value)
                        if raw_value > 32767:
                            signed_value = raw_value - 65536
                        else:
                            signed_value = raw_value
                            
                        collected_valid_item.matrix[i][j] = signed_value
                        
                        self.logger.debug(f"Element [{i}][{j}] = {signed_value}, delay = {pre_delay}")
                
                self.logger.info(f"Input Monitor collected item: {collected_valid_item.convert2string()}")
                
                # Write item to analysis port
                self.ap.write(collected_valid_item)
                
                # Wait for mat_request to go high again (end of transaction)
                await RisingEdge(self.dut.mat_request)
                
            except Exception as e:
                self.logger.error(f"Error in monitor_valid_item: {e}")
                break
                
    async def reset_monitor(self):
        """Reset monitor"""
        while True:
            # Wait for reset assertion
            await FallingEdge(self.dut.rst_n)
            
            self.logger.info("Resetting input monitor")
            
            # Kill the valid process if it exists
            if self.valid_process is not None:
                self.valid_process.kill()
                
            # Reset local variables
            self.reset_local_variables()
        
    def reset_local_variables(self):
        """Reset local state"""
        if not self.has_init_reset:
            self.has_init_reset = True

class MatrixSequencer(uvm_sequencer):
    """Sequencer for matrix items"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        
    def build_phase(self):
        super().build_phase()
        self.logger.info("Matrix Sequencer build_phase completed")

class MatrixAgent(uvm_agent):
    """Input agent for matrix interface"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.driver = None
        self.monitor = None
        self.sequencer = None
        
    def build_phase(self):
        super().build_phase()
        self.logger.info("Matrix Agent build_phase started")
        
        # Create components
        self.monitor = MatrixMonitor("monitor", self)
        self.sequencer = MatrixSequencer("sequencer", self)
        self.driver = MatrixDriver("driver", self)
        
        self.logger.info("Matrix Agent build_phase completed")
        
    def connect_phase(self):
        super().connect_phase()
        self.logger.info("Matrix Agent connect_phase started")
        
        # Connect driver to sequencer
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
        
        self.logger.info("Matrix Agent connect_phase completed")