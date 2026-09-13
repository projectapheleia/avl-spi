module example_hdl();


    logic clk, rst_n;

    spi_if#(.CS_WIDTH(3),
            .CS_POLARITY(3'b010),
            .DATA_WIDTH(64))  spi_if();

    assign spi_if.clk = clk;
    assign spi_if.rst_n = rst_n;

endmodule : example_hdl
