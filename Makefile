# Makefile for Matrix Determinant PyUVM Testbench

# Virtual environment settings
VENV_DIR = venv
VENV_PYTHON = $(VENV_DIR)/bin/python
VENV_PIP = $(VENV_DIR)/bin/pip

# Check if virtual environment exists
ifeq ($(shell test -d $(VENV_DIR) && echo exists), exists)
    PYTHON = $(VENV_PYTHON)
    export PATH := $(PWD)/$(VENV_DIR)/bin:$(PATH)
else
    PYTHON = python3
endif

# Simulator settings
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Verilog source files
VERILOG_SOURCES = matrix_determinant.v

# Top level module
TOPLEVEL = matrix_determinant

# Python test module
MODULE = test_matrix_det

# PyUVM and Cocotb settings
export PYTHONPATH := $(PWD):$(PYTHONPATH)

# Default test
TESTCASE ?= simple_matrix_test

# Enable waves by default for debugging
WAVES ?= 1
# Note: VCD generation is handled in the Verilog code itself

# Check dependencies
check-deps:
	@echo "Checking dependencies..."
	@$(PYTHON) -c "import cocotb; print(f'cocotb version: {cocotb.__version__}')" || (echo "cocotb not found. Install with: $(VENV_PIP) install cocotb"; exit 1)
	@$(PYTHON) -c "import pyuvm; print('pyuvm found')" || (echo "pyuvm not found. Install with: $(VENV_PIP) install pyuvm"; exit 1)
	@which iverilog > /dev/null || (echo "Icarus Verilog not found. Install with: sudo apt-get install iverilog"; exit 1)

# Setup virtual environment
setup-venv:
	python3 -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install cocotb pyuvm

# Include cocotb makefiles
include $(shell $(PYTHON) -m cocotb.config --makefiles)/Makefile.sim

# Convenience targets with dependency checking
simple: check-deps
	$(MAKE) sim TESTCASE=simple_matrix_test

random: check-deps
	$(MAKE) sim TESTCASE=random_matrix_test

# New test targets
stress: check-deps
	$(MAKE) sim TESTCASE=stress_matrix_test

small: check-deps  
	$(MAKE) sim TESTCASE=small_matrix_test

multiple-reset: check-deps
	$(MAKE) sim TESTCASE=multiple_reset_test

# Run all tests sequentially
test-all: check-deps
	@echo "Running all test cases..."
	$(MAKE) simple
	$(MAKE) random
	$(MAKE) stress
	$(MAKE) small
	$(MAKE) multiple-reset
	@echo "All tests completed!"

# Run with custom test case
run: check-deps
	$(MAKE) sim TESTCASE=$(TESTCASE)

# Full clean including virtual environment
clean-all: clean
	rm -rf $(VENV_DIR)

# Help
help:
	@echo "Available targets:"
	@echo "  setup-venv     - Create virtual environment and install dependencies"
	@echo "  check-deps     - Check if dependencies are installed"
	@echo "  sim            - Run simulation with default test"
	@echo "  simple         - Run simple matrix test"
	@echo "  random         - Run random matrix test"
	@echo "  stress         - Run stress test (zero delays, max throughput)"
	@echo "  small          - Run small value test (values -32 to 32)"
	@echo "  multiple-reset - Run multiple reset test (20 random resets)"
	@echo "  test-all       - Run all test cases sequentially"
	@echo "  run            - Run custom test case"
	@echo "  clean          - Clean build files"
	@echo "  clean-all      - Clean build files and virtual environment"
	@echo ""
	@echo "Available environment variables:"
	@echo "  SIM            - Simulator (icarus, verilator, etc.)"
	@echo "  TESTCASE       - Test case to run"
	@echo "  WAVES          - Enable waveform generation (1/0)"
	@echo ""
	@echo "Usage examples:"
	@echo "  make simple                    - Run simple test"
	@echo "  make stress WAVES=0            - Run stress test without waves"
	@echo "  make small                     - Run small value test"
	@echo "  make multiple-reset            - Run reset test"
	@echo "  make test-all                  - Run all tests"
	@echo "  make run TESTCASE=my_test      - Run custom test case"
	@echo ""
	@echo "Test descriptions:"
	@echo "  simple         - Identity matrix and basic patterns"
	@echo "  random         - Random matrix values (full range)"
	@echo "  stress         - Zero delays for maximum throughput testing"
	@echo "  small          - Small values (-32 to 32) to avoid overflow"
	@echo "  multiple-reset - Random resets during traffic transmission"

.PHONY: clean clean-all help simple random stress small multiple-reset test-all setup-venv check-deps run sim