import numpy as np
import ctypes as ct
import matplotlib.pyplot as plt
# For Python under Linux
#ADQAPI = ct.cdll.LoadLibrary("libadq.so")
# For Python under Windows
ADQAPI = ct.cdll.LoadLibrary("ADQAPI.dll")
ADQAPI.ADQAPI_GetRevision()

# Manually set return type from some ADQAPI functions
ADQAPI.CreateADQControlUnit.restype = ct.c_void_p
ADQAPI.ADQ_GetRevision.restype = ct.c_void_p
ADQAPI.ADQ_GetPtrStream.restype = ct.POINTER(ct.c_int16)
ADQAPI.ADQControlUnit_FindDevices.argtypes = [ct.c_void_p]

# Create ADQControlUnit
adq_cu = ct.c_void_p(ADQAPI.CreateADQControlUnit())
ADQAPI.ADQControlUnit_EnableErrorTrace(adq_cu, 3, '.')
adq_num = 1

# Convenience function
def adq_status(status):
    if (status==0):
        return 'FAILURE'
    else:
        return 'OK'  

# Find ADQ devices
ADQAPI.ADQControlUnit_FindDevices(adq_cu)
n_of_ADQ  = ADQAPI.ADQControlUnit_NofADQ(adq_cu)
print('Number of ADQ found:  {}'.format(n_of_ADQ))

if n_of_ADQ > 0:
    # Get revision info from ADQ
    rev = ADQAPI.ADQ_GetRevision(adq_cu, adq_num)
    revision = ct.cast(rev,ct.POINTER(ct.c_int))
    print('\nConnected to ADQ #1')
    # Print revision information
    print('FPGA Revision: {}'.format(revision[0]))
    if (revision[1]):
        print('Local copy')
    else :
        print('SVN Managed')
        if (revision[2]):
            print('Mixed Revision')
        else :
            print('SVN Updated')
            print('')

    # Set clock source
    ADQ_CLOCK_INT_INTREF = 0
    ADQ_CLOCK_INT_EXTREF = 1
    ADQ_CLOCK_EXT = 2
    ADQ_CLOCK_INT_PXIREF = 3
    # clock_source = ADQ_CLOCK_INT_EXTREF
    clock_source = ADQ_CLOCK_INT_INTREF
    success = ADQAPI.ADQ_SetClockSource(adq_cu, adq_num, clock_source)
    if (success == 0):
        print('ADQ_SetClockSource failed.')

    ##########################
    # Test pattern
    #ADQAPI.ADQ_SetTestPatternMode(adq_cu, adq_num, 4)
    ##########################
    # Sample skip
    #ADQAPI.ADQ_SetSampleSkip(adq_cu, adq_num, 1)
    ##########################

    # Set trig mode
    SW_TRIG = 1
    EXT_TRIG = 2
    LVL_TRIG = 3
    INT_TRIG = 4
    EXT_SYNC = 9
    # trigger = EXT_TRIG
    trigger = SW_TRIG
    success = ADQAPI.ADQ_SetTriggerMode(adq_cu, adq_num, trigger)
    if (success == 0):
        print('ADQ_SetTriggerMode failed.')

    #ADQAPI.ADQ_SetSampleSkip(adq_cu, adq_num, 4)

    number_of_records = 1
    samples_per_record = 1 * 10**6
        
    # Start acquisition
    ADQAPI.ADQ_MultiRecordSetup(adq_cu, adq_num,
                                number_of_records,
                                samples_per_record)
    ADQAPI.ADQ_DisarmTrigger(adq_cu, adq_num)
    ADQAPI.ADQ_ArmTrigger(adq_cu, adq_num)
    
    while(ADQAPI.ADQ_GetAcquiredAll(adq_cu,adq_num) == 0):
        if (trigger == SW_TRIG):
            ADQAPI.ADQ_SWTrig(adq_cu, adq_num)
        print('Waiting for trigger')

    # Setup target buffers for data
    max_number_of_channels = ADQAPI.ADQ_GetNofChannels(adq_cu, adq_num)
    print('Number of channels:  {}'.format(max_number_of_channels))
    target_buffers=(ct.POINTER(ct.c_int16*samples_per_record*number_of_records)*max_number_of_channels)()
    for bufp in target_buffers:
        bufp.contents = (ct.c_int16*samples_per_record*number_of_records)()
    target_timestamps = (ct.POINTER(ct.c_ulonglong)*number_of_records)()
    for tstampp in target_timestamps:
        tstampp.contents = (ct.c_ulonglong)()


    # Get data from ADQ
    ADQ_TRANSFER_MODE_NORMAL = 0
    ADQ_CHANNELS_MASK = 0xFF
    status = ADQAPI.ADQ_GetDataWHTS(adq_cu, adq_num, target_buffers,0,target_timestamps,
                                samples_per_record*number_of_records, 2,
                                0, number_of_records, ADQ_CHANNELS_MASK,
                                0, samples_per_record, ADQ_TRANSFER_MODE_NORMAL);
    print('ADQ_GetData returned {}'.format(adq_status(status)))

    # Re-arrange data in numpy arrays
    data_16bit_ch0 = np.frombuffer(target_buffers[0].contents[0],dtype=np.int16)
    print('Data length ch0 is {}'.format(len(data_16bit_ch0)))
    data_16bit_ch1 = np.frombuffer(target_buffers[1].contents[0],dtype=np.int16)
    print('Data length ch1 is {}'.format(len(data_16bit_ch1)))
    # data_16bit_ch2 = np.frombuffer(target_buffers[2].contents[0],dtype=np.int16)
    # data_16bit_ch3 = np.frombuffer(target_buffers[3].contents[0],dtype=np.int16)
    tstamp_64bit_rec0 = np.frombuffer(target_timestamps[0].contents[0],dtype=np.ulonglong)
    print('Timestamp is {}'.format(tstamp_64bit_rec0))

    # Plot data
    if True:
        plt.figure(0)
        plt.clf()
        plt.plot(data_16bit_ch0[:500], '.-')
        #plt.plot(data_16bit_ch1[:1000], '.--')

        plt.figure(1)
        plt.clf()
        plt.plot(data_16bit_ch0[-500:],'.-')
        #plt.plot(data_16bit_ch1[-1000:],'.--')

        
        plt.show()

    # Only disarm trigger after data is collected
    ADQAPI.ADQ_DisarmTrigger(adq_cu, adq_num)
    ADQAPI.ADQ_MultiRecordClose(adq_cu, adq_num);

    # Delete ADQControlunit
    ADQAPI.DeleteADQControlUnit(adq_cu);

    print('Done')

else:
    print('No ADQ connected.')

# This can be used to completely unload the DLL in Windows
#ct.windll.kernel32.FreeLibrary(ADQAPI._handle)
