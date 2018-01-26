import numpy as np
import ctypes as ct
import matplotlib.pyplot as plt
import time
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

if n_of_ADQ < 2:
    print('Failed to find two devices, aborting ...')
else:
    for adq_num in range(1, n_of_ADQ+1):
        # Get revision info from ADQ
        rev = ADQAPI.ADQ_GetRevision(adq_cu, adq_num)
        revision = ct.cast(rev, ct.POINTER(ct.c_int))
        print('Connected to ADQ {}'.format(adq_num))
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

        # Set clock source
        ADQ_CLOCK_INT_INTREF = 0
        ADQ_CLOCK_INT_EXTREF = 1
        ADQ_CLOCK_EXT = 2
        ADQ_CLOCK_INT_PXIREF = 3
        clock_source = ADQ_CLOCK_INT_EXTREF  # Choose an external 10Mhz clock as the common reference
        success = ADQAPI.ADQ_SetClockSource(adq_cu, adq_num, clock_source)
        if (success == 0):
            print('ADQ_SetClockSource failed.')

        # Set trig mode
        SW_TRIG = 1
        EXT_TRIG = 2
        LVL_TRIG = 3
        INT_TRIG = 4
        EXT_SYNC = 9
        trigger = EXT_TRIG # Set as external trig
        success = ADQAPI.ADQ_SetTriggerMode(adq_cu, adq_num, trigger)
        if (success == 0):
            print('ADQ_SetTriggerMode failed.')

        # Reset timestamp counter
        SYN_ONCE = 0  # Synchronize only on the first trigger event
        SYN_EACH_TRIG = 1 # synchronize on all trigger events (until disarmed)
        syn_mode = SYN_ONCE
        trig_source = EXT_TRIG # TRIG connector as the source for timestamp counter reset
        success = ADQAPI.ADQ_DisarmTimestampSync(adq_cu, adq_num)
        success = ADQAPI.ADQ_SetupTimestampSync(adq_cu, adq_num, syn_mode, trig_source)
        success = ADQAPI.ADQ_ArmTimestampSync(adq_cu, adq_num)
        if (success == 0):
            print('ADQ_SetupTimestampSync failed.')

        # Reduce sampling rate
        # decimation_factor = 4
        # success = ADQAPI.ADQ_SetSampleSkip(adq_cu, adq_num, decimation_factor)

        number_of_records = 1
        samples_per_record = 1 * 10 ** 6

        ADQAPI.ADQ_MultiRecordSetup(adq_cu, adq_num,number_of_records,samples_per_record)

    sleep_time = 5
    print('Waiting {} seconds for external trigger to reset the timestamp counter'.format(sleep_time))
    time.sleep(sleep_time)

    num_snapshot = 31
    for snapshot in range(1,num_snapshot+1):
        print('\nStarting collection with Snapshot {}'.format(snapshot))

        # Enable trigger
        for adq_num in range(1,n_of_ADQ+1):
            ADQAPI.ADQ_DisarmTrigger(adq_cu, adq_num)
            ADQAPI.ADQ_ArmTrigger(adq_cu, adq_num)

        # Data acquisition and transfer
        for adq_num in range(1, n_of_ADQ + 1):
            while (ADQAPI.ADQ_GetAcquiredAll(adq_cu, adq_num) == 0):
                if (trigger == SW_TRIG):
                    ADQAPI.ADQ_SWTrig(adq_cu, adq_num)
                # print('Waiting for trigger')

            # Setup target buffers for data
            max_number_of_channels = ADQAPI.ADQ_GetNofChannels(adq_cu, adq_num)
            print('Number of channels:  {}'.format(max_number_of_channels))
            target_buffers = (ct.POINTER(ct.c_int16 * samples_per_record * number_of_records) * max_number_of_channels)()
            for bufp in target_buffers:
                bufp.contents = (ct.c_int16 * samples_per_record * number_of_records)()
            target_timestamps = (ct.POINTER(ct.c_ulonglong * number_of_records))()
            target_timestamps.contents = (ct.c_ulonglong * number_of_records)()

            # Get data from ADQ
            ADQ_TRANSFER_MODE_NORMAL = 0
            ADQ_CHANNELS_MASK = 0xFF
            status = ADQAPI.ADQ_GetDataWHTS(adq_cu, adq_num, target_buffers, 0, target_timestamps,
                                            samples_per_record * number_of_records , 2,
                                            0, number_of_records, ADQ_CHANNELS_MASK,
                                            0, samples_per_record, ADQ_TRANSFER_MODE_NORMAL)
            print('ADQ_GetData returned {}'.format(adq_status(status)))

            # Re-arrange data in numpy arrays
            data_16bit_ch0 = np.frombuffer(target_buffers[0].contents[0], dtype=np.int16)
            data_16bit_ch1 = np.frombuffer(target_buffers[1].contents[0], dtype=np.int16)
            tstamp_64bit_rec0 = np.frombuffer(target_timestamps.contents, dtype=np.ulonglong)
            print('ADQ {} Timestamp is {}' .format(adq_num, tstamp_64bit_rec0[0]))

            # Plot data
            # if True:
            #     plt.figure(0)
            #     plt.clf()
            #     plt.plot(data_16bit_ch0[:500], '.-')
            #     # plt.plot(data_16bit_ch1[:1000], '.--')
            #
            #     plt.figure(1)
            #     plt.clf()
            #     plt.plot(data_16bit_ch0[-500:], '.-')
            #     # plt.plot(data_16bit_ch1[-1000:],'.--')
            #
            #     plt.show()

    # Only disarm trigger after all data snapshots are collected
    ADQAPI.ADQ_DisarmTrigger(adq_cu, adq_num)
    ADQAPI.ADQ_MultiRecordClose(adq_cu, adq_num)

    # Delete ADQControlunit
    ADQAPI.DeleteADQControlUnit(adq_cu)

    print('Done')


# This can be used to completely unload the DLL in Windows
#ct.windll.kernel32.FreeLibrary(ADQAPI._handle)
