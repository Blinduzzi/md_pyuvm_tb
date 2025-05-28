"""
Matrix Determinant Environment
"""
import pyuvm
from pyuvm import *
from input_agent import MatrixAgent
from output_agent import DeterminantAgent
from scoreboard import MatrixScoreboard
from coverage_collector import CoverageCollector

class MatrixDetEnv(uvm_env):
    """Top-level environment for matrix determinant testbench"""
    
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.input_agent = None
        self.output_agent = None
        self.scoreboard = None
        self.coverage_collector = None
        
    def build_phase(self):
        super().build_phase()
        self.logger.info("Environment build_phase started")
        
        # Create agents
        self.input_agent = MatrixAgent("input_agent", self)
        self.output_agent = DeterminantAgent("output_agent", self)
        
        # Create scoreboard
        self.scoreboard = MatrixScoreboard("scoreboard", self)
        
        # Create coverage collector
        self.coverage_collector = CoverageCollector("coverage_collector", self)
        
        self.logger.info("Environment build_phase completed")
        
    def connect_phase(self):
        super().connect_phase()
        self.logger.info("Environment connect_phase started")
        
        # Connect input agent monitor to scoreboard input FIFO
        self.input_agent.monitor.ap.connect(self.scoreboard.input_ap)
        
        # Connect output agent monitor to scoreboard output FIFO
        self.output_agent.monitor.ap.connect(self.scoreboard.output_ap) 
        
        # Connect agents to coverage collector FIFOs
        self.input_agent.monitor.ap.connect(self.coverage_collector.input_ap)
        self.output_agent.monitor.ap.connect(self.coverage_collector.output_ap)
        
        self.logger.info("Environment connect_phase completed")
        
    async def run_phase(self):
        self.logger.info("Environment run_phase started")
        
        # Environment run phase - let agents handle their own run phases
        await super().run_phase()
        
        self.logger.info("Environment run_phase completed")