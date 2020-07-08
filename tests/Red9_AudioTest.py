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


# import pymel.core as pm
import maya.standalone
maya.standalone.initialize(name='python')

import Red9.core.Red9_Audio as r9Audio
import Red9.core.Red9_General as r9General
import Red9.startup.setup as r9Setup
import Red9.core.Red9_CoreUtils as r9Core
# r9Setup.start(Menu=False)

# force the upAxis, just in case
r9Setup.mayaUpAxis('y')


import maya.cmds as cmds
import os


class Test_AudioNode(object):
    def setup(self):
        cmds.file(new=True, f=True)
        self.path = r9General.formatPath(os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'bwav_test.wav'))

    def test_path_given(self):
        # build the AudioNode directly from the path not through Maya
        pathNode = r9Audio.AudioNode(filepath=self.path)
        assert not pathNode.isLoaded
        assert pathNode.path == self.path
        assert not pathNode.audioNode
        assert int(pathNode.endFrame) == 199
        assert int(pathNode.endTime) == 8294
        assert pathNode.startTime == 0
        assert pathNode.startFrame == 0
        pathNode.importAndActivate()
        assert pathNode.isLoaded
        assert pathNode.audioNode
        assert pathNode.isValid()

    def test_audioNode_given(self):
        # test from a given Maya sound node
        cmds.file(self.path, i=True, type='audio', options='o=0')
        node = cmds.ls(type='audio')[0]
        audio = r9Audio.AudioNode(node)
        assert audio.audioNode == node
        assert audio.isLoaded

    def test_path_but_Loaded(self):
        # from Path but that path is a loaded Maya sound node
        cmds.file(self.path, i=True, type='audio', options='o=0')
        node = cmds.ls(type='audio')[0]
        assert node
        audio = r9Audio.AudioNode(filepath=self.path)
        assert audio.path == self.path
        assert audio.isLoaded
        assert audio.audioNode == node

    def test_pyDub_base(self):
        # pyDub calls internal
        self.audioNode = r9Audio.AudioNode(filepath=self.path)
        assert self.audioNode.sample_width == 2
        assert self.audioNode.sampleRate == 44100
        assert self.audioNode.sample_bits == 16
        assert self.audioNode.channels == 1
        print self.audioNode.dBFS
        print self.audioNode.max_dBFS
        assert True  # self.audioNode.dBFS


class Test_BwavHandler(object):
    def setup(self):
        cmds.file(new=True, f=True)
        self.bwavpath = os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'bwav_test.wav')
        self.audioNode = r9Audio.AudioNode(filepath=self.bwavpath)
        self.audioNode.importAndActivate()
        cmds.currentUnit(time='ntsc')

    def test_funcs(self):
        assert isinstance(self.audioNode, r9Audio.AudioNode)
        assert r9General.formatPath(self.audioNode.path) == r9General.formatPath(self.bwavpath)
        assert self.audioNode.isLoaded
        assert cmds.ls(type='audio')[0] == 'bwav_test'
        assert self.audioNode.audioNode == 'bwav_test'

        assert self.audioNode.startFrame == 0
        self.audioNode.startFrame = 10
        assert self.audioNode.startFrame == 10
        assert cmds.getAttr('%s.offset' % self.audioNode.audioNode) == 10
        self.audioNode.offsetTime(25)
        assert self.audioNode.startFrame == 35

        assert cmds.getAttr('%s.mute' % self.audioNode.audioNode) == False
        self.audioNode.mute(True)
        assert cmds.getAttr('%s.mute' % self.audioNode.audioNode) == True


    def test_bwav_handler(self):
        '''
        test the bwav handler and formatting of the data
        '''
        assert self.audioNode.isBwav()
        # print self.audioNode.bwav_timecodeFormatted()
        cmds.currentUnit(time='ntscf')
        assert r9General.getCurrentFPS() == 60
        print 'ntscf' , self.audioNode.bwav_timecodeFormatted()
        assert self.audioNode.bwav_timecodeFormatted() == '01:26:04:11'
        cmds.currentUnit(time='pal')
        assert r9General.getCurrentFPS() == 25
        # print 'pal : ', self.audioNode.bwav_timecodeFormatted()
        assert self.audioNode.bwav_timecodeFormatted() == '01:26:04:05'
        # print self.audioNode.bwav_timecodeFormatted(smpte=False)
        assert self.audioNode.bwav_timecodeFormatted(smpte=False) == '01:26:04:172'
        assert self.audioNode.bwav_timecodeReference() == 227739993
        assert self.audioNode.bwav_timecodeMS() == 5164172.1768707484

        # need to get the bWav header to bind it to the var
        self.audioNode.bwav_getHeader()
        assert self.audioNode.bwav_HeaderData == {'AudioFormat': 0,
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


class Test_timecode_converts(object):
    def setup(self):
        cmds.file(new=True, f=True)
        cmds.currentUnit(time='ntsc')

    def test_full_convert(self):
        '''
        full round the houses process back to input value through all converts
        '''
        framerate = 30.0
        timecode = '00:10:13:22'

        a = r9Audio.timecode_to_milliseconds(timecode, smpte=True, framerate=framerate)
        print a
        assert r9Core.floatIsEqual(a, 613733, 0.0001)

        b = r9Audio.milliseconds_to_frame(a, framerate=framerate)
        print b
        assert r9Core.floatIsEqual(b, 18412.0 , 0.0001)

        c = r9Audio.frame_to_milliseconds(b, framerate=framerate)
        print c
        assert r9Core.floatIsEqual(c, 613733.0, 0.0001)

        d = r9Audio.milliseconds_to_Timecode(c, smpte=False, framerate=framerate)
        print d
        assert d == '00:10:13:733'  # note converted to non-smpte

        e = r9Audio.timecode_to_frame(d, smpte=False, framerate=framerate)
        print e
        assert r9Core.floatIsEqual(e, 18412.0, 0.0001)

        f = r9Audio.frame_to_timecode(e, smpte=True, framerate=framerate)
        print e
        assert f == '00:10:13:22'

        assert f == timecode

        # try again with single tests
        assert r9Audio.timecode_to_frame('06:10:29:29', smpte=True, framerate=framerate) == 666899.0
        assert r9Audio.frame_to_timecode(666899.0) == '06:10:29:29'

        assert r9Audio.timecode_to_milliseconds('06:10:29:29') == 22229966
        assert r9Audio.milliseconds_to_Timecode(22229966) == '06:10:29:29'

        assert r9Audio.frame_to_milliseconds(666899.0) == 22229966
        assert r9Audio.milliseconds_to_frame(22229966) == 666899.0

        assert r9Audio.timecode_to_frame('06:10:29:29', smpte=True, framerate=29.97) == 666232.13


    def test_timecode_formatter(self):
        '''
        Validate the format inspection for timecode in Pro
        '''
        pass

# print '\n\n ########### END'
# if float(cmds.about(v=True)) >= 2016.0:
#         maya.standalone.uninitialize()


