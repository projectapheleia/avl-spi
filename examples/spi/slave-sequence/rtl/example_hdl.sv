module example_hdl();


    logic clk, rst_n;

    spi_if#(.DATA_WIDTH(16))  spi_if();

    assign spi_if.clk = clk;
    assign spi_if.rst_n = rst_n;

endmodule : example_hdl
