# ADV7280A-M decoder on the CM4 baseboard (from sdtv2csi)

Source: github.com/rniwase/sdtv2csi (KiCad 9 schematic + PCB, MIT). Board photo: sdtv2csi/misc/*.jpg.

## What the reference board contains
- U1 ADV7280A-M (Analog Devices SDTV video decoder, MIPI CSI-2 output, 1 data lane).
- U2 NJM12888F18 LDO: 3.3 V in → 1.8 V for AVDD/DVDD/MVDD/PVDD (each rail through a 600 Ω ferrite bead, 0.1 µF + 10 µF per rail). DVDDIO = 3.3 V.
- Y1 ABM8G 28.63636 MHz crystal, 2 × 20 pF.
- 8 analogue inputs AIN1–AIN8: each VINx → 24 Ω series → 0.1 µF (AC coupling) → AINx, 51 Ω to GND at the input (termination). Inputs come from a 2×8 pin header (VIDEO_IN).
- CSI-2: D0P/D0N (U1 pins 9/10) and CLKP/CLKN (11/12) to the 15-pin Raspberry Pi camera FFC; D1 pins on the FFC left unconnected.
- I2C: SDA/SCL (U1 30/31) to FFC pins 2/3 (= CM4 SDA0/SCL0). ALSB (29) via 4.7 kΩ pull-up (R20) with DNP pull-down (R21): ALSB high → I2C address 0x21 (7-bit), low → 0x20.
- ~RESET (28): 4.7 kΩ pull-up + 4.7 µF to GND (RC power-on reset). ~PWRDWN (32): 4.7 kΩ pull-up. ~INTRQ, GPO0–GPO2: test points only.
- FFC pins 4/5 ("GPIO0/GPIO1" nets): test points only, not used by the decoder.

## Software (Raspberry Pi OS)
- `dtoverlay=adv728x-m,adv7280m=1` (default I2C address 0x21; `addr=0x20` if ALSB is low). The overlay targets CAM1 = CSI1 with I2C on `i2c_csi_dsi` (CM4 SDA0/SCL0, pins 82/80). Kernel driver adv7180 (patched for 507-line NTSC frames in sdtv2csi/rpi/install_patch.sh).

## Consequences for the CM4 pinout (decided 2026-09-13)
- CSI1 D0 (pins 115/117) and CSI1 clock (127/129) → ADV7280A-M. CSI1 D1–D3 unused → leave unconnected.
- I2C0 (pins 82/80) shared by the CSI0 camera and the decoder (0x20/0x21). A CSI0 camera must use a custom overlay variant with `i2c_csi_dsi` (stock `cam0` variants expect I2C on GPIO0/1, which are UART2 on this board).
- No CM4 GPIO for the decoder: reset by RC, power-down pulled up (as on sdtv2csi). CVBS switch + K7 encoder path is kept in parallel.
