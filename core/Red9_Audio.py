'''
..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com

    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk


This is the Audio library of utils used throughout the modules

'''

from __future__ import print_function

import maya.cmds as cmds
import maya.mel as mel
from functools import partial
import os
# import struct
# import math
# import re

import Red9_General as r9General
import Red9.startup.setup as r9Setup
import Red9_Meta as r9Meta
import Red9_CoreUtils as r9Core


import wave
import contextlib

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

try:
    from ..packages.pydub.pydub import audio_segment
except:
    log.debug('unable to import pydub libs')


# ------------------------------------------------------------------------------------------------
# ProPack management and legacy wraps for the timecode converts
# ------------------------------------------------------------------------------------------------

def bind_pro_audio():
    '''
    This is a wrap to import the pro_audio extensions. We have to
    lazy load this to avoid cyclic issues in the boot and wrapping it
    like this makes it easy to consume in the classes
    '''
    if r9Setup.has_pro_pack():
        try:
            import Red9.pro_pack.core.audio as r9paudio  # dev mode only ;)
        except StandardError, err:
            from Red9.pro_pack import r9pro
            r9paudio = r9pro.r9import('r9paudio')
        return r9paudio

def milliseconds_to_Timecode(milliseconds, smpte=True, framerate=None):
    return bind_pro_audio().milliseconds_to_Timecode(milliseconds, smpte=smpte, framerate=framerate)

def milliseconds_to_frame(milliseconds, framerate=None):
    return bind_pro_audio().milliseconds_to_frame(milliseconds, framerate=framerate)

def timecode_to_milliseconds(timecode, smpte=True, framerate=None):
    return bind_pro_audio().timecode_to_milliseconds(timecode, smpte=smpte, framerate=framerate)

def timecode_to_frame(timecode, smpte=True, framerate=None):
    try:
        return bind_pro_audio().timecode_to_frame(timecode, smpte=smpte, framerate=framerate)
    except:
        import traceback
        print(traceback.format_exc())

def frame_to_timecode(frame, smpte=True, framerate=None):
    return bind_pro_audio().frame_to_timecode(frame, smpte=smpte, framerate=framerate)

def frame_to_milliseconds(frame, framerate=None):
    return bind_pro_audio().frame_to_milliseconds(frame, framerate=framerate)

# ProPack Bind End ----


def combineAudio():
    '''
    this is a logic wrapper over the main compile call in the AudioHandler
    I wanted to keep things simple in the base class.

    '''
    prompt = False
    filepath = None
    audioHandler = AudioHandler()

    if not len(audioHandler.audioNodes) > 1:
        raise ValueError('We need more than 1 audio node in order to compile')

    for audio in cmds.ls(type='audio'):
        audioNode = AudioNode(audio)
        if audioNode.isCompiled:
            result = cmds.confirmDialog(
                title='Compiled Audio',
                message='Compiled Audio Track already exists, over-right this instance?\n\nSoundNode : %s' % audioNode.audioNode,
                button=['OK', 'Generate New', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
            if result == 'OK':
                filepath = audioNode.path
            elif result == 'Cancel':
                return
            else:
                prompt = True
            break

    scenepath = cmds.file(q=True, sn=True)
    if not filepath:
        if not scenepath or prompt:
            filepath = cmds.fileDialog2(fileFilter="Wav Files (*.wav *.wav);;", okc='Save')[0]
        else:
            filepath = '%s_combined.wav' % os.path.splitext(scenepath)[0]
    audioHandler.combineAudio(filepath)


def audioSelected():
    selected = cmds.ls(sl=True, type='audio')
    if selected:
        return selected[0]

def audioPathLoaded(filepath):
    '''
    return any soundNodes in Maya that point to the given audio path
    '''
    nodes = []
    if not os.path.exists(filepath):
        return nodes
    for audio in cmds.ls(type='audio'):
        if r9General.formatPath(cmds.getAttr('%s.filename' % audio)) == r9General.formatPath(filepath):
            nodes.append(audio)
    return nodes

def inspect_wav(multi=False, audioNodes=[]):
    '''
    Simple UI to show internal Wav file properties. Supports full Broadcast Wav inspection

    :param multi: allow multiple audio nodes to be inspected
    :param audioNodes: allows you to pass in either Maya sound nodes or filepaths to wavs to inspect
    '''
    if not audioNodes:
        audio = cmds.ls(sl=True, type='audio')
        if multi:
            audioNodes = audio
        else:
            audioNodes = [audio[0]]

    if not audioNodes:
        raise StandardError('Please select the soundNode you want to inspect - no Sound nodes selected')

    winOffset = 0
    for audio in audioNodes:
        if cmds.objExists(audio):
            audio = AudioNode(audio)
        else:
            audio = AudioNode(filepath=audio)
        formatData = ''
        data = audio.gatherInfo()
        for key, val in data.items():
            if not key == 'bwav':
                formatData += '{:<15}: {:}\n'.format(key, val)
        bWavData = ''
        if 'bwav' in data.keys():
            bWavData += 'TimecodeFormatted : %s\n' % data['bwav']['TimecodeFormatted']
            bWavData += 'TimecodeReference : %i\n\n' % data['bwav']['TimecodeReference']
            for key, value in sorted(data['bwav'].items()):
                if key not in ['TimecodeFormatted', 'TimecodeReference']:
                    bWavData += '%s : %s\n' % (key, value)

        win = cmds.window(title="Red9 Wav Inspector: %s" % audio.audioNode)
        cmds.columnLayout(adjustableColumn=True, columnOffset=('both', 20))
        cmds.separator(h=15, style='none')
        cmds.text(l='Inspect Internal Sound file data:', font='boldLabelFont')
        cmds.text(l='Note that if the wav is in Bwav format you also get additional metaData')
        cmds.separator(h=15, style='in')
        cmds.text(l=formatData, align='left', font="fixedWidthFont")
        if data:
            cmds.separator(h=10, style='in')
            cmds.text(l='Broadcast Wav metaData', font='boldLabelFont')
            cmds.separator(h=15, style='in')
            cmds.text(l=bWavData, align='left')
        cmds.showWindow(win)
        tlc = cmds.window(win, q=True, topLeftCorner=True)
        cmds.window(win, e=True, topLeftCorner=(tlc[0] + winOffset, tlc[1] + winOffset))
        winOffset += 25


# Audio Handlers  -----------------------------------------------------

class AudioHandler(object):
    '''
    process on multiple audio nodes within the Maya scene, ie, already loaded

    .. note::
        all BWav and Timecode support is in the Red9 ProPack
    '''
    def __init__(self, audio=None):
        self._audioNodes = []
        if audio:
            self.audioNodes = audio
        else:
            if cmds.ls(sl=True, type='audio'):
                self.audioNodes = cmds.ls(sl=True, type='audio')
            else:
                self.audioNodes = cmds.ls(type='audio')

        # bind ProPack Timecode node
        self.pro_audio = bind_pro_audio()

    @property
    def audioNodes(self):
        if not self._audioNodes:
            raise StandardError('No AudioNodes selected or given to process')
        return self._audioNodes

    @audioNodes.setter
    def audioNodes(self, val):
        if not val:
            raise StandardError('No AudioNodes selected or given to process')
        if not type(val) == list:
            val = [val]
        for a in val:
            if issubclass(type(a), AudioNode):
                log.debug('Instantiated AudioNode passed in  : %s' % a)
                self._audioNodes.append(a)
            else:
                log.debug('unicode audio str passed in  : %s' % a)
                self._audioNodes.append(AudioNode(a))
        # self._audioNodes = [AudioNode(audio) for audio in val]

    @property
    def mayaNodes(self):
        return [audio.audioNode for audio in self.audioNodes]

    def getAudioInRange(self, time=(), asNodes=True, start_inRange=True, end_inRange=True):
        '''
        return any audio in the handler within a given timerange

        :param time: tuple, (min,max) timerange which returned audio has to fall
             within else it's ignored.
        :param asNodes: return the data as r9Audio.AudioNodes, default=True
        :param start_inRange: check if the audio startFrame is after the time[0] value
        :param end_inRange: check if the audio endFrame is before the time[1] value

        .. note::
            if you pass in time as (None, 100) then we only validate against the end time.
            if we pass in time as (10, None) we only validate against the start time
            else we validate that the audio's start and end times are fully within the time range given
        '''
        audio_in_range = []
        for a in self.audioNodes:
            if r9Core.timeIsInRange(time, (a.startFrame, a.endFrame), start_inRange=start_inRange, end_inRange=end_inRange):
                audio_in_range.append(a)
        if not asNodes:
            return [a.audioNode for a in audio_in_range]
        return audio_in_range

    def getOverallRange(self):
        '''
        return the overall frame range of the given audioNodes (min/max)
        '''
        minV = self.audioNodes[0].startFrame
        maxV = self.audioNodes[0].endFrame
        for a in self.audioNodes:
            minV = min(minV, a.startFrame)
            maxV = max(maxV, a.endFrame)  # why the hell does this always come back 1 frame over??
        return (minV, maxV)

    def getOverallBwavTimecodeRange(self, ms=False):
        '''
        : PRO_PACK :
            return the overall internal BWAV timecode range for the given
            nodes. Note this is the internal timecode plus the length of the files

        :param ms: return the (minV,maxV) in milliseconds or SMPTE timecode
        '''
        maxV = None
        minV = None
        for a in self.audioNodes:
            if a.isBwav():
                tcStart = a.bwav_timecodeMS()
                tcEnd = tcStart + self.pro_audio.frame_to_milliseconds(a.getLengthFromWav())
                if not minV:
                    minV = tcStart
                    maxV = tcEnd
                else:
                    minV = min(minV, tcStart)
                    maxV = max(maxV, tcEnd)
        if ms:
            return (minV, maxV)
        else:
            return (self.pro_audio.milliseconds_to_Timecode(minV), self.pro_audio.milliseconds_to_Timecode(maxV))

    def setTimelineToAudio(self, audioNodes=None):
        '''
        set the current TimeSlider to the extent of the given audioNodes
        '''
        frmrange = self.getOverallRange()
        cmds.playbackOptions(min=int(frmrange[0]), max=int(frmrange[1]))

    def setActive(self):
        if len(self.audioNodes) == 1:
            self.audioNodes[0].setActive()
        else:
            gPlayBackSlider = mel.eval("string $temp=$gPlayBackSlider")
            cmds.timeControl(gPlayBackSlider, e=True, ds=1, sound="")

    def offsetBy(self, offset):
        '''
        offset all audioNode by a given frame offset
        '''
        for node in self.audioNodes:
            node.offsetTime(offset)

    def offsetRipple(self, *args):
        '''
        offset all audioNodes so that they ripple in the
        order of self.audioNodes
        '''
        endFrm = None
        for node in self.audioNodes:
            if not endFrm:
                endFrm = node.endFrame
            else:
                log.debug('previous EndFrm : %s, current startFrm : %s, offset : %s' %
                          (endFrm, node.startFrame, endFrm - node.startFrame))
                node.offsetTime(endFrm - node.startFrame)
                endFrm = node.endFrame

    def offsetTo(self, startFrame):
        '''
        offset all audio such that they start relative to a given frame,
        takes the earliest startpoint of the given audio to calculate how much
        to offset by

        :param startFrame: the required start frame to set too
        '''
        minV, _ = self.getOverallRange()
        offset = startFrame - minV
        for node in self.audioNodes:
            node.offsetTime(offset)

    def muteSelected(self, state=True):
        for a in self.audioNodes:
            a.mute(state)

    def lockTimeInputs(self, state=True):
        '''
        lock the time attrs of the audio nodes so they can't be slipped or moved by accident

        :param state: state of the lock, True or False
        '''
        for a in self.audioNodes:
            a.lockTimeInputs(state)

    def deleteSelected(self):
        for a in self.audioNodes:
            a.delete()

    def formatNodes_to_Path(self):
        '''
        rename the sound nodes to match their internal audioPath filename
        '''
        for a in self.audioNodes:
            a.formatAudioNode_to_Path()

    def bwav_sync_to_Timecode(self, relativeToo=None, offset=0, timecodebase=None, *args):
        '''
        : PRO_PACK :
            process either selected or all audio nodes and IF they are found
            to be BWav's with valid timecode references, sync them in Maya such
            that their offset = Bwav's timecode ie: sync them on the timeline to
            the bwavs internal timecode.

        :param relativeToo: This is fucking clever, even though I do say so. Pass in another BWav Audio node and we
            calculate it's internal timecode against where it is in the timeline. We then use any difference in
            that nodes time as an offset for all the other nodes in self.audioNodes. Basically syncing multiple
            bwav's against a given sound.
        :param offset: given offset (in frames) to pass to the sync call
        :param timecodebase: optional mapping for a reference timecode so we can manipulate the offset
            relative to a given timecodebase rather than assuming that frame 1 = '00:00:00:00'
            ie, we set the timecodebase to '01:00:00:00' therefore day 1 timecode is stripped from
            all the calculations and a bwav who's timecode is '01:00:00:10' is set to frame 10
        '''
        fails = []
        if not relativeToo:
            for audio in self.audioNodes:
                if audio.isBwav():
                    audio.bwav_sync_to_Timecode(offset=offset, timecodebase=timecodebase)
                else:
                    fails.append(audio.audioNode)
        else:
            relativeNode = AudioNode(relativeToo)
            if not relativeNode.isBwav():
                raise StandardError('Given Reference audio node is NOT  a Bwav!!')

            # calculate the frame difference to use as an offset
            relativeTC = self.pro_audio.milliseconds_to_frame(relativeNode.bwav_timecodeMS())
            actualframe = relativeNode.startFrame
            diff = actualframe - relativeTC

            log.info('internalTC: %s , internalStartFrm %s, offset required : %f' % (relativeNode.bwav_timecodeFormatted(), relativeTC, diff))
            for audio in self.audioNodes:
                if audio.isBwav():
                    audio.bwav_sync_to_Timecode(offset=diff + offset, timecodebase=timecodebase)
                else:
                    fails.append(audio.audioNode)
        if fails:
            for f in fails:
                print('Error : Audio node is not in Bwav format : %s' % f)
            log.warning('Some Audio Node were not in Bwav format, see script editor for debug')
            # self.offsetBy(diff)

    def bwav_sync_to_dynamic(self, tc_node):
        '''
        : PRO_PACK :
            like the baw_sync_to_timecode func this will sync this audio bwav node to a given timecode
            but the difference here is that that timecode is extracted dynamically from a given node,
            stamped with the Red9 timecode attrs. This also supports multiple timecode takes within the
            same node

        :param tc_node: the Maya node that has the Red9 Timecode attrs that we want to sync against
        '''
        fails = []
        _timecode = self.pro_audio.Timecode(tc_node)
        _bounds = _timecode.getTimecode_bounds()
        for audio in self.audioNodes:
            if audio.isBwav():
                synced = audio.bwav_sync_to_dynamic(tc_node, bounds=_bounds)
            else:
                fails.append(audio.audioNode)
        if fails:
            for f in fails:
                print('Error : Audio node failed to sync : %s' % f)
            log.warning('Some Audio Node were not in Bwav format, see script editor for debug')

#     def delCombined(self):
#         audioNodes=cmds.ls(type='audio')
#         if not audioNodes:
#             return
#         for audio in audioNodes:
#             audioNode=AudioNode(audio)
#             if audioNode.path==filepath:
#                 if audioNode.isCompiled:
#                     log.info('Deleting currently compiled Audio Track')
#                     if audioNode in self.audioNodes:
#                         self.audioNodes.remove(audioNode)
#                     audioNode.delete()
#                     break
#                 else:
#                     raise IOError('Combined Audio path is already imported into Maya')

    def combineAudio(self, filepath):
        '''
        Combine audio tracks into a single wav file. This by-passes
        the issues with Maya not playblasting multiple audio tracks.

        :param filepath: filepath to store the combined audioTrack
        TODO: Deal with offset start and end data + silence
        '''
        status = True
        failed = []
        if not len(self.audioNodes) > 1:
            raise ValueError('We need more than 1 audio node in order to compile')

        for audio in cmds.ls(type='audio'):
            audioNode = AudioNode(audio)
            if audioNode.path == filepath:
                if audioNode.isCompiled:
                    log.info('Deleting currently compiled Audio Track : %s' % audioNode.path)
                    if audioNode in self.audioNodes:
                        self.audioNodes.remove(audioNode)
                    audioNode.delete()
                    break
                else:
                    raise IOError('Combined Audio path is already imported into Maya')

        frmrange = self.getOverallRange()
        neg_adjustment = 0
        if frmrange[0] < 0:
            neg_adjustment = frmrange[0]

        duration = ((frmrange[1] + abs(neg_adjustment)) / r9General.getCurrentFPS()) * 1000
        log.info('Audio BaseTrack duration = %f' % duration)
        baseTrack = audio_segment.AudioSegment.silent(duration)

        for audio in self.audioNodes:
            if not os.path.exists(audio.path):
                log.warning('Audio file not found!  : "%s" == %s' % (audio.audioNode, audio.path))
                status = False
                failed.append(audio)
                continue
            # deal with any trimming of the audio node in Maya
            sourceStart = cmds.getAttr(audio.audioNode + '.sourceStart')
            sourceEnd = cmds.getAttr(audio.audioNode + '.sourceEnd')
            sound = audio_segment.AudioSegment.from_wav(audio.path)[(sourceStart / r9General.getCurrentFPS()) * 1000:(sourceEnd / r9General.getCurrentFPS()) * 1000]
            # sound = audio_segment.AudioSegment.from_wav(audio.path)
            if sound.sample_width not in [1, 2, 4]:
                log.warning('24bit Audio is NOT supported in Python audioop lib!  : "%s" == %i' % (audio.audioNode, sound.sample_width))
                status = False
                failed.append(audio)
                continue
            insertFrame = (audio.startFrame + abs(neg_adjustment))
            log.info('inserting sound : %s at %f adjusted to %f' %
                     (audio.audioNode, audio.startFrame, insertFrame))
            baseTrack = baseTrack.overlay(sound, position=(insertFrame / r9General.getCurrentFPS()) * 1000)

        baseTrack.export(filepath, format="wav")
        compiled = AudioNode(filepath=filepath)
        compiled.importAndActivate()
        compiled.stampCompiled(self.mayaNodes)
        compiled.startFrame = neg_adjustment

        if not status:
            raise StandardError('combine completed with errors: see script Editor for details')


class AudioNode(object):
    '''
    Single AudioNode handler for simple audio management object

    "Broadcast Wav" format now supported using specs from :
    https://tech.ebu.ch/docs/tech/tech3285.pdf

    '''
    def __init__(self, audioNode=None, filepath=None):
        self.__path = ''
        self.__audioNode = None
        self.isLoaded = False  # if true we're only working on an audioPath, NOT an active Maya soundNode
        self.pro_bwav = None

        if not filepath:
            if audioNode:
                if issubclass(type(audioNode), AudioNode):
                    # log.info('Audio is already an instatiated audioNode')
                    self.audioNode = audioNode.audioNode
                self.audioNode = audioNode
            else:
                self.audioNode = audioSelected()
            if self.audioNode:
                self.isLoaded = True
        else:
            # You can't load a wav more than once, if path is mapped to a current node, switch the class to that
            isAudioloaded = audioPathLoaded(filepath)
            if isAudioloaded:
                log.info('given audio filePath is already assigned to a Maya node, connecting to that : %s' % isAudioloaded[0])
                self.isLoaded = True
                self.audioNode = isAudioloaded[0]
            else:
                self.isLoaded = False
            self.path = filepath

        # bind ProPack bwav support
        if r9Setup.has_pro_pack():
            self.pro_audio = bind_pro_audio()
            self.pro_bwav = self.pro_audio.BWav_Handler(self.path)

    def __repr__(self):
        if self.isLoaded:
            if self.audioNode:
                return "%s(AudioNode InternalAudioNodes: '%s')" % (self.__class__, self.audioNode)
            else:
                return "%s(AudioNode NO AudioNodes: )" % self.__class__
        else:
            return "%s(AudioNode from file: %s)" % (self.__class__, self.path)

    def __eq__(self, val):
        if self.isLoaded:
            if isinstance(val, AudioNode):
                return self.audioNode == val.audioNode
            elif cmds.nodeType(val) == 'audio':
                return self.audioNode == val
        else:
            return self.path == val.path

    def __ne__(self, val):
        return not self.__eq__(val)

    @property
    def path(self):
        if self.isLoaded and self.audioNode:
            return cmds.getAttr('%s.filename' % self.audioNode)
        else:
            return self.__path

    @path.setter
    def path(self, path):
        self.__path = path
        if self.pro_bwav:
            # print 'setting new path', self.pro_bwav.path
            self.pro_bwav.path = path
            log.debug('Setting BWAV internal path : %s' % self.pro_bwav)

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def audioNode(self):
        return self.__audioNode

    @audioNode.setter
    def audioNode(self, node):
        if node and cmds.objExists(node):
            self.isLoaded = True
            self.__audioNode = node

    def gatherInfo(self):
        '''
        gather all general data on this audioNode
        replicates the ProPack's gatherInfo call on mNodes
        '''
        data = {}
        data['SoundNode'] = self.audioNode
        data['Filepath'] = self.path
        data['Duration'] = self.duration
        data['Sample_Width'] = self.sample_width
        data['BitRate'] = self.sample_bits
        data['SampleRate'] = self.sampleRate
        data['Channels'] = self.channels
        data['dBFS'] = self.dBFS
        data['Max dBFS'] = self.max_dBFS

        if self.bwav_getHeader():
            data['bwav'] = {}
            data['bwav']['TimecodeFormatted'] = self.bwav_timecodeFormatted()
            data['bwav']['TimecodeReference'] = self.bwav_timecodeReference()
            for key, value in sorted(self.bwav_HeaderData.items()):
                data['bwav'][key] = value
        return data

    # ---------------------------------------------------------------------------------
    # pyDub inspect calls ---
    # ---------------------------------------------------------------------------------
    # https://github.com/jiaaro/pydub/blob/master/API.markdown

    @property
    def sampleRate(self):
        '''
        sample rate in milliseconds
        '''
        return audio_segment.AudioSegment.from_wav(self.path).frame_rate

    @property
    def sample_width(self):
        '''
        bytes per sample, is converted by the sample_bits into bitrate
        '''
        return audio_segment.AudioSegment.from_wav(self.path).sample_width

    @property
    def sample_bits(self):
        '''
        bit rate taken from the bytes per sample : 4,8,16,24 bit
        '''
        data = {'1': 8, '2': 16, '3': 24, '4': 32}
        return data[str(audio_segment.AudioSegment.from_wav(self.path).sample_width)]

    @property
    def channels(self):
        '''
        number of channels 1=mone, 2=stereo
        '''
        return audio_segment.AudioSegment.from_wav(self.path).channels

    @property
    def dBFS(self):
        '''
        loudness of the AudioSegment in dBFS (db relative to the maximum possible loudness)
        '''
        return audio_segment.AudioSegment.from_wav(self.path).dBFS

    @property
    def max_dBFS(self):
        '''
        The highest amplitude of any sample in the AudioSegment,
        in dBFS (relative to the highest possible amplitude value).
        '''
        return audio_segment.AudioSegment.from_wav(self.path).max_dBFS

    @property
    def duration(self):
        '''
        return the duration of the wav from the file directly
        '''
        return audio_segment.AudioSegment.from_wav(self.path).duration_seconds

    # pyDub end ---

    @property
    def startFrame(self):
        '''
        Maya start frame of the sound node
        '''
        if self.isLoaded:
            return cmds.getAttr('%s.offset' % self.audioNode)
        return 0

    @startFrame.setter
    def startFrame(self, val):
        if self.isLoaded:
            cmds.setAttr('%s.offset' % self.audioNode, val)

    @property
    def endFrame(self):
        '''
        Note in batch mode we calculate via the Wav duration
        NOT the Maya audioNode length as it's invalid under batch mode!
        '''
        if not cmds.about(batch=True) and self.isLoaded:
            return cmds.getAttr('%s.endFrame' % self.audioNode)  # why the hell does this always come back 1 frame over??
        else:
            return self.getLengthFromWav() + self.startFrame

    @endFrame.setter
    def endFrame(self, val):
        '''
        Maya end frame of the sound node
        '''
        if self.isLoaded:
            cmds.setAttr('%s.offset' % self.audioNode, val)

    @property
    def startTime(self):
        '''
        : PRO_PACK : Maya start time of the sound node in milliseconds
        '''
        if self.isLoaded:
            return (self.startFrame / r9General.getCurrentFPS()) * 1000
        return 0

    @startTime.setter
    def startTime(self, val):
        if self.isLoaded:
            cmds.setAttr('%s.offset' % self.audioNode, self.pro_audio.milliseconds_to_frame(val, framerate=None))

    @property
    def endTime(self):
        '''
        : PRO_PACK : Maya end time of the sound node in milliseconds
        '''
        return (self.endFrame / r9General.getCurrentFPS()) * 1000

    @endTime.setter
    def endTime(self, val):
        if self.isLoaded:
            cmds.setAttr('%s.offset' % self.audioNode, self.pro_audio.milliseconds_to_frame(val, framerate=None))

    @property
    def offset(self):
        '''
        simply get the offset
        '''
        return cmds.getAttr('%s.offset' % self.audioNode)

    @offset.setter
    def offset(self, offset):
        if self.isLoaded:
            cmds.setAttr('%s.offset' % self.audioNode, offset)

    def inspect(self):
        '''
        simple warp over the inspect function to bind it to this audioNode instance
        '''
        inspect_wav(multi=False, audioNodes=[self.audioNode])

    def to_mono(self, output):
        '''
        convert a stereo file to mono
        '''
        if not output:
            output = self.path
        audioseg = audio_segment.AudioSegment.from_wav(self.path)
        audioseg = audioseg.set_channels(1)
        audioseg.export(output, format="wav")

    # ---------------------------------------------------------------------------------
    # PRO_PACK : BWAV support ---
    # ---------------------------------------------------------------------------------

    def isBwav(self):
        '''
        : PRO_PACK : validate if the given source Wav is a BWav or not
        '''
        if self.pro_bwav:
            return self.pro_bwav.isBwav()
        else:
            raise r9Setup.ProPack_Error()

    def bwav_getHeader(self):
        '''
        : PRO_PACK : get the internal BWav header data from the wav if found
        '''
        if self.pro_bwav:
            self.bwav_HeaderData = self.pro_bwav.bwav_getHeader()
            return self.bwav_HeaderData
        else:
            raise r9Setup.ProPack_Error()

    def bwav_timecodeMS(self):
        '''
        : PRO_PACK : read the internal timecode reference from the bwav and convert that number into milliseconds
        '''
        if self.pro_bwav:
            return self.pro_bwav.bwav_timecodeMS()
        else:
            raise r9Setup.ProPack_Error()

    def bwav_timecodeReference(self):
        '''
        : PRO_PACK : if is BWaw return the internal timeReference
        '''
        if self.pro_bwav:
            return self.pro_bwav.bwav_timecodeReference()
        else:
            raise r9Setup.ProPack_Error()

    def bwav_timecodeFormatted(self, smpte=True, framerate=None):
        '''
        : PRO_PACK : if is Bwav return the internal timecode & convert from milliseconds into timecode

        :param smpte: format the timecode HH:MM:SS:FF where FF is frames, else milliseconds
        :param framerate: when using smpte this is the framerate used in the FF block
        '''
        if self.pro_bwav:
            return self.pro_bwav.bwav_timecodeFormatted(smpte=smpte, framerate=framerate)
        else:
            raise r9Setup.ProPack_Error()

    def bwav_sync_to_Timecode(self, offset=0, timecodebase=None):
        '''
        : PRO_PACK : given that self is a Bwav and has timecode reference, sync it's position
        in the Maya timeline to match

        :param offset: offset (in frames) to apply to the internal timecode of the given wav's
        :param timecodebase: optional mapping for a reference timecode so we can manipulate the offset
            relative to a given timecodebase rather than assuming that frame 1 = '00:00:00:00'
            ie, we set the timecodebase to '01:00:00:00' therefore day 1 timecode is stripped from
            all the calculations and a bwav who's timecode is '00:00:00:10' is set to frame 10
        '''
        if self.isLoaded and self.pro_bwav and self.pro_bwav.isBwav():
            if timecodebase:
                offset = offset - self.pro_audio.timecode_to_frame(timecodebase)
                # print 'new timecode base given : %s : new offset = %s' % (timecodebase,offset)
            self.startFrame = self.pro_audio.milliseconds_to_frame(self.pro_bwav.bwav_timecodeMS()) + offset
        else:
            raise r9Setup.ProPack_Error()

    def bwav_sync_to_dynamic(self, tc_node, bounds=[]):
        '''
        like the baw_sync_to_timecode func this will sync this audio bwav node to a given timecode
        but the difference here is that that timecode is extracted dynamically from a given node,
        stamped with the Red9 timecode attrs. This also supports multiple timecode takes within the
        same node
        '''
        if self.isLoaded and self.pro_bwav and self.pro_bwav.isBwav():
            _timecode = self.pro_audio.Timecode(tc_node)
            if not bounds:
                bounds = _timecode.getTimecode_bounds()
            matchedStart_tc = _timecode.find_Timecode_frame(self.pro_bwav.bwav_timecodeFormatted(), bounds=bounds, set=False)
            if matchedStart_tc:
                self.startFrame = matchedStart_tc
            else:
                pass
        else:
            raise r9Setup.ProPack_Error()

    def isConnected_AudioGrp(self):
        '''
        : PRO_PACK : is this audioNode connected to a Pro_ AudioGrp metaNode
        for asset management in the Pro systems
        '''
        return r9Meta.getConnectedMetaNodes(self.audioNode, mTypes='AudioGroup')

    # ---------------------------------------------------------------------------------
    # General utils ---
    # ---------------------------------------------------------------------------------

    def isValid(self):
        '''
        If the audionode is loaded in maya then valid is if that node we're pointing to exists
        If the audionode is NOT loaded and we just have a path check if that path exists
        '''
        if self.isLoaded:
            return (self.audioNode and cmds.objExists(self.audioNode) and os.path.exists(self.path)) or False
        else:
            return os.path.exists(self.path)

    def delete(self):
        '''
        Maya delete the sound node
        '''
        if self.isLoaded:
            cmds.delete(self.audioNode)

    def offsetTime(self, offset):
        '''
        offset the time of this audioNode instance

        :param offset: amount to offset
        '''
        if self.isLoaded:
            if r9Setup.mayaVersion() == 2011:
                # Autodesk fucked up in 2011 and we need to manage both these attrs
                cmds.setAttr('%s.offset' % self.audioNode, self.startFrame + offset)
                cmds.setAttr('%s.endFrame' % self.audioNode, self.length + offset)
            else:
                cmds.setAttr('%s.offset' % self.audioNode, self.startFrame + offset)

    def importAndActivate(self, active=True):
        '''
        If self was instantiated with filepath then this will import that wav
        into Maya and activate it on the timeline. Note that if there is already
        an instance of a sound node in Maya that points to this path them the
        class will bind itself to that node.

        :param active: do we set the imported audio to be active on the timerange in Maya

        >>> # example of use:
        >>> audio = r9Audio.AudioNode(filepath = 'c:/my_audio.wav')
        >>> audio.importAndActivate()
        '''
        if not self.isLoaded:
            a = cmds.ls(type='audio')
            cmds.file(self.path, i=True, type='audio', options='o=0')
            b = cmds.ls(type='audio')

            if not a == b:
                self.audioNode = (list(set(a) ^ set(b))[0])
            else:
                matchingnode = [audio for audio in a if cmds.getAttr('%s.filename' % audio) == self.path]
                if matchingnode:
                    self.audioNode = matchingnode[0]
                else:
                    log.warning("can't find match audioNode for path : %s" % self.path)
                    return
            self.isLoaded = True
        else:
            log.info('given Audio Path is already loaded in the Maya Scene')
        if active:
            self.setActive()

    def setActive(self):
        '''
        Set the sound node as active on the timeSlider
        '''
        if self.isLoaded:
            gPlayBackSlider = mel.eval("string $temp=$gPlayBackSlider")
            cmds.timeControl(gPlayBackSlider, e=True, ds=1, sound=self.audioNode)

    def getLengthFromWav(self):
        '''
        This uses the wav itself bypassing the Maya handling, why?
        In maya.standalone the audio isn't loaded correctly and always is of length 1!
        '''
        with contextlib.closing(wave.open(self.path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return (duration) * r9General.getCurrentFPS()

    def setTimeline(self, full=False):
        '''
        Set the Maya timeline to the duration of the sound
        '''
        if self.isLoaded:
            cmds.playbackOptions(min=int(self.startFrame), max=int(self.endFrame))
            if full:
                cmds.playbackOptions(ast=int(self.startFrame), aet=int(self.endFrame))

    def mute(self, state=True):
        '''
        Maya sound node, mute the sound

        :param state: the mute state to use, default is True
        '''
        if self.isLoaded:
            cmds.setAttr('%s.mute' % self.audioNode, state)

    def openAudioPath(self):
        path = self.path
        if path and os.path.exists(path):
            r9General.os_OpenFileDirectory(path)

    def formatAudioNode_to_Path(self):
        '''
        rename the AudioNode so it ties to the wav name
        '''
        try:
            cmds.rename(self.audioNode, r9Core.nodeNameStrip(os.path.splitext(os.path.basename(self.path))[0]))
        except:
            if cmds.referenceQuery(self.audioNode, inr=True):
                log.info('failed to Rename Referenced Audio Node : %s' % self.audioNode)
            else:
                log.info('failed to Rename Audio node : %s' % self.audioNode)

    def lockTimeInputs(self, state=True):
        '''
        lock the audio in time so it can't be accidentally shifted

        :param state: the lock state of the node, True or False
        '''
        cmds.setAttr('%s.offset' % self.audioNode, l=state)
        cmds.setAttr('%s.sourceEnd' % self.audioNode, l=state)
        cmds.setAttr('%s.sourceStart' % self.audioNode, l=state)
        cmds.setAttr('%s.endFrame' % self.audioNode, l=state)

    @property
    def isCompiled(self):
        '''
        return if the audioNode in Maya was generated via the compileAudio
        call in the AudioHandler.
        '''
        if self.isLoaded:
            if cmds.attributeQuery('compiledAudio', exists=True, node=self.audioNode):
                return True

    def stampCompiled(self, audioNodes):
        '''
        Used by the Audio compiler - stamp the audioNodes from which this audio
        track was compiled from

        :param audioNodes: the audioNodes being compiled
        '''
        if self.isLoaded:
            cmds.addAttr(self.audioNode, longName='compiledAudio', dt='string')
            cmds.setAttr('%s.compiledAudio' % self.audioNode, ','.join(audioNodes), type="string")

    def select(self):
        if self.isLoaded:
            cmds.select(self.audioNode)


class AudioToolsWrap(object):
    def __init__(self):
        self.win = 'AudioOffsetManager'
        self.__bwav_reference = None

        # bind ProPack Timecode node
        if r9Setup.has_pro_pack():
            self.pro_audio = bind_pro_audio()

    @classmethod
    def show(cls):
        cls()._showUI()

    def close(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self):
        self.close()

        cmds.window(self.win, title=self.win)  # , widthHeight=(400, 220))
        cmds.columnLayout('uicl_audioMain', adjustableColumn=True)
        cmds.separator(h=15, style='none')
        cmds.text(l='Select Audio Node to Offset')
        cmds.separator(h=15, style='in')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 90), (3, 100)])
        cmds.button(label='<< Offset',
                    ann='Nudge selected Audio Backwards',
                    command=partial(self.offsetSelectedBy, 'negative'))
        cmds.floatField('AudioOffsetBy', value=10)
        cmds.button(label='Offset >>',
                    ann='Nudge selected Audio Forwards',
                    command=partial(self.offsetSelectedBy, 'positive'))
        cmds.setParent('..')
        cmds.separator(h=15, style='in')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 200), (2, 90)])
        cmds.button(label='Offset Range to Start at:',
                    ann='offset the selected range of audionodes such that they start at the given frame',
                    command=self.offsetSelectedTo)
        cmds.floatField('AudioOffsetToo', value=10)
        cmds.setParent('..')
        cmds.separator(h=15, style='in')
        cmds.button(label='Ripple selected',
                    ann="Ripple offset the selected audio nodes so they're timed one after another",
                    command=self.offsetRipple)
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                             c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
        cmds.separator(h=15, style='none')
        cmds.showWindow(self.win)
        # cmds.window(self.win, e=True, widthHeight=(290, 190))

    def __uicb_cacheAudioNodes(self, *args):
        self.audioHandler = AudioHandler()

    def offsetSelectedBy(self, direction, *args):
        self.audioHandler = AudioHandler()
        offset = cmds.floatField('AudioOffsetBy', q=True, v=True)
        if direction == 'negative':
            offset = 0 - offset
        self.audioHandler.offsetBy(float(offset))

    def offsetSelectedTo(self, *args):
        self.audioHandler = AudioHandler()
        offset = cmds.floatField('AudioOffsetToo', q=True, v=True)
        self.audioHandler.offsetTo(float(offset))

    def offsetRipple(self, *args):
        self.audioHandler = AudioHandler()
        self.audioHandler.offsetRipple()
