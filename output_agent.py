"""
Matrix Output Agent Components
"""
import pyuvm
from pyuvm import *
import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from matrix_det_items import DeterminantItem
from matrix_det_types import *

class DeterminantMonitor(uvm_monitor):
    """Monitor for determinant output interface - Multiple reset resistant"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut = None
        self.ap = uvm_analysis_port("ap", self)
        self.has_init_reset = False
        self.valid_process = None
        
    def build_phase(self):
        super().build_phase()
        self.logger.info("Determinant Monitor build_phase completed")
        
    async def run_phase(self):
        self.logger.info("Determinant Monitor run_phase started")
        
        while True:
            try:
                # Fork reset detection and monitoring logic (like input agent)
                reset_task = cocotb.start_soon(self.reset_monitor())
                monitor_task = cocotb.start_soon(self.monitor_valid_item())
                
                # Wait for either to complete
                await cocotb.triggers.First(reset_task, monitor_task)
                
            except Exception as e:
                self.logger.error(f"Determinant Monitor run_phase exception: {e}")
                await Timer(100, units='ns')  # Brief pause before retry
                
    async def monitor_valid_item(self):
        """Monitor valid determinant items - exact translation matching input agent style"""
        
        # Handle initial reset (like input agent)
        if not self.has_init_reset:
            await FallingEdge(self.dut.rst_n)
            
        await RisingEdge(self.dut.rst_n)
        
        while True:
            try:
                # Create the monitored item
                collected_valid_item = DeterminantItem("collected_valid_det_item")
                
                pre_delay = 0
                await RisingEdge(self.dut.clk)
                
                # Wait for det_valid to be asserted
                while self.dut.det_valid.value != 1:
                    await RisingEdge(self.dut.clk)
                    pre_delay += 1
                
                # Capture the determinant data
                collected_valid_item.pre_det_delay = pre_delay
                
                # Get raw determinant value and handle signed conversion
                raw_det_value = int(self.dut.det.value)
                if raw_det_value > 32767:
                    signed_det_value = raw_det_value - 65536
                else:
                    signed_det_value = raw_det_value
                    
                collected_valid_item.determinant = signed_det_value
                collected_valid_item.overflow = bool(self.dut.overflow.value)
                
                self.logger.debug(f"Determinant = {signed_det_value}, Overflow = {collected_valid_item.overflow}, Delay = {pre_delay}")
                self.logger.info(f"Output Monitor collected item: {collected_valid_item.convert2string()}")
                
                # Write item to analysis port
                self.ap.write(collected_valid_item)
                
                # Wait for det_valid to go low (end of transaction)
                while self.dut.det_valid.value == 1:
                    await RisingEdge(self.dut.clk)
                
            except Exception as e:
                self.logger.error(f"Error in monitor_valid_item: {e}")
                break
                
    async def reset_monitor(self):
        """Reset monitor - matching input agent implementation"""
        while True:
            # Wait for reset assertion
            await FallingEdge(self.dut.rst_n)
            
            self.logger.info("Resetting output monitor")
            
            # Kill the valid process if it exists
            if self.valid_process is not None:
                self.valid_process.kill()
                
            # Reset local variables
            self.reset_local_variables()
        
    def reset_local_variables(self):
        """Reset local state - matching input agent"""
        if not self.has_init_reset:
            self.has_init_reset = True

class DeterminantAgent(uvm_agent):
    """Output agent for determinant interface - Updated to match input agent style"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.monitor = None
        
    def build_phase(self):
        super().build_phase()
        self.logger.info("Determinant Agent build_phase started")
        
        # Create monitor (passive agent - no driver/sequencer needed)
        self.monitor = DeterminantMonitor("monitor", self)
        
        self.logger.info("Determinant Agent build_phase completed")
        
    def connect_phase(self):
        super().connect_phase()
        self.logger.info("Determinant Agent connect_phase started")
        
        # No connections needed for passive agent
        
        self.logger.info("Determinant Agent connect_phase completed")