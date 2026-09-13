module example_hdl();


    logic clk, rst_n;

    spi_if#(.CS_POLARITY(1'b1),
            .CPOL(1),
            .MASTER_DRIVE_EDGE(1),
            .MASTER_SAMPLE_EDGE(0),
            .SLAVE_DRIVE_EDGE(1),
            .SLAVE_SAMPLE_EDGE(0),
            .DATA_WIDTH(16))  spi_if();

    assign spi_if.clk = clk;
    assign spi_if.rst_n = rst_n;

endmodule : example_hdl
