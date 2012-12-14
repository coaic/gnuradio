#!/usr/bin/env python
#
# Copyright 2012 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import gr, gr_unittest
import parse_file_metadata
import blocks_swig as blocks
import pmt
import os, time

class test_file_metadata(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001(self):
	outfile = "test_out.dat"

        detached = False
        samp_rate = 200000
        key = pmt.pmt_intern("samp_rate")
        val = pmt.pmt_from_double(samp_rate)
        extras = pmt.pmt_make_dict()
        extras = pmt.pmt_dict_add(extras, key, val)
        extras_str = pmt.pmt_serialize_str(extras)

        src = gr.sig_source_c(samp_rate, gr.GR_COS_WAVE, 1000, 1, 0)
        head = gr.head(gr.sizeof_gr_complex, 1000)
        fsnk = blocks.file_meta_sink(gr.sizeof_gr_complex, outfile,
                                     samp_rate, 1, 
                                     blocks.GR_FILE_FLOAT, True,
                                     1000000, extras_str, detached)
        fsnk.set_unbuffered(True)

	self.tb.connect(src, head, fsnk)
	self.tb.run()
        fsnk.close()

        handle = open(outfile, "rb")
        header_str = handle.read(parse_file_metadata.HEADER_LENGTH)
        if(len(header_str) == 0):
            self.assertFalse()

        try:
            header = pmt.pmt_deserialize_str(header_str)
        except RuntimeError:
            self.assertFalse()

        info = parse_file_metadata.parse_header(header, False)

        extra_str = handle.read(info["extra_len"])
        self.assertGreater(len(extra_str), 0)
        handle.close()

        try:
            extra = pmt.pmt_deserialize_str(extra_str)
        except RuntimeError:
            self.assertFalse()

        extra_info = parse_file_metadata.parse_extra_dict(extra, info, False)

        self.assertEqual(info['rx_rate'], samp_rate)
        self.assertEqual(pmt.pmt_to_double(extra_info['samp_rate']), samp_rate)


        # Test file metadata source
        # Create a new sig source to start from the beginning
        src2 = gr.sig_source_c(samp_rate, gr.GR_COS_WAVE, 1000, 1, 0)
        fsrc = blocks.file_meta_source(outfile, False)
        vsnk = gr.vector_sink_c()
        tsnk = gr.tag_debug(gr.sizeof_gr_complex, "QA")
        ssnk = gr.vector_sink_c()
        head.reset()
        self.tb.disconnect(src, head, fsnk)
        self.tb.connect(fsrc, vsnk)
        self.tb.connect(fsrc, tsnk)
        self.tb.connect(src2, head, ssnk)
        self.tb.run()

        # Test to make sure tags with 'samp_rate' and 'rx_rate' keys
        # were generated and received correctly.
        tags = tsnk.current_tags()
        for t in tags:
            if(pmt.pmt_eq(t.key, pmt.pmt_intern("samp_rate"))):
                self.assertEqual(pmt.pmt_to_double(t.value), samp_rate)
            elif(pmt.pmt_eq(t.key, pmt.pmt_intern("rx_rate"))):
                self.assertEqual(pmt.pmt_to_double(t.value), samp_rate)

        # Test that the data portion was extracted and received correctly.
        self.assertComplexTuplesAlmostEqual(vsnk.data(), ssnk.data(), 5)

	os.remove(outfile)

    def test_002(self):
	outfile = "test_out.dat"
	outfile_hdr = "test_out.dat.hdr"

        detached = True
        samp_rate = 200000
        key = pmt.pmt_intern("samp_rate")
        val = pmt.pmt_from_double(samp_rate)
        extras = pmt.pmt_make_dict()
        extras = pmt.pmt_dict_add(extras, key, val)
        extras_str = pmt.pmt_serialize_str(extras)

        src = gr.sig_source_c(samp_rate, gr.GR_COS_WAVE, 1000, 1, 0)
        head = gr.head(gr.sizeof_gr_complex, 1000)
        fsnk = blocks.file_meta_sink(gr.sizeof_gr_complex, outfile,
                                     samp_rate, 1, 
                                     blocks.GR_FILE_FLOAT, True,
                                     1000000, extras_str, detached)
        fsnk.set_unbuffered(True)

	self.tb.connect(src, head, fsnk)
	self.tb.run()
        fsnk.close()

        # Open detached header for reading
        handle = open(outfile_hdr, "rb")
        header_str = handle.read(parse_file_metadata.HEADER_LENGTH)
        if(len(header_str) == 0):
            self.assertFalse()

        try:
            header = pmt.pmt_deserialize_str(header_str)
        except RuntimeError:
            self.assertFalse()

        info = parse_file_metadata.parse_header(header, False)

        extra_str = handle.read(info["extra_len"])
        self.assertGreater(len(extra_str), 0)
        handle.close()

        try:
            extra = pmt.pmt_deserialize_str(extra_str)
        except RuntimeError:
            self.assertFalse()

        extra_info = parse_file_metadata.parse_extra_dict(extra, info, False)

        self.assertEqual(info['rx_rate'], samp_rate)
        self.assertEqual(pmt.pmt_to_double(extra_info['samp_rate']), samp_rate)


        # Test file metadata source
        # Create a new sig source to start from the beginning
        src2 = gr.sig_source_c(samp_rate, gr.GR_COS_WAVE, 1000, 1, 0)
        fsrc = blocks.file_meta_source(outfile, False, detached, outfile_hdr)
        vsnk = gr.vector_sink_c()
        tsnk = gr.tag_debug(gr.sizeof_gr_complex, "QA")
        ssnk = gr.vector_sink_c()
        head.reset()
        self.tb.disconnect(src, head, fsnk)
        self.tb.connect(fsrc, vsnk)
        self.tb.connect(fsrc, tsnk)
        self.tb.connect(src2, head, ssnk)
        self.tb.run()

        # Test to make sure tags with 'samp_rate' and 'rx_rate' keys
        # were generated and received correctly.
        tags = tsnk.current_tags()
        for t in tags:
            if(pmt.pmt_eq(t.key, pmt.pmt_intern("samp_rate"))):
                self.assertEqual(pmt.pmt_to_double(t.value), samp_rate)
            elif(pmt.pmt_eq(t.key, pmt.pmt_intern("rx_rate"))):
                self.assertEqual(pmt.pmt_to_double(t.value), samp_rate)

        # Test that the data portion was extracted and received correctly.
        self.assertComplexTuplesAlmostEqual(vsnk.data(), ssnk.data(), 5)

	os.remove(outfile)
	os.remove(outfile_hdr)

if __name__ == '__main__':
    gr_unittest.run(test_file_metadata, "test_file_metadata.xml")