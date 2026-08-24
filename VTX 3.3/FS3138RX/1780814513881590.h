/***************************************************************************************************
 @file  PLL.h
 @brief This file contains the interface to the KEY Service.
 Group:
 Target Device:
***************************************************************************************************/
#ifndef PLL_H
#define PLL_H

/***************************************************************************************************
 *                                                 EXTERNS
 ***************************************************************************************************/
#ifdef PLL_MODULE
#define PLL_EXT
#else
#define PLL_EXT extern
#endif

#include "types.h"

#define C_Bit0 0x0001
#define C_Bit1 0x0002
#define C_Bit2 0x0004
#define C_Bit3 0x0008
#define C_Bit4 0x0010
#define C_Bit5 0x0020
#define C_Bit6 0x0040
#define C_Bit7 0x0080

#define C_Bit00 0x00000001
#define C_Bit01 0x00000002
#define C_Bit02 0x00000004
#define C_Bit03 0x00000008
#define C_Bit04 0x00000010
#define C_Bit05 0x00000020
#define C_Bit06 0x00000040
#define C_Bit07 0x00000080
#define C_Bit08 0x00000100
#define C_Bit09 0x00000200
#define C_Bit10 0x00000400
#define C_Bit11 0x00000800
#define C_Bit12 0x00001000
#define C_Bit13 0x00002000
#define C_Bit14 0x00004000
#define C_Bit15 0x00008000
#define C_Bit16 0x00010000
#define C_Bit17 0x00020000
#define C_Bit18 0x00040000
#define C_Bit19 0x00080000
#define C_Bit20 0x00100000
#define C_Bit21 0x00200000
#define C_Bit22 0x00400000
#define C_Bit23 0x00800000
#define C_Bit24 0x01000000
#define C_Bit25 0x02000000
#define C_Bit26 0x04000000
#define C_Bit27 0x08000000
#define C_Bit28 0x10000000
#define C_Bit29 0x20000000
#define C_Bit30 0x40000000
#define C_Bit31 0x80000000

//*********************************  pll
//****************************************************
#define rdorwt_data 0 //
#define ref (20) // 参考频率20MHz // 50        // ( 20M )
#define fref_div 1    // ( 20M/2=10M )

// REG0
#define lk_sw 0   //
#define vco_bit 2 // VCO
#define en_cp 1   //
#define spi_cp 24 // CP 32x25uA

// REG1
#define fdiv_sw 1 // 4/5 or 8/9
#define conrt3b 1 // SDM

// REG2
#define muxout 1   //
#define mode 65536 // MOD: 65536 / 10000000

// REG3
#define vco_currt 3     // 0				// VCO1.5mA
#define spi_or_afc 3    // AFC
#define spi_vco 53      //
#define vco_cnt_num 800 // VCO_CNT
#define md_is 0         // MD_IS

// REG4
#define ldo_sw 2    // power( H-2 / L-3 )
#define afc_r_sw 16 // AFC

// REG5
#define pfd_delay_d 0  //
#define pfd_delay_en 1 //
#define lfsr_sel 2     //
#define bit_sel 2      //
//*********************************  pll
//****************************************************

/***************************************************************************************************
 *																				FUNCTIONS
 * - Local
 ***************************************************************************************************/
#ifdef PLL_MODULE
// u32		u32_TransmitData;
// u08		u8_Freq_TabelOffset;
// u08		u8_FreqGroup;

#endif

/***************************************************************************************************
 *																				FUNCTIONS
 * - Glocal
 ***************************************************************************************************/
PLL_EXT u16 code Tab_PLL_Freq[16]; //

PLL_EXT void PLL_SetFreq(u08 Group, u08 ch);

#endif
