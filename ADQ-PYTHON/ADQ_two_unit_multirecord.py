import numpy as np
import ctypes as ct
import gc # gc = garbage collector
import matplotlib.pyplot as plt
# For Python under Linux
#ADQAPI = ct.cdll.LoadLibrary("libadq.so")
# For Python under Windows
ADQAPI = ct.cdll.LoadLibrary("ADQAPI.dll")

# Define convenience function
def adq_status(status):
    if (status==0):
        return 'FAILURE'
    else:
        return 'OK'

#print('ADQAPI loaded, revision {:d}.'.format(ADQAPI.ADQAPI_GetRevision()))

# Manually set return type from some ADQAPI functions
ADQAPI.CreateADQControlUnit.restype = ct.c_void_p # void pointer
ADQAPI.ADQ_GetRevision.restype = ct.c_void_p
ADQAPI.ADQ_GetPtrStream.restype = ct.POINTER(ct.c_int16)
ADQAPI.ADQControlUnit_FindDevices.argtypes = [ct.c_void_p]
ADQAPI.ADQ_GetBoardSerialNumber.restype = ct.c_char_p
ADQAPI.ADQ_GetBoardProductName.restype = ct.c_char_p

# Create a ADQ Control Unit
adq_cu = ct.c_void_p(ADQAPI.CreateADQControlUnit())

# Enable Logging for Debugging, Errors, Warnings and Info messages will be logged
ADQAPI.ADQControlUnit_EnableErrorTrace(adq_cu, 3, '.')

# Find ADQ devices
ADQAPI.ADQControlUnit_FindDevices(adq_cu)
n_of_ADQ  = ADQAPI.ADQControlUnit_NofADQ(adq_cu)
print('Number of ADQ devices found:  {}'.format(n_of_ADQ))
n_of_failed_ADQ = ADQAPI.ADQControlUnit_GetFailedDeviceCount(adq_cu)
print('Number of failed ADQ devices found:  {}'.format(n_of_failed_ADQ))

if n_of_ADQ < 2:
    print('Did not find two devices, aborting..')
else:
    for adq_num in range(1,2):
        # Get revision info from ADQ
        rev = ADQAPI.ADQ_GetRevision(adq_cu, adq_num)
        revision = ct.cast(rev, ct.POINTER(ct.c_int))
        print('\nConnected to ADQ #{:d}'.format(adq_num))
        # print('\nConnected to ADQ #%d'%(adq_num))
        # Print revision information
        print('FPGA Revision: {}'.format(revision[0]))
        if (revision[1]):
            print('Local copy')
        else:
            print('SVN Managed')
            if (revision[2]):
                print('Mixed Revision')
            else:
                print('SVN Updated')
                print('')

        # Get serial number and product name from ADQ
        serial_number = ADQAPI.ADQ_GetBoardSerialNumber(adq_cu, adq_num)
        product_name = ADQ_GetBoardProductName(adq_cu, adq_num)
        print('Board serial number: {}' .format(serial_number))
        print("Board product name:  {}\n" .format(product_name))

        # Set clock source as Internal clock source, external 10 MHz reference
        ADQ_CLOCK_INT_INTREF = 0
        ADQ_CLOCK_INT_EXTREF = 1
        ADQ_CLOCK_EXT = 2
        ADQ_CLOCK_INT_PXIREF = 3
        clock_source = ADQ_CLOCK_INT_EXTREF
        success = ADQAPI.ADQ_SetClockSource(adq_cu, adq_num, clock_source)
        if (success == 0):
            print('ADQ_SetClockSource failed.')

        ##########################
        # Test pattern
        # ADQAPI.ADQ_SetTestPatternMode(adq_cu, adq_num, 4)
        ##########################
        # Sample skip
        # ADQAPI.ADQ_SetSampleSkip(adq_cu, adq_num, 1)
        ##########################

        # Set trig mode
        SW_TRIG = 1
        EXT_TRIG = 2
        LVL_TRIG = 3
        INT_TRIG = 4
        EXT_SYNC = 9
        trigger = EXT_TRIG
        success = ADQAPI.ADQ_SetTriggerMode(adq_cu, adq_num, trigger)
        if (success == 0):
            print('ADQ_SetTriggerMode failed.')

        # Timestamp Counter Reset
        ADQAPI.ADQ_DisarmTimestampSync(adq_cu, adq_num)
        SYN_FIRST_TRG = 0
        SYN_ALL_TRG = 1
        reset_mode = SYN_ALL_TRG
        reset_ext_signal = EXT_TRIG
        ADQAPI.ADQ_SetupTimestampSync(adq_cu, adq_num, reset_mode,reset_ext_signal)
        ADQ_ArmTimestampSync(adq_cu, adq_num)

        #  Set Up Collection with MultiRecord
        number_of_records = 1
        #samples_per_record = 1000000000 - 100 # 1G Samples - 100 Samples for header(44 Bytes)
        samples_per_record = 2 ** 30 - 100  # 1G Samples - 100 Samples for header(44 Bytes)
        ADQAPI.ADQ_MultiRecordSetup(adq_cu, adq_num, number_of_records, samples_per_record)

    # Enable Triggers of two ADQ 7
    for adq_num in range(1, 2):
        ADQAPI.ADQ_DisarmTrigger(adq_cu, adq_num)
        ADQAPI.ADQ_ArmTrigger(adq_cu, adq_num)

    # Start data acquisition with a loop to control snapshots
    for snapshot_num in range(1, 2000):
        # Call the function to generate trigger signal
        # Python function to send command to the function generator to generate trigger signal

        print('\nSnapshot #{:d} starts ...'.format(adq_num))

        for adq_num in range(1,2):
            while (ADQAPI.ADQ_GetAcquiredAll(adq_cu, adq_num) == 0):
                if (trigger == SW_TRIG):
                    ADQAPI.ADQ_SWTrig(adq_cu, adq_num)
                print('ADQ #{:d}:Waiting for trigger'.format(adq_num))

            # Setup target buffers for data
            max_number_of_channels = 2
            target_buffers = (ct.POINTER(ct.c_int16 * samples_per_record * number_of_records) * max_number_of_channels)()
            for bufp in target_buffers:
                bufp.contents = (ct.c_int16 * samples_per_record * number_of_records)()

            # Transfer data from ADQ to Host
            ADQ_TRANSFER_MODE_NORMAL = 0
            ADQ_CHANNELS_MASK = 0xF

            status = ADQAPI.ADQ_GetData(adq_cu, adq_num, target_buffers,
                                        samples_per_record * number_of_records, 2,
                                        0, number_of_records, ADQ_CHANNELS_MASK,
                                        0, samples_per_record, ADQ_TRANSFER_MODE_NORMAL);
            print('ADQ_GetData returned {}'.format(adq_status(status)))

            # Re-arrange data in numpy arrays
            data_16bit_ch0 = np.frombuffer(target_buffers[0].contents[0], dtype=np.int16)
            data_16bit_ch1 = np.frombuffer(target_buffers[1].contents[0], dtype=np.int16)

            # Save data to file - To add ...

            # Free memory of target buffer
            del target_buffers
            gc.collect()


    # Only disarm trigger after all data is collected
    for adq_num in range(1, 2):
        ADQAPI.ADQ_DisarmTrigger(adq_cu, adq_num)
        ADQAPI.ADQ_MultiRecordClose(adq_cu, adq_num);

    # Delete ADQControlunit
    ADQAPI.DeleteADQControlUnit(adq_cu);

    print('Done')

# This can be used to completely unload the DLL in Windows
#ct.windll.kernel32.FreeLibrary(ADQAPI._handle)
