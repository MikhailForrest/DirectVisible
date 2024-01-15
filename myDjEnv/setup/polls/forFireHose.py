import json, sys, zlib, time

class InflateStream:
   "A wrapper for a socket carrying compressed data that does streaming decompression"

   def __init__(self, sock, mode):
      self.sock = sock
      self._buf = bytearray()
      self._eof = False
      if mode == 'deflate':     # no header, raw deflate stream
         self._z = zlib.decompressobj(-zlib.MAX_WBITS)
      elif mode == 'compress':  # zlib header
         self._z = zlib.decompressobj(zlib.MAX_WBITS)
      elif mode == 'gzip':      # gzip header
         self._z = zlib.decompressobj(16 | zlib.MAX_WBITS)
      else:
         raise ValueError('unrecognized compression mode')

   def _fill(self):
      rawdata = self.sock.recv(8192)
      if len(rawdata) == 0:
         self._buf += self._z.flush()
         self._eof = True
      else:
         self._buf += self._z.decompress(rawdata)

   def readline(self):
      newline = self._buf.find(b'\n')
      while newline < 0 and not self._eof:
         self._fill()
         newline = self._buf.find(b'\n')

      if newline >= 0:
         rawline = self._buf[:newline+1]
         del self._buf[:newline+1]
         return rawline.decode('ascii')

      # EOF
      return ''


# function to parse JSON data:
def parse_json( str ):
   try:
       # parse all data into dictionary decoded:
       decoded = json.loads(str)
       print(decoded)

       # compute the latency of this message:
       clocknow = time.time()
       diff = clocknow - int(decoded['pitr'])
       print("diff = {0:.2f} s\n".format(diff))
   except (ValueError, KeyError, TypeError):
       print("JSON format error: ", sys.exc_info()[0])
       print(str)
       #print(traceback.format_exc())
   return ''