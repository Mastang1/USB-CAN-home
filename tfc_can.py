###
import time, os, sys
import random
import threading

from zlgcan import *



class TfcZlgCan(): #Basic class DevIf
    __gZCan = None
    __gDevHandle = INVALID_DEVICE_HANDLE
    __defaultConfig = {"can_dev_type":ZCAN_USBCAN2,"can_channel":0, "can_baudrate":500000,
                       "can_type":ZCAN_TYPE_CAN}

    def __init__(self, config = __defaultConfig ):
        print(config, type(config))
        self.tfcCanChanHandle = None
        self.configInfo = config
        if TfcZlgCan.__gZCan == None:
            TfcZlgCan.__gZCan = ZCAN()

        if TfcZlgCan.__gDevHandle == INVALID_DEVICE_HANDLE:
            print(config['can_dev_type'])
            TfcZlgCan.__gDevHandle = TfcZlgCan.__gZCan.OpenDevice(config['can_dev_type'], 0, 0)
            if TfcZlgCan.__gDevHandle is INVALID_DEVICE_HANDLE:
                print('Open CAN device failed.')
                exit(0)
            info = TfcZlgCan.__gZCan.GetDeviceInf(TfcZlgCan.__gDevHandle)
            print("Device Information:\n%s" %(info))
        else:
            print("Current deviece is Exist.")
        
    # 
    def open(self):
        if TfcZlgCan.__gDevHandle == INVALID_DEVICE_HANDLE:
            print('Device open error.')
            exit(0)
        
        chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
        chn_init_cfg.can_type = self.configInfo["can_type"]
        print("Configure:", chn_init_cfg.can_type)
        if chn_init_cfg.can_type == 0:
            chn_init_cfg.config.can.acc_mode = 0
            chn_init_cfg.config.can.acc_mask = 0xFFFFFFFF
            # chn_init_cfg.config.can.filter = 1
            # 3 transmit only once 2. trasmit to self  1. just listen
            chn_init_cfg.config.can.mode = 0
            # chn_init_cfg.config.can.pad = 0 

        else:
            chn_init_cfg.config.canfd.acc_mode = 0
            chn_init_cfg.config.canfd.acc_mask = 0xFFFFFFFF
            chn_init_cfg.config.canfd.brp = 0
            # chn_init_cfg.config.canfd.filter = 1
            chn_init_cfg.config.canfd.mode = 0
            # chn_init_cfg.config.canfd.pad = 0 

        self.tfcCanChanHandle = TfcZlgCan.__gZCan.InitCAN(TfcZlgCan.__gDevHandle, self.configInfo["can_channel"], chn_init_cfg)

        if self.tfcCanChanHandle is INVALID_CHANNEL_HANDLE:
            print("Channel handle is none.")
            exit(0)
        if ZCAN_STATUS_OK != self.__gZCan.StartCAN(self.tfcCanChanHandle):
            print(" CAN Open failed.")
            exit(0)
        print(" CAN Open.")

        return self.tfcCanChanHandle


    '''
    TODO: add canfd 
    rcv_can_msgs = (ZCAN_Receive_Data * rcv_num)()
    '''
    def read(self):
        rcv_num = TfcZlgCan.__gZCan.GetReceiveNum(self.tfcCanChanHandle, self.configInfo['can_type'])
        if rcv_num > 0:
            print("Receive CAN message number: %d" %rcv_num)
            rcv_msg, rcv_num = TfcZlgCan.__gZCan.Receive(self.tfcCanChanHandle, rcv_num = rcv_num)
            print(" Received data number is :", rcv_num, "Type is :", type(rcv_msg))
            dictRslt = {"num":rcv_num, "msg":rcv_msg}
            
            for i in range(rcv_num):
                print("[%d]:timestamps:%d,type:CAN, id:%s, dlc:%d, eff:%d, rtr:%d, data:%s" %(i, rcv_msg[i].timestamp, 
                      hex(rcv_msg[i].frame.can_id), rcv_msg[i].frame.can_dlc, 
                      rcv_msg[i].frame.eff, rcv_msg[i].frame.rtr,
                      ''.join(hex(rcv_msg[i].frame.data[j])+ ' 'for j in range(rcv_msg[i].frame.can_dlc))))
            return dictRslt

    def write(self):
        #Send CAN Messages
        transmit_num = 10
        msgs = (ZCAN_Transmit_Data * transmit_num)()
        for i in range(transmit_num):
            msgs[i].transmit_type = 2 #0-正常发送，2-自发自收
            msgs[i].frame.eff     = 0 #0-标准帧，1-扩展帧
            msgs[i].frame.rtr     = 0 #0-数据帧，1-远程帧
            msgs[i].frame.can_id  = i
            msgs[i].frame.can_dlc = 8
            for j in range(msgs[i].frame.can_dlc):
                msgs[i].frame.data[j] = j
        ret = TfcZlgCan.__gZCan.Transmit(self.tfcCanChanHandle, msgs, transmit_num)
        print("Tranmit Num: %d." % ret)

    def close(self):
        TfcZlgCan.__gZCan.ResetCAN(self.tfcCanChanHandle)
        print("Finish")

    def closeDev(self):
        TfcZlgCan.__gZCan.ResetCAN(self.tfcCanChanHandle)
        TfcZlgCan.__gZCan.CloseDevice(TfcZlgCan.__gDevHandle)
        print("Close device.")



def input_thread():
   input()

def testCanIf():
    thread=threading.Thread(target=input_thread)
    thread.start()

    myCanConfig = {"can_dev_type":ZCAN_USBCAN2,"can_channel":0, "can_baudrate":500000,
                       "can_type":ZCAN_TYPE_CANFD}
    myCan = TfcZlgCan()
    myCan.open()
    myCan.write()
    while True:
        rslt = myCan.read()
        if rslt['num']:
            print("Result is : ", rslt)
            break
        
        if thread.is_alive() == False:
            break
    
    myCan.closeDev()


if __name__ == '__main__':
    testCanIf()
