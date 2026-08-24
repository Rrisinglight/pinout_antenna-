/******************************************************************************
 @file  RTC6705.h
 @brief This file contains the interface to the KEY Service.
 Group:
 Target Device:
******************************************************************************/
#ifndef RTC6705_H
#define RTC6705_H

/**********************************************************************************************************
*                                                 EXTERNS
**********************************************************************************************************/
#ifdef   RTC6705_15_MODULE
#define  RTC67x5_EXT
#else
#define  RTC67x5_EXT  extern
#endif

#include "types.h"

#define	C_Bit0	0x0001
#define	C_Bit1	0x0002
#define	C_Bit2	0x0004
#define	C_Bit3	0x0008
#define	C_Bit4	0x0010
#define	C_Bit5	0x0020
#define	C_Bit6	0x0040
#define	C_Bit7	0x0080

#define	C_Bit00	0x00000001
#define	C_Bit01	0x00000002
#define	C_Bit02	0x00000004
#define	C_Bit03	0x00000008
#define	C_Bit04	0x00000010
#define	C_Bit05	0x00000020
#define	C_Bit06	0x00000040
#define	C_Bit07	0x00000080
#define	C_Bit08	0x00000100
#define	C_Bit09	0x00000200
#define	C_Bit10	0x00000400
#define	C_Bit11	0x00000800
#define	C_Bit12	0x00001000
#define	C_Bit13	0x00002000
#define	C_Bit14	0x00004000
#define	C_Bit15	0x00008000
#define	C_Bit16	0x00010000
#define	C_Bit17	0x00020000
#define	C_Bit18	0x00040000
#define	C_Bit19	0x00080000
#define	C_Bit20	0x00100000
#define	C_Bit21	0x00200000
#define	C_Bit22	0x00400000
#define	C_Bit23	0x00800000
#define	C_Bit24	0x01000000
#define	C_Bit25	0x02000000
#define	C_Bit26	0x04000000
#define	C_Bit27	0x08000000
#define	C_Bit28	0x10000000
#define	C_Bit29	0x20000000
#define	C_Bit30	0x40000000
#define	C_Bit31	0x80000000



//********************************************

//*****************************************************************************************************
// Fosc	= 8000000		( 晶振8M )
// R		= 8					( Default_6705 = 0x00190 ) -->(8000000/400)	= 20K
//									( Default_6715 = 0x00008 ) -->(8000000/8)		= 1M
// Freq = 2*(N*64+A)*(Fosc/R)		---> (N*64+A) = Freq/2*(R/Fosc)
#define		D_Fosc											0x08
#define		C_Freq_TabelOffset_Max			15


#define		D_RTC6705_SYN_RF_R_REG			0x190					// 0x190=400
#define		D_RTC6705_SYN_Define_N			(0x000361>>2)
#define		D_RTC6705_Address02_Value		(0x04C2B2>>2)

#define		D_RTC6715_SYN_RF_R_REG			0x190					// 0x190=400
#define		D_RTC6715_SYN_Define_N			(0x000361>>2)
#define		D_RTC6715_Address02_Value		(0x04C2B2>>2)
//*****************************************************************************************************


/**************************************************************************************************
*																				FUNCTIONS - Local
**************************************************************************************************/
#ifdef   RTC6705_15_MODULE
//u32		u32_TransmitData;
//u08		u8_Freq_TabelOffset;
//u08		u8_FreqGroup;

#endif

/**************************************************************************************************
*																				FUNCTIONS - Glocal
**************************************************************************************************/
#define FreqCntMax	72 	// 8, 24, 40,48, 64


RTC67x5_EXT	u08				VCO_Cap[8];										// VCO电容调整( 锁频 )
RTC67x5_EXT	u08				VGO_Pump[8];									// VGO
RTC67x5_EXT	u16 code	Tab_RTC6705Freq[FreqCntMax];	// 中频


RTC67x5_EXT	void Rtc6705_SetFreq(u08 Group, u08 ch);
RTC67x5_EXT	void Rtc6715_SetFreq(u08 Group, u08 ch);


#endif



