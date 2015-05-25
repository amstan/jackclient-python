#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import jack
import binascii
from queue import Queue

client = jack.Client("MIDI-Monitor")
port = client.midi_inports.register("input")
queue = Queue(0)


@client.set_process_callback
def process(frames):
    last_frame_time = client.last_frame_time
    for offset, data in port.incoming_midi_events():
        queue.put_nowait((last_frame_time + offset, data))
    return jack.CALL_AGAIN

with client:
    print("#" * 80)
    print("press Ctrl+C to quit")
    print("#" * 80)
    while True:
        event_time, data = queue.get()
        print("{0}: 0x{1}".format(event_time, binascii.hexlify(data).decode()))
