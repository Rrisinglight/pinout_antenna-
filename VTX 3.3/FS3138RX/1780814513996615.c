/******************************************************************************
 @file  PLL.c
 @brief
 Group:
 Target Device: N7E003
******************************************************************************/
#define PLL_MODULE

#include "N76E003.h"
#include "SFR_Macro.h"
#include "Function_define.h"
#include "bsp.h"
#include "process.h"
#include "PLL.h"
#include "cSystem.h"
#include "tramp.h"


#define S_SPI_CLK_L()		st( P15_SPI_CLK		= 0;	)
#define S_SPI_CLK_H()		st( P15_SPI_CLK		= 1;	)
#define S_SPI_DATA_L()	st( P11_SPI_DATA	= 0;	)
#define S_SPI_DATA_H()	st( P11_SPI_DATA	= 1;	)
#define S_SPI_LE_L()		st( P10_SPI_CE		= 0;	)
#define S_SPI_LE_H()		st( P10_SPI_CE		= 1;	)

u16 code Tab_PLL_Freq[16] =
{// 1			2			3			4			5			6			7			8
	2690,	2710,	2730,	2750,	2770,	2790,	2810,	2830,	// Rx
	2850,	2870,	2890,	2910,	2930,	2950,	2970,	2990,	// Rx
};

/*******************************************************************************
*:	Spi_Nop
*:
*******************************************************************************/
void Spi_Nop(void)
{
	u08 u8_Temp=10;		// 8051_16MHz
	while(u8_Temp)	{ u8_Temp--;	}
}

/*******************************************************************************
*:	Spi_CmdNop
*:
*******************************************************************************/
void Spi_CmdNop(void)
{
	u08 u8_Temp=10;		// 8051_16MHz
	while(u8_Temp)	{ u8_Temp--;	Spi_Nop();}
}

/*******************************************************************************
*:	SpiWrite
*:
*******************************************************************************/
void SpiWrite(u32 u32_SPI_Data)
{
	u08		u8_SPI_Bitx		= 32;
	u32		u32_Data			= u32_SPI_Data;

//S_SPI_Mode();
	Spi_Nop();
	S_SPI_LE_L();		Spi_Nop();Spi_Nop();
	S_SPI_CLK_L();	Spi_Nop();Spi_Nop();
	while(u8_SPI_Bitx!=0)
	{
		Spi_Nop();
		if((u32_Data&C_Bit31)==0)	{ S_SPI_DATA_L();	}
		else											{ S_SPI_DATA_H();	}
		Spi_Nop();

		S_SPI_CLK_H();	Spi_Nop();	Spi_Nop();
		S_SPI_CLK_L();
		u32_Data = u32_Data<<1;
		u8_SPI_Bitx--;
	}
	Spi_Nop();
	S_SPI_LE_H();	Spi_Nop();
}

/*******************************************************************************
*:	PLL_SetFreq
*:
*******************************************************************************/
void PLL_SetFreq(u08 Group, u08 ch)
{
	u08 a0Buf[4], a1Buf[4], a2Buf[4], a3Buf[4], a4Buf[4], a5Buf[4];
	u08 temp;
	double freq, freq_out, frac_and_mod;

	u32 int_data;
	u32 frac_data;
	u32 spi_divider;
	u32 vco_sel;

	temp	= (Group-1)*8+(ch-1);
	freq	= (u32)Tab_PLL_Freq[temp];

	if		 (freq>=1620		&& freq<=3500)	{ spi_divider = 1;		}
	else if(freq>=810			&& freq<1620)		{ spi_divider = 2;		}
	else if(freq>=405			&& freq<810)		{ spi_divider = 4;		}
	else if(freq>=202.5 	&& freq<405)		{ spi_divider = 8;		}
	else if(freq>=101.25	&& freq<202.5)	{ spi_divider = 16;		}
	else if(freq>=50.625	&& freq<101.25)	{ spi_divider = 32;		}
	else if(freq>=25			&& freq<50.625)	{ spi_divider = 64;		}

	freq_out			= freq * (double)fref_div * (double)spi_divider / (double)ref;
	int_data			= (u32)(freq_out);
	frac_and_mod	= freq_out - (double)int_data;
	frac_data			= (u32)(frac_and_mod * (double)mode);		//

//if(freq*fref_div>=2400)			{ vco_sel = 1;	}
	if(freq*spi_divider>=2400)	{ vco_sel = 1;	}
	else												{ vco_sel = 0;	}

	a0Buf[0] = (0x00 | (0x10 & (rdorwt_data << 4)) | ( 0x08 & (lk_sw << 3)) | ( 0x06 & (vco_bit << 1)) | ( 0x01 & (en_cp << 0)));
	a0Buf[1] = (0xFF & (spi_cp));				
	a0Buf[2] = (0xFF & (int_data >> 8));
	a0Buf[3] = (0xFF & (int_data));

	a1Buf[0] = (0x20 | (0x10 & (rdorwt_data << 4)) | (0x08 & (fdiv_sw << 3)) | (0x07 & conrt3b));
	a1Buf[1] = (0xFF & (frac_data >> 16));		
	a1Buf[2] = (0xFF & (frac_data >> 8));			
	a1Buf[3] = (0xFF & (frac_data >> 0));			

	a2Buf[0] = (0x40 | (0x10 & (rdorwt_data << 4)) | (0x0E & (muxout << 1) | (0x01 & (mode >> 24))));	
	a2Buf[1] = (0xFF & (mode >> 16));			
	a2Buf[2] = (0xFF & (mode >> 8));			
	a2Buf[3] = (0xFF & (mode >> 0)); 			

	a3Buf[0] =  (0x60 | (0x10 & (rdorwt_data << 4)) | (0x02 & (vco_currt << 1)) | (0x01 & (vco_sel << 0)));
	a3Buf[1] = ((0x40 & (spi_or_afc << 6)) | (0x3F & (spi_vco)));
	a3Buf[2] =  (0xFF & (vco_cnt_num >> 2));
	a3Buf[3] = ((0xC0 & (vco_cnt_num << 6)) | (0x3F & (md_is)));

	a4Buf[0] =  (0x80 | (0x10 & (rdorwt_data << 4)) | (0x0C & (ldo_sw << 2)) | (0x03 & (afc_r_sw >> 3)));
	a4Buf[1] =((0xE0 & (afc_r_sw << 1)) | (0x1F & (fref_div >> 9)));
	a4Buf[2] =  (0xFF & (fref_div >> 1));
	a4Buf[3] = ((0x80 & (fref_div << 7)) | (0x7F & (spi_divider)));

	a5Buf[0] =  (0xA0 | (0x10 & (rdorwt_data << 4)));
	a5Buf[1] =   0x00;
	a5Buf[2] =   0x00;
	a5Buf[3] = ((0x60 & (pfd_delay_d << 5)) | (0x10 & (pfd_delay_en << 4)) | (0x0C & (lfsr_sel << 2)) | (0x03 & (bit_sel)));



	SpiWrite( (((u32)a1Buf[0])<<24)| (((u32)a1Buf[1])<<16)|(((u32)a1Buf[2])<<8)|((u32)a1Buf[3]) );		Spi_CmdNop();
	SpiWrite( (((u32)a2Buf[0])<<24)| (((u32)a2Buf[1])<<16)|(((u32)a2Buf[2])<<8)|((u32)a2Buf[3]) );		Spi_CmdNop();
	SpiWrite( (((u32)a3Buf[0])<<24)| (((u32)a3Buf[1])<<16)|(((u32)a3Buf[2])<<8)|((u32)a3Buf[3]) );		Spi_CmdNop();
	SpiWrite( (((u32)a4Buf[0])<<24)| (((u32)a4Buf[1])<<16)|(((u32)a4Buf[2])<<8)|((u32)a4Buf[3]) );		Spi_CmdNop();
	SpiWrite( (((u32)a5Buf[0])<<24)| (((u32)a5Buf[1])<<16)|(((u32)a5Buf[2])<<8)|((u32)a5Buf[3]) );		Spi_CmdNop();
	SpiWrite( (((u32)a0Buf[0])<<24)| (((u32)a0Buf[1])<<16)|(((u32)a0Buf[2])<<8)|((u32)a0Buf[3]) );

}










