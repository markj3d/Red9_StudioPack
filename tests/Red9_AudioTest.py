'''
------------------------------------------
Red9 Studio Pack: Maya Pipeline Solutions
Author: Mark Jackson
email: rednineinfo@gmail.com

Red9 blog : http://red9-consultancy.blogspot.co.uk/
MarkJ blog: http://markj3d.blogspot.co.uk
------------------------------------------

This is the main unittest for the Red9_Meta module and a good
example of what's expected and what the systems can do on simple data
================================================================

'''


#import pymel.core as pm
import maya.standalone
maya.standalone.initialize(name='python')

import Red9.core.Red9_Audio as r9Audio
import Red9.core.Red9_General as r9General
import Red9.startup.setup as r9Setup
r9Setup.start(Menu=False)
   
import maya.cmds as cmds
import os

class Test_BwavHandler(object):
    def setup(self):
        self.bwavpath=os.path.join(r9Setup.red9ModulePath(),'tests','testFiles','bwav_test.wav')
        self.audioNode = r9Audio.AudioNode.importAndActivate(self.bwavpath)
    
    def teardown(self):
        cmds.file(new=True,f=True)
        
    def test_basics(self):
        assert isinstance(self.audioNode, r9Audio.AudioNode)
        assert r9General.formatPath(self.audioNode.path)==r9General.formatPath(self.bwavpath)
        assert self.audioNode.audioNode=='bwav_test'
        assert self.audioNode.sample_width==2
        assert self.audioNode.sampleRate==44100
        assert self.audioNode.sample_bits==16
        assert self.audioNode.channels==1

    
    def test_funcs(self):
        assert self.audioNode.startFrame==0
        self.audioNode.startFrame=10
        assert self.audioNode.startFrame==10
        assert cmds.getAttr('%s.offset' % self.audioNode.audioNode)==10
        self.audioNode.offsetTime(25)
        assert self.audioNode.startFrame==35
    
        assert cmds.getAttr('%s.mute' % self.audioNode.audioNode)==False
        self.audioNode.mute(True)
        assert cmds.getAttr('%s.mute' % self.audioNode.audioNode)==True

        
    def test_bwav_handler(self):
        '''
        test the bwav handler and formatting of the data
        '''
        assert self.audioNode.isBwav()
        #print self.audioNode.bwav_timecodeFormatted()
        cmds.currentUnit(time='ntscf')
        assert r9General.getCurrentFPS()==60
        #print 'ntscf' ,  self.audioNode.bwav_timecodeFormatted()
        assert self.audioNode.bwav_timecodeFormatted()=='01:26:04:11'
        cmds.currentUnit(time='pal')
        assert r9General.getCurrentFPS()==25
        #print 'pal : ', self.audioNode.bwav_timecodeFormatted()
        assert self.audioNode.bwav_timecodeFormatted()=='01:26:04:05'
        #print self.audioNode.bwav_timecodeFormatted(smpte=False)
        assert self.audioNode.bwav_timecodeFormatted(smpte=False)=='01:26:04:172'
        assert self.audioNode.bwav_timecodeReference()==227739993
        assert self.audioNode.bwav_timecodeMS()==5164172.1768707484
        assert self.audioNode.bwav_HeaderData=={'AudioFormat': 0,
                                                 'BextVersion': 0,
                                                 'BitsPerSample': 0,
                                                 'ChunkSize': 732516,
                                                 'Description': 'This is a unitTest file for validating the Red9 broadcast wav extraction of metaData',
                                                 'Format': 'WAVE',
                                                 'InternalFormat': 'fmt ',
                                                 'OriginationDate': '2014-03-03',
                                                 'OriginationTime': '10:00:00',
                                                 'Originator': 'Pro Tools',
                                                 'OriginatorReference': 'ffgDDffdhgff',
                                                 'Subchunk1Size': 16,
                                                 'TimeReference': 227739993,
                                                 'TimeReferenceHigh': 0}
        
    def test_compiler(self):
        self.audioNode.stampCompiled(self.audioNode.audioNode)
        assert self.audioNode.isCompiled
                                                        