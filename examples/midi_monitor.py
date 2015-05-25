#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import jack
import binascii
import time
import struct

client = jack.Client("MIDI-Monitor")
port = client.midi_inports.register("input")

class MidiEventBuffer(object):
    EVENT_HEADER_FORMAT = "IB"
    # NOTE: The 'B' (length) is actually size_t,
    # but it's rare to have midi event be over 255 in length
    EVENT_HEADER_SIZE = struct.calcsize(EVENT_HEADER_FORMAT)

    def __init__(self):
        self.ringbuffer = jack.RingBuffer(1000)

    def insert(self, event_time, data):
        if self.ringbuffer.write_space < (self.EVENT_HEADER_SIZE + len(data)):
            # no space in the ringbuffer, discard it
            return
            # perhaps make a note of it?
            # printing at this point is still a bad idea, it might actually make matters worse.

        self.ringbuffer.write(struct.pack(self.EVENT_HEADER_FORMAT, event_time, len(data)))
        self.ringbuffer.write(data)

    def __iter__(self):
        while True:
            while self.ringbuffer.read_space < self.EVENT_HEADER_SIZE:
                time.sleep(0.05) #wait a little bit to not use all the cpu
            header = self.ringbuffer.read(self.EVENT_HEADER_SIZE)
            event_time, length = struct.unpack(self.EVENT_HEADER_FORMAT, header)
            while self.ringbuffer.read_space < length:
                time.sleep(0.05) #wait a little bit to not use all the cpu
            data = self.ringbuffer.read(length)

            yield event_time, data

midi_event_buffer = MidiEventBuffer()

@client.set_process_callback
def process(frames):
    last_frame_time = client.last_frame_time
    for offset, data in port.incoming_midi_events():
        midi_event_buffer.insert(last_frame_time + offset, data)
    return jack.CALL_AGAIN

with client:
    print("#" * 80)
    print("press Ctrl+C to quit")
    print("#" * 80)
    for event_time, data in midi_event_buffer:
        print("{0}: 0x{1}".format(event_time, binascii.hexlify(data).decode()))
