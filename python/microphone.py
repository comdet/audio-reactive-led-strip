import time
import numpy as np
import pyaudio
import config


def start_stream(callback):
    p = pyaudio.PyAudio()    

    recorded_frames = []
    device_info = {}
    useloopback = False
    recordtime = 5
    try:
        default_device_index = p.get_default_input_device_info()
    except IOError:
        default_device_index = -1

    #Select Device
    print ("Available devices:\n")
    for i in range(0, p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print (str(info["index"]) + ": \t %s \n \t %s \n" % (info["name"], p.get_host_api_info_by_index(info["hostApi"])["name"]))

        if default_device_index == -1:
            default_device_index = info["index"]

    #Handle no devices available
    if default_device_index == -1:
        print ("No device available. Quitting.")
        exit()

    #Get input or default
    device_id = int(input("Choose device [" + str(default_device_index)  + "]: ") or default_device_index)
    print ("")

    #Get device info
    try:
        device_info = p.get_device_info_by_index(device_id)
    except IOError:
        device_info = p.get_device_info_by_index(default_device_index)
        print ("Selection not available, using default.")

    #Choose between loopback or standard mode
    is_input = device_info["maxInputChannels"] > 0
    is_wasapi = (p.get_host_api_info_by_index(device_info["hostApi"])["name"]).find("WASAPI") != -1
    if is_input:
        print ( "Selection is input using standard mode.\n")
    else:
        if is_wasapi:
            useloopback = True;
            print ("Selection is output. Using loopback mode.\n")
        else:
            print ("Selection is input and does not support loopback mode. Quitting.\n")
            exit()


    #Open stream
    channelcount = device_info["maxInputChannels"] if (device_info["maxOutputChannels"] < device_info["maxInputChannels"]) else device_info["maxOutputChannels"]

    frames_per_buffer = int(config.MIC_RATE / config.FPS)
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    #rate=config.MIC_RATE,
                    rate=int(device_info["defaultSampleRate"]),
                    input=True,
                    frames_per_buffer=frames_per_buffer,
                    input_device_index = device_info["index"],
                    as_loopback = useloopback)
    overflows = 0
    prev_ovf_time = time.time()
    while True:
        try:
            y = np.fromstring(stream.read(frames_per_buffer), dtype=np.int16)
            y = y.astype(np.float32)
            callback(y)
        except IOError:
            overflows += 1
            if time.time() > prev_ovf_time + 1:
                prev_ovf_time = time.time()
                print('Audio buffer has overflowed {} times'.format(overflows))
    stream.stop_stream()
    stream.close()
    p.terminate()
