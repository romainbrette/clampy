//***********************************************************************************************
//
//    Copyright (c) 1998 Axon Instruments.
//    All rights reserved.
//
//***********************************************************************************************
// MODULE:  AXDD132X.HPP
// PURPOSE: Interface definition for AXDD132X.DLL
// AUTHOR:  BHI  Aug 1998
//

#ifndef INC_AXDD132X_HPP
#define INC_AXDD132X_HPP

#if _MSC_VER >= 1000
#pragma once
#endif // _MSC_VER >= 1000

#pragma pack(push,1)

const int DD132X_MAXAICHANNELS = 16;
const int DD132X_MAXAOCHANNELS = 16;
const int DD132X_SCANLIST_SIZE = 64;

struct DD132X_Info
{
   UINT uLength;
   BYTE byAdaptor;
   BYTE byTarget;
   BYTE byImageType;
   BYTE byResetType;
   char szManufacturer[16];
   char szName[32];
   char szProductVersion[8];
   char szFirmwareVersion[16];
   UINT uInputBufferSize;
   UINT uOutputBufferSize;
   UINT uSerialNumber;
   UINT uClockResolution;
   UINT uMinClockTicks;
   UINT uMaxClockTicks;
   BYTE byUnused[280];

   DD132X_Info() 
   {
      memset( this, 0, sizeof(*this));
      uLength   = sizeof(*this);
      byAdaptor = BYTE(-1);
      byTarget  = BYTE(-1);
   }
};

//========================================================================================
// Constants for the protocol.

// Values used in the dwFlags field
#define DD132X_PROTOCOL_STOPONTC          0x00000001

// DD1320 special cases for Analog output sequence.
#define DD132X_PROTOCOL_DIGITALOUTPUT     0x0040
#define DD132X_PROTOCOL_NULLOUTPUT        0x0050

enum DD132X_Triggering
{
   DD132X_StartImmediately,
   DD132X_ExternalStart,
   DD132X_LineTrigger,
};

enum DD132X_AIDataBits
{
   DD132X_Bit0Data,
   DD132X_Bit0ExtStart,
   DD132X_Bit0Line,
   DD132X_Bit0Tag,
   DD132X_Bit0Tag_Bit1ExtStart,
   DD132X_Bit0Tag_Bit1Line,
};

enum DD132X_OutputPulseType
{
   DD132X_NoOutputPulse,
   DD132X_ADC_level_Triggered,
   DD132X_DAC_bit0_Triggered,
};

//==============================================================================================
// STRUCTURE: DD132X_Protocol
// PURPOSE:   Describes acquisition settings.
//
struct DD132X_Protocol
{
   UINT                    uLength;             // Size of this structure in bytes.
   double                  dSampleInterval;     // Sample interval in us.
   DWORD                   dwFlags;             // Boolean flags that control options.
   DD132X_Triggering       eTriggering;
   DD132X_AIDataBits       eAIDataBits;

   UINT                    uAIChannels;
   int                     anAIChannels[DD132X_SCANLIST_SIZE];
   DATABUFFER             *pAIBuffers;
   UINT                    uAIBuffers;

   UINT                    uAOChannels;
   int                     anAOChannels[DD132X_SCANLIST_SIZE];
   DATABUFFER             *pAOBuffers;
   UINT                    uAOBuffers;

   LONGLONG                uTerminalCount;

   DD132X_OutputPulseType  eOutputPulseType;
   short                   bOutputPulsePolarity;   // TRUE = positive.
   short                   nOutputPulseChannel;
   WORD                    wOutputPulseThreshold;
   WORD                    wOutputPulseHystDelta;

   UINT                    uChunksPerSecond;
   BYTE                    byUnused[248];

   DD132X_Protocol()
   {
      memset(this, 0, sizeof(*this));
      uLength          = sizeof(*this);
      uChunksPerSecond = 20;
   }
};

//==============================================================================================
// STRUCTURE: DD132X_PowerOnData
// PURPOSE:   Contains items that are set in the EEPROM of the DD1320 as power-on defaults.
//
struct DD132X_PowerOnData
{
   UINT  uLength;
   DWORD dwDigitalOuts;
   short anAnalogOuts[DD132X_MAXAOCHANNELS];

   DD132X_PowerOnData()
   {
      memset(this, 0, sizeof(*this));
      uLength = sizeof(*this);
   }
};

// constants for the uEquipmentStatus field.
const UINT DD132X_STATUS_TERMINATOR      = 0x00000001;
const UINT DD132X_STATUS_DRAM            = 0x00000002;
const UINT DD132X_STATUS_EEPROM          = 0x00000004;
const UINT DD132X_STATUS_INSCANLIST      = 0x00000008;
const UINT DD132X_STATUS_OUTSCANLIST     = 0x00000010;
const UINT DD132X_STATUS_CALIBRATION_MUX = 0x00000020;
const UINT DD132X_STATUS_INPUT_FIFO      = 0x00000040;
const UINT DD132X_STATUS_OUTPUT_FIFO     = 0x00000080;
const UINT DD132X_STATUS_LINEFREQ_GEN    = 0x00000100;
const UINT DD132X_STATUS_FPGA            = 0x00000200;
const UINT DD132X_STATUS_ADC0            = 0x00000400;
const UINT DD132X_STATUS_DAC0            = 0x00000800;
const UINT DD132X_STATUS_DAC1            = 0x00001000;
const UINT DD132X_STATUS_DAC2            = 0x00002000;
const UINT DD132X_STATUS_DAC3            = 0x00003000;
const UINT DD132X_STATUS_DAC4            = 0x00004000;
const UINT DD132X_STATUS_DAC5            = 0x00010000;
const UINT DD132X_STATUS_DAC6            = 0x00020000;
const UINT DD132X_STATUS_DAC7            = 0x00040000;
const UINT DD132X_STATUS_DAC8            = 0x00080000;
const UINT DD132X_STATUS_DAC9            = 0x00100000;
const UINT DD132X_STATUS_DACA            = 0x00200000;
const UINT DD132X_STATUS_DACB            = 0x00400000;
const UINT DD132X_STATUS_DACC            = 0x00800000;
const UINT DD132X_STATUS_DACD            = 0x01000000;
const UINT DD132X_STATUS_DACE            = 0x02000000;
const UINT DD132X_STATUS_DACF            = 0x04000000;

//==============================================================================================
// STRUCTURE: Diagnostic data
// PURPOSE:   Configuration data returned through DriverLINX.
// NOTE:      The size of diagnostic data must be even.
//
struct DD132X_CalibrationData
{
   UINT   uLength;            // Size of this structure in bytes.
   UINT   uEquipmentStatus;   // Bit mask of equipment status flags.
   double dADCGainRatio;      // ADC 0 gain-ratio
   short  nADCOffset;         // ADC 0  zero offset
   BYTE   byUnused1[46];      // Unused space for more ADCs

   WORD   wNumberOfDACs;      // total number of DACs on board
   BYTE   byUnused2[6];       // Alignment bytes.
   short  anDACOffset[DD132X_MAXAOCHANNELS];       // DAC 0 zero offset
   double adDACGainRatio[DD132X_MAXAOCHANNELS];    // DAC 0 gain-ratio
   BYTE   byUnused4[24];

   DD132X_CalibrationData()
   {
      memset(this, 0, sizeof(*this));
      uLength = sizeof(*this);
   }
};

//==============================================================================================
// STRUCTURE: Start acquisition info.
// PURPOSE:   To store the start acquisition time and precission,
//            by querying a high resolution timer before and after
//            the start acquisition SCSI command.
//
struct DD132X_StartAcqInfo
{
   UINT                     uLength;            // Size of this structure in bytes.
   SYSTEMTIME               m_StartTime;        // Stores the time and date of the begginning of the acquisition. 
   __int64                  m_n64PreStartAcq;   // Stores the high resolution counter before the acquisition start.
   __int64                  m_n64PostStartAcq;  // Stores the high resolution counter after the acquisition start.

   DD132X_StartAcqInfo()
   {
      memset(this, 0, sizeof(*this));
      uLength = sizeof(*this);
   }
};

#pragma pack(pop)

// constants for SetDebugMsgLevel()
const int DD132X_MSG_SHOWALL  = 0;
const int DD132X_MSG_SHOWLESS = 1;
const int DD132X_MSG_SHOWNONE = 2;

// The handle type declaration.
DECLARE_HANDLE(HDD132X);

// Find, Open & close device.
BOOL    WINAPI DD132X_RescanSCSIBus(int *pnError);
UINT    WINAPI DD132X_FindDevices(DD132X_Info *pInfo, UINT uMaxDevices, int *pnError);
HDD132X WINAPI DD132X_OpenDevice(BYTE byAdaptor, BYTE byTarget, int *pnError);
HDD132X WINAPI DD132X_OpenDeviceEx(BYTE byAdaptor, BYTE byTarget, const BYTE *pRamware,
                                   UINT uImageSize, int *pnError);
BOOL    WINAPI DD132X_CloseDevice(HDD132X hDevice, int *pnError);
BOOL    WINAPI DD132X_GetDeviceInfo(HDD132X hDevice, DD132X_Info *pInfo, int *pnError);

BOOL    WINAPI DD132X_Reset(HDD132X hDevice, int *pnError);
BOOL    WINAPI DD132X_DownloadRAMware(HDD132X hDevice, const BYTE *pRAMware, UINT uImageSize, int *pnError);

// Get/set acquisition protocol information.   
BOOL    WINAPI DD132X_SetProtocol(HDD132X hDevice, const DD132X_Protocol *pProtocol, int *pnError);
BOOL    WINAPI DD132X_GetProtocol(HDD132X hDevice, DD132X_Protocol *pProtocol, int *pnError);

// Start/stop acquisition.
BOOL    WINAPI DD132X_StartAcquisition(HDD132X hDevice, int *pnError);
BOOL    WINAPI DD132X_StopAcquisition(HDD132X hDevice, int *pnError);
BOOL    WINAPI DD132X_PauseAcquisition(HDD132X hDevice, BOOL bPause, int *pnError);
BOOL    WINAPI DD132X_IsAcquiring(HDD132X hDevice);
BOOL    WINAPI DD132X_IsPaused(HDD132X hDevice);
BOOL    WINAPI DD132X_GetTimeAtStartOfAcquisition( HDD132X hDevice, DD132X_StartAcqInfo *pStartAcqInfo );

// Start/read ReadLast acquisition.
BOOL    WINAPI DD132X_StartReadLast(HDD132X hDevice, int *pnError);
BOOL    WINAPI DD132X_ReadLast(HDD132X hDevice, ADC_VALUE *pnBuffer, UINT uNumSamples, int *pnError);

// Monitor progress of the acquisition.
BOOL    WINAPI DD132X_GetAcquisitionPosition(HDD132X hDevice, LONGLONG *puSampleCount, int *pnError);
BOOL    WINAPI DD132X_GetNumSamplesOutput(HDD132X hDevice, LONGLONG *puSampleCount, int *pnError);

// Single read/write operations.
BOOL    WINAPI DD132X_GetAIValue(HDD132X hDevice, UINT uChannel, short *pnValue, int *pnError);
BOOL    WINAPI DD132X_GetDIValues(HDD132X hDevice, DWORD *pdwValues, int *pnError);
BOOL    WINAPI DD132X_PutAOValue(HDD132X hDevice, UINT uChannel, short nValue, int *pnError);
BOOL    WINAPI DD132X_PutDOValues(HDD132X hDevice, DWORD dwValues, int *pnError);
BOOL    WINAPI DD132X_GetTelegraphs(HDD132X hDevice, UINT uFirstChannel, short *pnValue, UINT uValues, int *pnError);

// Calibration & EEPROM interraction.
BOOL    WINAPI DD132X_SetPowerOnOutputs(HDD132X hDevice, const DD132X_PowerOnData *pPowerOnData, int *pnError);
BOOL    WINAPI DD132X_GetPowerOnOutputs(HDD132X hDevice, DD132X_PowerOnData *pPowerOnData, int *pnError);

BOOL    WINAPI DD132X_Calibrate(HDD132X hDevice, DD132X_CalibrationData *pCalibrationData, int *pnError);
BOOL    WINAPI DD132X_GetCalibrationData(HDD132X hDevice, DD132X_CalibrationData *pCalibrationData, int *pnError);
BOOL    WINAPI DD132X_GetScsiTermStatus(HDD132X hDevice, BYTE *pbyStatus, int *pnError);

BOOL    WINAPI DD132X_DTermRead(HDD132X hDevice, LPSTR pszBuf, UINT uMaxLen,  int *pnError);
BOOL    WINAPI DD132X_DTermWrite(HDD132X hDevice, LPCSTR pszBuf, int *pnError);
BOOL    WINAPI DD132X_DTermSetBaudRate(HDD132X hDevice, UINT uBaudRate, int *pnError);

// Diagnostic functions.
BOOL    WINAPI DD132X_GetLastErrorText(HDD132X hDevice, char *pszMsg, UINT uMsgLen, int *pnError);
BOOL    WINAPI DD132X_SetDebugMsgLevel(HDD132X hDevice, UINT uLevel, int *pnError);

// Setup threshold level.
BOOL    WINAPI DD132X_UpdateThresholdLevel( HDD132X hDevice, const WORD *pwOutputPulseThreshold, const WORD *pwOutputPulseHystDelta );

// Error codes
const int DD132X_ERROR_ASPINOTFOUND  = 1;
const int DD132X_ERROR_OUTOFMEMORY   = 2;
const int DD132X_ERROR_NOTDD132X     = 3;
const int DD132X_ERROR_RAMWAREOPEN   = 4;
const int DD132X_ERROR_RAMWAREREAD   = 5;
const int DD132X_ERROR_RAMWAREWRITE  = 6;
const int DD132X_ERROR_RAMWARESTART  = 7;
const int DD132X_ERROR_SETAIPROTOCOL = 8;
const int DD132X_ERROR_SETAOPROTOCOL = 9;
const int DD132X_ERROR_STARTACQ      = 10;
const int DD132X_ERROR_STOPACQ       = 11;
const int DD132X_ERROR_PAUSEACQ      = 12;
const int DD132X_ERROR_READDATA      = 13;
const int DD132X_ERROR_WRITEDATA     = 14;
const int DD132X_ERROR_CALIBRATION   = 15;
const int DD132X_ERROR_DIAGNOSTICS   = 16;
const int DD132X_ERROR_DTERM_READ    = 17;
const int DD132X_ERROR_DTERM_WRITE   = 18;
const int DD132X_ERROR_DTERM_BUSY    = 19;
const int DD132X_ERROR_DTERM_SETBAUD = 20;

const int DD132X_ERROR_ASPIERROR     = 1000;

// Internal error numbers.
const int DD132X_ERROR_CANTCOMPLETE  = 9999;

#endif      // INC_AXDD132X_HPP

