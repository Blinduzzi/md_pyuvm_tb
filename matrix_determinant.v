`ifndef MATRIX_DETERMINANT
`define MATRIX_DETERMINANT
`endif
module matrix_determinant (
		input reg[15:0] mat_in,
		input reg mat_valid, //for mat_in signal validation
		input reg clk,
		input reg rst_n,
		output reg mat_request, //if matrix needs more elements
		output reg[15:0] det,
		output reg det_valid, //if det is valid
		output reg overflow
	);

	shortint mat[2:0][2:0]; //the matrix
	reg step; //indicates what step I'm at when clk is 1
	reg[1:0] row; //index of the current row in the matrix
	reg[1:0] col; //index of the current column in the matrix
	reg[63:0] r_det; //for overflow checking

	localparam ZERO = 2'b00;
	localparam ONE = 2'b01;
	localparam TWO = 2'b10;
	//signed value of determinant
	longint det_int = 0;

	// VCD dump for debugging
	initial begin
		$dumpfile("matrix_det.vcd");
		$dumpvars(0, matrix_determinant);
	end

	always@(negedge rst_n) begin //reset the values
		step <= ZERO;
		row <= 2'b0;
		col <= 2'b0;
		det <= 16'h0000;
		det_valid <= 1'b0;
		overflow <= 1'd0;
		mat_request <= 1'b1;
	end

	always@(posedge clk) begin
		case (step)
			ZERO:
				//fill the matrix here
				if (mat_valid) begin
					mat[row][col] = mat_in;

					if ((row == TWO) && (col == TWO)) begin //end of matrix
						mat_request <= 1'b0;
						det_valid <= 1'b1;

						//calculate determinant
						r_det = ((mat[0][0] * mat[1][1] * mat[2][2]) + (mat[0][1] * mat[1][2] * mat[2][0]) + (mat[0][2] * mat[1][0] * mat[2][1]) - (mat[0][2] * mat[1][1] * mat[2][0]) - (mat[0][1] * mat[1][0] * mat[2][2]) - (mat[0][0] * mat[1][2] * mat[2][1])); /* @DVT_LINTER_WAIVER "Generated Code Waiver" DISABLE SVTB.1.1.3 */ /* @DVT_LINTER_WAIVER "Generated Code Waiver" DISABLE SVTB.1.1.4 */
						det <= r_det;

						det_int = r_det;

						if ((det_int < -32768) || (det_int > 32767)) begin
							overflow = 1'b1;

							if (det_int < -32768) begin
								det <= 16'h8000;
							end

							else begin
								det <= 16'h7FFF;
							end

							step <= ONE;
						end else begin
							overflow <= 1'b0;
							step <= ONE;
						end
					end

					if ((row != TWO) && (col == TWO)) begin //new row
						row <= row + 1;
						col <= 2'b00;
					end

					if (col != TWO) begin //same row, next column
						col <= col + 1;
					end
				end

			ONE: begin
				det_valid <= 1'b0;
				mat_request <= 1'b1;
				overflow <= 1'b0;
				row <= 2'b0;
				col <= 2'b0;
				step <= ZERO;
			end
			default begin
				step <= ZERO;
			end
		endcase
	end

endmodule