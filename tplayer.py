#!/usr/bin/python3
import threading
from os import path
import time
import gi

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstApp, GstController
bitrate=536
GObject.threads_init()
Gst.init(None)
def file_content(file):
        f = open(file, 'r')
        fc=f.read()
        fc=fc.strip()
        f.close()
        return fc

def write_content(file,content):
	f = open(file, 'w')
	f.write(content)
	f.close()
def append_content(file,content):
	f = open(file, 'a')
	f.write(str(content))
	f.close()	
def file_content(file):
	f = open(file, 'r')
	fc=f.read()
	fc=fc.strip()
	f.close()
	return fc    
class AudioDecoder(Gst.Bin):
    def __init__(self):
       # super().__init__()
	super(AudioDecoder, self).__init__()
        # Create elements
        q0 = Gst.ElementFactory.make('queue', None)
        aparse = Gst.ElementFactory.make('aacparse', None)
        decoder = Gst.ElementFactory.make('avdec_aac', None)
        q2 = Gst.ElementFactory.make('queue', None)

        # Add elements to Bin
        self.add(q0)
        self.add(aparse)
        self.add(decoder)
        self.add(q2)
        
        # Link elements
        q0.link(aparse)     
        aparse.link(decoder)

#       	enc.set_property('target', 1)  
#        enc.set_property('cbr', 'true')  
#        enc.set_property('tolerance', 400000000000)  
#        enc.set_property('bitrate', 64)  
#        enc.set_property('quality', 0)  
#        enc.set_property('encoding-engine-quality', 0)  

        decoder.link(q2)

        # Add Ghost Pads
        self.add_pad(
            Gst.GhostPad.new('sink', q0.get_static_pad('sink'))
        )
        self.add_pad(
            Gst.GhostPad.new('src', q2.get_static_pad('src'))
        )

class H264Decoder(Gst.Bin):
    def __init__(self):
#        super().__init__()
	super(H264Decoder, self).__init__()
        global bitrate, vwidth, vheight

        q1 = Gst.ElementFactory.make('queue', None)
        vaapiparse = Gst.ElementFactory.make('h264parse', None)
        self.decoder = Gst.ElementFactory.make('vaapidecode', None)
        q2 = Gst.ElementFactory.make('queue', None)



        
        # Add elements to Bin
        self.add(q1)
        self.add(self.decoder)
        self.add(vaapiparse)
        self.add(q2)

        q1.link(vaapiparse)
     
        vaapiparse.link_filtered(self.decoder,
        Gst.caps_from_string('video/x-h264,  profile=high')
        )
        self.decoder.link(q2)

        
        self.add_pad(
            Gst.GhostPad.new('sink', q1.get_static_pad('sink'))
        )
        self.add_pad(
            Gst.GhostPad.new('src', q2.get_static_pad('src'))
        )

class H265Decoder(Gst.Bin):
    def __init__(self):
#        super().__init__()
	super(H265Decoder, self).__init__()
        global bitrate, vwidth, vheight

        q1 = Gst.ElementFactory.make('queue', None)
        vaapiparse = Gst.ElementFactory.make('vaapiparse_h265', None)
        self.decoder = Gst.ElementFactory.make('libdex265', None)
        q2 = Gst.ElementFactory.make('queue', None)



        
        # Add elements to Bin
        self.add(q1)
        self.add(self.decoder)
        self.add(vaapiparse)
        self.add(q2)

        q1.link(vaapiparse)

        vaapiparse.link_filtered(self.decoder,
        Gst.caps_from_string('video/x-h265, profile=main')
        )
        self.decoder.link(q2)

        
        self.add_pad(
            Gst.GhostPad.new('sink', q1.get_static_pad('sink'))
        )
        self.add_pad(
            Gst.GhostPad.new('src', q2.get_static_pad('src'))
        )


class Example:
	def __init__(self):
		global bitrate, listener_ip
		self.bitrate=bitrate
		self.mainloop = GObject.MainLoop()
		self.pipeline = Gst.Pipeline()
		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect('message::eos', self.on_eos)
		self.bus.connect('message::error', self.on_error)
		# Create elements
		self.src = Gst.ElementFactory.make('tcpserversrc', None)
		self.src.set_property('host','192.168.0.8')
		self.src.set_property('port',1800)
		self.deinterlace = Gst.ElementFactory.make('deinterlace', None)
		videoscale = Gst.ElementFactory.make('videoscale', None)
		videorate = Gst.ElementFactory.make('videorate', None)
		convert = Gst.ElementFactory.make('videoconvert', None)
		self.video = H264Decoder()
		self.audio = AudioDecoder()
		self.tsparse = Gst.ElementFactory.make('tsparse', None)
		self.demuxer = Gst.ElementFactory.make('tsdemux', None)
		self.vsink=  Gst.ElementFactory.make('vaapisink', None)
		self.asink=  Gst.ElementFactory.make('autoaudiosink', None)
		# Add elements to pipeline      
		self.pipeline.add(self.src)
		self.pipeline.add(self.tsparse)
		self.pipeline.add(self.demuxer)
		self.pipeline.add(self.video)
		self.pipeline.add(self.audio)
		self.pipeline.add(self.vsink)
		self.pipeline.add(self.asink)
		self.src.link(self.tsparse)
		self.tsparse.link(self.demuxer)
		self.video.link(self.vsink)
		self.audio.link(self.asink)
		self.demuxer.connect('pad-added', self.on_pad_added)

	def on_new_buffer(self, sink):
		sample = sink.emit("pull-sample")
		buf = sample.get_buffer() 
		data=buf.extract_dup(0,buf.get_size())
		append_content(file,str(buf))
   		print str(data)
		return False

	def on_new_preroll(self, sink):
		buf = appink.emit('pull-preroll')
		print ('new preroll', str(len(buf)))
		
		
	def run(self):
        	self.pipeline.set_state(Gst.State.PLAYING)
        	self.mainloop.run()

	def kill(self):
        	self.pipeline.set_state(Gst.State.NULL)
        	self.mainloop.quit()

	def on_pad_added(self, element, pad):
		string = pad.query_caps(None).to_string()
		print('on_pad_added():', string)
		if string.startswith('audio/'):
			pad.link(self.audio.get_static_pad('sink'))
		elif string.startswith('video/'):
			pad.link(self.video.get_static_pad('sink'))

	def on_eos(self, bus, msg):
		print('on_eos()')
		self.pipeline.set_state(Gst.State.PAUSED)
		self.pipeline.set_state(Gst.State.NULL)
		self.pipeline.set_state(Gst.State.PLAYING)

	def on_error(self, bus, msg):
		print('on_error():', msg.parse_error())
		self.pipeline.set_state(Gst.State.PAUSED)
		self.pipeline.set_state(Gst.State.NULL)
		self.pipeline.set_state(Gst.State.PLAYING)



import argparse
vwidth='720'
vheight='486'
example=Example()
example.run()
