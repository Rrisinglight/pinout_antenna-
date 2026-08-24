/******************************************************************************
 @file  RTC6705_15.c
 @brief This file contains the interface to the HAL KEY Service.
 Group:
 Target Device:
******************************************************************************/
#define RTC6705_15_MODULE

#include "N76E003.h"
#include "SFR_Macro.h"
#include "Function_define.h"
#include "bsp.h"
#include "process.h"
#include "flash.h"
#include "RTC6705_15.h"
#include "cSystem.h"
#include "tramp.h"


#define S_SPI_CLK_L()		st( P15_SPI_CLK	= 0;	)
#define S_SPI_CLK_H()		st( P15_SPI_CLK	= 1;	)
#define S_SPI_DATA_L()	st( P11_SPI_DATA	= 0;	)
#define S_SPI_DATA_H()	st( P11_SPI_DATA	= 1;	)
#define S_SPI_LE_L()		st( P10_PLCC_LE		= 0;	)
#define S_SPI_LE_H()		st( P10_PLCC_LE		= 1;	)

#define	A_SPI_LE(n)			(n ? ( P16_v_ATT_LE	=1)		: ( P16_v_ATT_LE	=0))
	#define	A_SPI_CLK(n)		(n ? ( P15_SPI_CLK		=1)	: ( P15_SPI_CLK			=0))
	#define	A_SPI_DATA(n)		(n ? ( P11_SPI_DATA		=1)	: ( P11_SPI_DATA		=0))


u08	VCO_Cap[8]		= { 0x03,	0x02,	0x02,	0x01,	0x01,	0x00,	0x00,	0x00,		};	// VCO电容调整( 锁频 )
u08	VGO_Pump[8]		=	{ 0x01,	0x01,	0x01,	0x01,	0x01,	0x01,	0x01,	0x01,		};	// VGO

#if FreqCntMax == 8
u16 code Tab_RTC6705Freq[8] =		// ( 4990-5450 )
{// 1			2			3			4			5			6			7			8
	4990,	5020,	5050,	5080,	5110,	5140,	5170,	5200,
};
#elif FreqCntMax == 56
u16 code Tab_RTC6705Freq[56] =		// ( 5325-5945 )
{// 1			2			3			4			5			6			7			8
	5865, 5845, 5825, 5805, 5785, 5765, 5745, 5725,		// A
	5733, 5752, 5771, 5790, 5809, 5828, 5847, 5866,		// B
	5705, 5685, 5665, 5645, 5885, 5905, 5925, 5945,		// C
	5740, 5760, 5780, 5800, 5820, 5840, 5860, 5880,		// D
	5658, 5695, 5732, 5769, 5806, 5843, 5880, 5917,		// E
	5362, 5399, 5436, 5473, 5510, 5547, 5584, 5621,		// F
	4990, 5020, 5050, 5080, 5110, 5140, 5170, 5200,
};
#elif FreqCntMax == 72
u16 code Tab_RTC6705Freq[72] =		// ( 4990-5450 )
{// 1			2			3			4			5			6			7			8
	5865, 5845, 5825, 5805, 5785, 5765, 5745, 5725,		// A
	5733, 5752, 5771, 5790, 5809, 5828, 5847, 5866,		// B
	5705, 5685, 5665, 5645, 5885, 5905, 5925, 5945,		// E
	5740, 5760, 5780, 5800, 5820, 5840, 5860, 5880,		// F
	5658, 5695, 5732, 5769, 5806, 5843, 5880, 5917,		// R
	5362, 5399, 5436, 5473, 5510, 5547, 5584, 5621,		// L
	5325, 5348, 5366, 5384, 5402, 5420, 5438, 5456,		// X1
	5474, 5492, 5510, 5528, 5546, 5564, 5582, 5600,		// X2
	5653, 5693, 5733, 5773, 5813, 5853, 5893, 5933,		// X3
};

#endif



/*******************************************************************************
函 数 名:	Spi_Nop
功    能:
作    者:
日    期:	2011-05-09
*******************************************************************************/
void Spi_Nop(void)
{
	u08 u8_Temp=10;
	while(u8_Temp)	{ u8_Temp--;	}
}

/*******************************************************************************
函 数 名:	SpiWrite
功    能:
作    者:
日    期:	2011-05-09
*******************************************************************************/
void SpiWrite(u32 u32_SPI_Data)
{
	u08		u8_SPI_Bitx		= 25;
	u32		u32_Data			= u32_SPI_Data;

//S_SPI_Mode();
	Spi_Nop();
	S_SPI_CLK_L();	Spi_Nop();
	S_SPI_LE_L();		Spi_Nop();
	while(u8_SPI_Bitx!=0)
	{
		Spi_Nop();
		if((u32_Data&C_Bit00)==0)	{ S_SPI_DATA_L();	}
		else											{ S_SPI_DATA_H();	}
		Spi_Nop();

		S_SPI_CLK_H();	Spi_Nop();	Spi_Nop();
		S_SPI_CLK_L();
		u32_Data = u32_Data>>1;
		u8_SPI_Bitx--;
	}
	Spi_Nop();
	S_SPI_LE_H();	Spi_Nop();
}

#if 0
/*******************************************************************************
函 数 名:	SpiRead
功    能:
作    者:
日    期:	2011-05-09
*******************************************************************************/
u32 SpiRead(u08 u8_SPI_Addr)
{
	u08		u8_SPI_Bitx		= 0x00;
	u08		u8_Addr				= u8_SPI_Addr;
	u32		u32_SPI_Data	= (u32)u8_Addr;

	u32_SPI_Data |= C_Bit04;
	u32_SPI_Data <<= 27;
	u32_SPI_Data &= 0xF8000000;
	u8_Addr &= 0x0F;
	S_SPI_Mode();		Spi_Nop();
	S_SPI_CLK_L();	Spi_Nop();
	S_SPI_LE_L();		Spi_Nop();
	u8_SPI_Bitx = 0x05;
	while(u8_SPI_Bitx!=0)
	{
		if((u8_Addr&0x01)==0)		{ S_SPI_DATA_L();	}
		else										{ S_SPI_DATA_H();	}
		Spi_Nop();

		S_SPI_CLK_H();	Spi_Nop();
		S_SPI_CLK_L();	Spi_Nop();
		u8_Addr >>= 1;
		u8_SPI_Bitx--;
	}

	S_SPI_DATA_InputStatus();
	Spi_Nop();
	u8_SPI_Bitx = 20;
	while(u8_SPI_Bitx!=0)
	{
		u32_SPI_Data >>= 1;
		if((P_SPI_DATA_In&b_SPI_DATA)!=0)	{ u32_SPI_Data |= C_Bit31;	}
		else															{ u32_SPI_Data &= ~C_Bit31;	}
		Spi_Nop();
		S_SPI_CLK_H();	Spi_Nop();
		S_SPI_CLK_L();	Spi_Nop();
		u8_SPI_Bitx--;
	}
	S_SPI_DATA_OutputStatus();
	u32_SPI_Data >>= 7;
	u32_SPI_Data &= 0x01FFFFFF;
	S_SPI_LE_H();		Spi_Nop();
	return(u32_SPI_Data);
}
#endif

/*******************************************************************************
函 数 名:	Rtc6705_Write
功    能:
作    者:
日    期:	2011-05-09
*******************************************************************************/
void Rtc6705_Write(u08 u8_Addr, u32 u32_Value)
{
	u08 u8_Loop = 8;
	u32 u32_Data = (u32)((u8_Addr&0x0F)|C_Bit4)&0x0000001F;
	u32_Data |= ((u32_Value<<5)&0x01FFFFE0);
	SpiWrite(u32_Data);
}

/*******************************************************************************
函 数 名:	Rtc6705_SetFreq
功    能:
作    者:
日    期:	2011-05-09
*******************************************************************************/
void Rtc6705_SetFreq(u08 Group,u08 ch)
{
	u08 temp;
	u32 u32_RegN, u32_RegA;
	u32 u32_Freq;

	Rtc6705_Write(0x00,D_RTC6705_SYN_RF_R_REG);		// 8M/400 = 20K
	Rtc6705_Write(0x0F,0x000000);
	temp			=	(Group-1)*8+(ch-1);
	u32_Freq	= (u32)Tab_RTC6705Freq[temp];

	u32_RegN = ((((u32_Freq*D_RTC6705_SYN_RF_R_REG)/D_Fosc)/2)/64);
	u32_RegA = ((((u32_Freq*D_RTC6705_SYN_RF_R_REG)/D_Fosc)/2)%64);
	u32_Freq = (u32_RegN<<7) | (u32_RegA&0x7F);
	Rtc6705_Write(0x01,u32_Freq);

}

#if 0
/*******************************************************************************
函 数 名:	Rtc6715_Write
功    能:
作    者:
日    期:	2011-05-09
*******************************************************************************/
void Rtc6715_Write(u08 u8_Addr, u32 u32_Value)
{
	u08 u8_Loop = 8;
	u32 u32_Data = (u32)((u8_Addr&0x0F)|C_Bit4)&0x0000001F;
	u32_Data |= ((u32_Value<<5)&0x01FFFFE0);
	SpiWrite(u32_Data);
}
#endif

#if 0
/*******************************************************************************
函 数 名:	Rtc6705_SetFreq
功    能:
作    者:
日    期:	2011-05-09
*******************************************************************************/
void Rtc6715_SetFreq(u08 Group,u08 ch)
{
	u08 temp;
	u32 u32_RegN, u32_RegA;
	u32 u32_Freq;

	Rtc6715_Write(0x00,D_RTC6715_SYN_RF_R_REG); 	// 8M/400 = 20K
	Rtc6715_Write(0x0F,0x000000);
	temp			= (Group-1)*8+(ch-1);
//u32_Freq	= (u32)Tab_RTC6715Freq[temp];

	u32_RegN = ((((u32_Freq*D_RTC6715_SYN_RF_R_REG)/D_Fosc)/2)/64);
	u32_RegA = ((((u32_Freq*D_RTC6715_SYN_RF_R_REG)/D_Fosc)/2)%64);
	u32_Freq = (u32_RegN<<7) | (u32_RegA&0x7F);
	Rtc6705_Write(0x01,u32_Freq);

}
#endif

#if 0
//==================================================================
void F_RTC6715_WriteTabelFreqUart(u08 u8_TabelOffset)
{
	u32 u32_Temp0;
	u32 u32_Temp	= (u32)Tab_RTC6715FreqUart[u8_TabelOffset];
	u32_Temp			>>= 1;
	u32_Temp0			= u32_Temp;
	u32_Temp			= ((u32_Temp<<2)&0XFFF80)|(u32_Temp0&0X0000001F);
	F_RTC6715_Write(0X01,u32_Temp);
}
#endif

#if 0
//==================================================================
void F_RTC6715_WriteTabelFreq(u08 u8_TabelOffset)
{
//R = 400
	u32 Temp0,Temp1,Temp2,Temp3;

	u32 u32_Temp	= (u32)Tab_RTC6715Freq[u8_TabelOffset];
	Temp0					= (u32_Temp<<4)+(u32_Temp<<3)+u32_Temp;	//Temp0 = u32_Temp*25;
	Temp1					= Temp0>>5;    													//N = Temp0/32
	Temp2					= Temp0&0X1F;    												//A = Temp0%32
	Temp3					= (Temp1<<7)|Temp2;
	F_RTC6715_Write(0X00,400);
	F_RTC6715_Write(0X01,Temp3);
}*/
#endif

#if 0
//==================================================================
void F_RTC6705_6715_Reset(void)
{
	D_SetRTC6705_6715_Addr0F();
	u16_RTC6705_6715_TransmitDelay = C_RTC6705_6715_Reset_DelayValue;
	u8_Freq_TabelOffset = 0x00;
}
#endif








