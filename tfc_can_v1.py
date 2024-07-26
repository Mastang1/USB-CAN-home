###
import time, os, sys,string
import random
import threading

if __name__ == '__main__':
    from zlgcan import *
else:
    from .zlgcan import *


class TfcZlgCan(): #Basic class DevIf
    __gDevHandle = INVALID_DEVICE_HANDLE
    __defaultConfig = {"can_dev_type":ZCAN_USBCAN2,"can_channel":0, "can_baudrate":500000,
                       "can_type":ZCAN_TYPE_CAN, "test_frame_id":0x100, "receive_timeout_s":5}

    def __init__(self, config = __defaultConfig ):
        
        print(config, type(config))
        self.tfcCanChanHandle = None
        self.configInfo = config
        self.rcvTimeout = config['receive_timeout_s']


        self.zcanLib = ZCAN()

        if TfcZlgCan.__gDevHandle == INVALID_DEVICE_HANDLE:
            print(config['can_dev_type'])
            TfcZlgCan.__gDevHandle = self.zcanLib.OpenDevice(config['can_dev_type'], 0, 0)
            if TfcZlgCan.__gDevHandle is INVALID_DEVICE_HANDLE:
                print('Open CAN device failed.')
                exit(0)
            info = self.zcanLib.GetDeviceInf(TfcZlgCan.__gDevHandle)
            print("Device Information:\n%s" %(info))
        else:
            print("Current deviece is Exist.")
        
    # 
    def open(self):
        self.tmpRslt = None
        if TfcZlgCan.__gDevHandle == INVALID_DEVICE_HANDLE:
            print('Device open error.')
            exit(0)
        
        # Some config information
        ip = self.zcanLib.GetIProperty(TfcZlgCan.__gDevHandle)

        ret = self.zcanLib.SetValue(ip, str(self.configInfo['can_channel']) + "/canfd_standard", "0")
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d CANFD standard failed!" %(self.configInfo['can_channel']))
            exit(0)

        ret = self.zcanLib.SetValue(ip,str(self.configInfo['can_channel'])+"/canfd_abit_baud_rate","500000")  #设置波特率
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d baud failed!" %(self.configInfo['can_channel']))      
            exit(0)

        ret = self.zcanLib.SetValue(ip,str(self.configInfo['can_channel'])+"/canfd_dbit_baud_rate","500000")
        if ret != ZCAN_STATUS_OK:
            print("Set CH%d baud failed!" %(self.configInfo['can_channel']))      
            exit(0)
        
        # Config and initialization
        chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
        chn_init_cfg.can_type = self.configInfo["can_type"]
        print("Configure can channel type is :", chn_init_cfg.can_type)
        if chn_init_cfg.can_type == 0:
            chn_init_cfg.config.can.acc_mode = 0
            chn_init_cfg.config.can.acc_mask = 0xFFFFFFFF
            # chn_init_cfg.config.can.filter = 1
            # 3 transmit only once 2. trasmit to self  1. just listen
            chn_init_cfg.config.can.mode = 0
            # chn_init_cfg.config.can.pad = 0 

        else:
            # chn_init_cfg.config.canfd.acc_mode = 0
            # chn_init_cfg.config.canfd.acc_mask = 0xFFFFFFFF
            # chn_init_cfg.config.canfd.brp = 0
            # chn_init_cfg.config.canfd.filter = 1
            chn_init_cfg.config.canfd.mode = 0
            # chn_init_cfg.config.canfd.pad = 0 

        self.tfcCanChanHandle = self.zcanLib.InitCAN(TfcZlgCan.__gDevHandle, self.configInfo["can_channel"], chn_init_cfg)

        if self.tfcCanChanHandle is INVALID_CHANNEL_HANDLE:
            print("Channel handle is none.")
            exit(0)

        ret = self.zcanLib.SetValue(ip, str(self.configInfo['can_channel']) + "/initenal_resistance", "1")
        if ret != ZCAN_STATUS_OK:
            print("Open CH%d resistance failed!" %(self.configInfo['can_channel']))
            exit(0)

        ret = self.zcanLib.SetValue(ip, str(self.configInfo['can_channel']) + "/tx_timeout", "100")
        if ret != ZCAN_STATUS_OK:
            print("Open CH%d tx_timeou failed!" %(self.configInfo['can_channel']))
            exit(0)

        ret = self.zcanLib.SetValue(ip, str(self.configInfo['can_channel']) + "/filter_clear", "0")
        if ret != ZCAN_STATUS_OK:
            print("Open CH%d filter_clear failed!" %(self.configInfo['can_channel']))
            exit(0)

        if ZCAN_STATUS_OK != self.zcanLib.StartCAN(self.tfcCanChanHandle):
            print(" CAN Open failed.")
            exit(0)
        print(" Open channel {}.".format(self.configInfo['can_channel']))

        self.zcanLib.ReleaseIProperty(ip) 

        return self.tfcCanChanHandle


    '''
    TODO: add canfd 
    rcv_can_msgs = (ZCAN_Receive_Data * rcv_num)()
    '''
    def read(self):
        listFrames = []
        # rcv_num = self.zcanLib.GetReceiveNum(self.tfcCanChanHandle, self.configInfo['can_type'])
        rcv_num = self.zcanLib.GetReceiveNum(self.tfcCanChanHandle, 0)
        print("Received data number is:", rcv_num)
        if rcv_num > 0:
            print("Receive CAN message number: %d" %rcv_num)
            rcv_msg, rcv_num = self.zcanLib.Receive(self.tfcCanChanHandle, rcv_num = rcv_num)
            for i in range(rcv_num):
                data = []
                for j in range(rcv_msg[i].frame.can_dlc):
                    data.append(rcv_msg[i].frame.data[j])
                listFrames.append({'id':rcv_msg[i].frame.can_id, 'len':rcv_msg[i].frame.can_dlc, 'data':data})
            '''
            for i in range(rcv_num):
                print("[%d]:timestamps:%d,type:CAN, id:%s, dlc:%d, eff:%d, rtr:%d, data:%s" %(i, rcv_msg[i].timestamp, 
                      hex(rcv_msg[i].frame.can_id), rcv_msg[i].frame.can_dlc, 
                      rcv_msg[i].frame.eff, rcv_msg[i].frame.rtr,
                      ''.join(hex(rcv_msg[i].frame.data[j])+ ' 'for j in range(rcv_msg[i].frame.can_dlc))))
                        
            '''

            return listFrames

    def write(self, data = None):
        if not isinstance(data, str):
            print("The type of data is error.")
            exit(0)

        if len(data) == 0:
            print("The type of data error.")
            exit(0)
        data += '.'
        byteData = data.encode()
        dataRcv = self.__data2Frames(byteData)
        ret = self.zcanLib.Transmit(self.tfcCanChanHandle, dataRcv[1], dataRcv[0])
        print("Tranmit Num: %d." % ret)

    def __data2Frames(self, data):
        if not isinstance(data, (bytes, bytearray)):
            return None
        
        if len(data) % 8:
            transmit_num = len(data) // 8 + 1
            msgs = (ZCAN_Transmit_Data * transmit_num)()
            for i in range(transmit_num):
                msgs[i].transmit_type = 2 # 0-Normal，2-Only oneself
                msgs[i].frame.eff     = 0 # 0-Stand frame，1-Extended frame
                msgs[i].frame.rtr     = 0 # 0-Data frame，1-Remote frame
                msgs[i].frame.can_id  = i
                if i == (transmit_num - 1):
                    msgs[i].frame.can_dlc = len(data) % 8
                else:
                    msgs[i].frame.can_dlc = 8
                
                for j in range(msgs[i].frame.can_dlc):
                    msgs[i].frame.data[j] = data[8 * i + j]
        else:
            transmit_num = len(data) // 8 
            msgs = (ZCAN_Transmit_Data * transmit_num)()
            for i in range(transmit_num):
                msgs[i].transmit_type = 2
                msgs[i].frame.eff     = 0
                msgs[i].frame.rtr     = 0
                msgs[i].frame.can_id  = i
                msgs[i].frame.can_dlc = 8
                
                for j in range(msgs[i].frame.can_dlc):
                    msgs[i].frame.data[j] = data[8 * i + j]

        return [transmit_num, msgs]

    def getTestResult(self):

        '''
        TODO: Add a configure segment to identify the frame ID

        '''
        strRcv = ''
        startTime = time.time()
        endTime = self.rcvTimeout + startTime
        print("timeout is :", self.rcvTimeout)

        while True:
            if time.time() <= endTime:
                tmpFrames = self.read()
                if tmpFrames is None:
                    return strRcv
                if len(tmpFrames) > 0:
                    for frame in tmpFrames:
                        # if frame['id'] == self.configInfo["test_frame_id"]:
                        if True: #bytes(frame['data']).decode()
                            strRcv += bytes(frame['data']).decode()
                if strRcv.endswith('.'):
                    print( strRcv)
                    break
            else:
                break
        return strRcv
    
    def close(self):
        self.zcanLib.ResetCAN(self.tfcCanChanHandle)
        print("Finish")

    def closeDev(self):
        self.zcanLib.CloseDevice(TfcZlgCan.__gDevHandle)
        print("Close device.")


def testCanChan1(canChanHandle = None, threadCtrl = None):
    while True:
        time.sleep(5)
        if threadCtrl.is_alive() == False:
            break
        canChanHandle.getTestResult()
    canChanHandle.closeDev()

def input_thread():
   input()

def testCanIf():
    thread=threading.Thread(target=input_thread)
    thread.start()

    myCanConfig = {"can_dev_type":ZCAN_USBCANFD_400U,"can_channel":0, "can_baudrate":500000,
                       "can_type":ZCAN_TYPE_CANFD, "test_frame_id":0x100, "receive_timeout_s":5}
    myCan = TfcZlgCan(config=myCanConfig)
    myCan.open()

    myCanConfig2 = {"can_dev_type":ZCAN_USBCANFD_400U,"can_channel":2, "can_baudrate":500000,
                       "can_type":ZCAN_TYPE_CANFD, "test_frame_id":0x100, "receive_timeout_s":5}
    myCan2 = TfcZlgCan(config=myCanConfig2)
    myCan2.open()

    threadChan1=threading.Thread(target=testCanChan1, args=(myCan2,thread))
    threadChan1.start()

    time.sleep(2)


    while True:
        dataSend = 'Today is a nice day.\n'
        myCan.write(data=dataSend)
        time.sleep(2)

        if thread.is_alive() == False:
            break
    myCan2.closeDev()
    # print(myCan.getTestResult())
    


if __name__ == '__main__':
    testCanIf()
