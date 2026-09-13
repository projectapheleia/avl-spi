module example_hdl();


    logic clk, rst_n;

    spi_if#(.CS_SETUP(3),
            .CS_HOLD(2),
            .CS_GAP(4),
            .DATA_WIDTH(8))  spi_if();

    assign spi_if.clk = clk;
    assign spi_if.rst_n = rst_n;

endmodule : example_hdl
