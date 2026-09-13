// Copyright 2026 Apheleia
//
// Description:
// Apheleia Verification Library SPI Interface
// As described in https://en.wikipedia.org/wiki/Serial_Peripheral_Interface
//
// Edge parameters: 0 = falling edge, 1 = rising edge
// Timing parameters: clk cycles (0 = unchecked)

interface spi_if #(parameter string               CLASSIFICATION     = "SPI",
                   parameter int                  CS_WIDTH           = 1,
                   parameter logic [CS_WIDTH-1:0] CS_POLARITY        = '0,
                   parameter int                  CS_SETUP           = 1,
                   parameter int                  CS_HOLD            = 1,
                   parameter int                  CS_GAP             = 1,
                   parameter bit                  CPOL               = 0,
                   parameter bit                  MASTER_DRIVE_EDGE  = 0,
                   parameter bit                  MASTER_SAMPLE_EDGE = 1,
                   parameter bit                  SLAVE_DRIVE_EDGE   = 0,
                   parameter bit                  SLAVE_SAMPLE_EDGE  = 1,
                   parameter bit                  LSB_FIRST          = 0,
                   parameter int                  DATA_WIDTH         = 8)();

    logic                clk;
    logic                rst_n;
    logic                sclk;
    logic [CS_WIDTH-1:0] cs;
    logic                mosi;
    logic                miso;

    // Chip select must be onehot0 (after polarity) out of reset
    // Deliberately a clocked immediate check with $fatal to be supported on the widest range of simulators
    always @(posedge clk) begin : cs_onehot0
        logic [CS_WIDTH-1:0] active;
        active = ~(cs ^ CS_POLARITY);
        if ((rst_n === 1'b1) && ((active & (active - 1'b1)) != '0))
            $fatal(1, "%m: cs (%b) is not onehot0 (CS_POLARITY %b)", cs, CS_POLARITY);
    end : cs_onehot0

    // Chip select setup (assertion to first SCLK edge), hold (last SCLK edge to de-assertion)
    // and inter-frame gap (de-assertion to next assertion) in clk cycles, out of reset
    // Deliberately a clocked immediate check with $fatal to be supported on the widest range of simulators
    int unsigned         cs_setup_cnt;
    int unsigned         cs_hold_cnt;
    int unsigned         cs_gap_cnt;
    logic [CS_WIDTH-1:0] cs_active_q;
    logic                sclk_q;
    logic                sclk_seen;

    always @(posedge clk) begin : cs_timing
        logic [CS_WIDTH-1:0] active;
        logic                sclk_edge;
        active    = ~(cs ^ CS_POLARITY);
        sclk_edge = (sclk != sclk_q);

        if (rst_n !== 1'b1) begin
            cs_gap_cnt  = CS_GAP;
            cs_active_q = '0;
            sclk_seen   = 1'b0;
        end else begin
            // Saturating counts since each event
            if (cs_setup_cnt < CS_SETUP) cs_setup_cnt++;
            if (cs_hold_cnt  < CS_HOLD)  cs_hold_cnt++;
            if (cs_gap_cnt   < CS_GAP)   cs_gap_cnt++;

            // End of frame
            if ((cs_active_q != '0) && (active != cs_active_q)) begin
                if ((sclk_seen || sclk_edge) && ((sclk_edge ? 0 : cs_hold_cnt) < CS_HOLD))
                    $fatal(1, "%m: cs hold (%0d) less than CS_HOLD (%0d) clk cycles", (sclk_edge ? 0 : cs_hold_cnt), CS_HOLD);
                cs_gap_cnt = 0;
                sclk_seen  = 1'b0;
            end

            // Start of frame
            if ((active != '0) && (active != cs_active_q)) begin
                if (cs_gap_cnt < CS_GAP)
                    $fatal(1, "%m: cs gap (%0d) less than CS_GAP (%0d) clk cycles", cs_gap_cnt, CS_GAP);
                cs_setup_cnt = 0;
                sclk_seen    = 1'b0;
            end

            // SCLK edge within frame
            if (sclk_edge && (active != '0)) begin
                if (!sclk_seen && (cs_setup_cnt < CS_SETUP))
                    $fatal(1, "%m: cs setup (%0d) less than CS_SETUP (%0d) clk cycles", cs_setup_cnt, CS_SETUP);
                sclk_seen   = 1'b1;
                cs_hold_cnt = 0;
            end

            cs_active_q = active;
        end

        sclk_q = sclk;
    end : cs_timing

endinterface : spi_if
