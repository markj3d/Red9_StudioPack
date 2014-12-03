'''
..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com
    
    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk
    

This is the Audio library of utils used throughout the modules


'''
from __future__ import with_statement  # required only for Maya2009/8
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
import os
import struct
import math

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
    
    
## Timecode conversion utilities   -----------------------------------------------------

class Timecode(object):

    count = 'timecode_count'  # linear key-per-frame data used to keep track of timecode during animation
    samplerate = 'timecode_samplerate'  # fps used to generate the linear count curve
    ref = 'timecode_ref'  # milliseconds start point used as the initial reference
    
    @staticmethod
    def getTimecode_from_node(node):
        '''
        wrapper method to get the timecode back from a given node
        :param node: node containing correctly formatted timecode data
        
        .. note:
                the node passed in has to have the correctly formatted timecode data to compute
        '''
        node = r9Meta.MetaClass(node)
        if node.hasAttr(Timecode.ref):
            ms = (getattr(node, Timecode.ref) + ((float(getattr(node, Timecode.count)) / getattr(node,Timecode.samplerate)) * 1000))
            return milliseconds_to_Timecode(ms)
        
    @staticmethod
    def addTimecode_to_node(node):
        '''
        wrapper to add the timecode attrs to a node ready for propagating
        '''
        node = r9Meta.MetaClass(node)
        node.addAttr(Timecode.count, attrType='float')
        node.addAttr(Timecode.samplerate, attrType='float')
        node.addAttr(Timecode.ref, attrType='int')


def milliseconds_to_Timecode(milliseconds, smpte=True, framerate=None):
        '''
        convert milliseconds into correctly formatted timecode
        
        :param milliseconds: time in milliseconds
        :param smpte: format the timecode HH:MM:SS:FF where FF is frames
        :param framerate: when using smpte this is the framerate used in the FF block
            default (None) uses the current scenes framerate
        
        .. note::
            * If smpte = False : the format will be HH:MM:SS:MSS = hours, minutes, seconds, milliseconds
            * If smpte = True  : the format will be HH:MM:SS:FF  = hours, minutes, seconds, frames
        '''
        def __zeropad(value):
            if value<10:
                return '0%s' % value
            else:
                return value

        if not framerate:
            framerate=r9General.getCurrentFPS()
            
        if milliseconds > 3600000:
            hours = int(math.floor(milliseconds / 3600000))
            milliseconds -= (hours * 3600000)
        else:
            hours = 0
        if milliseconds > 60000:
            minutes = int(math.floor(milliseconds / 60000))
            milliseconds -= (minutes * 60000)
        else:
            minutes = 0
        if milliseconds > 1000:
            seconds = int(math.floor(milliseconds / 1000))
            milliseconds -= (seconds * 1000)
        else:
            seconds = 0
        frame = int(math.floor(milliseconds))
        if smpte:
            frame = int(math.ceil((float(frame)/1000) * float(framerate)))
            
        return "{0}:{1}:{2}:{3}".format(__zeropad(hours),
                                        __zeropad(minutes),
                                        __zeropad(seconds),
                                        __zeropad(frame))
  

def milliseconds_to_frame(milliseconds, framerate=None):
    '''
    convert milliseconds into frames
        
    :param milliseconds: time in milliseconds
    :param framerate: when using smpte this is the framerate used in the FF block
        default (None) uses the current scenes framerate
    '''
    if not framerate:
        framerate=r9General.getCurrentFPS()
    return  (float(milliseconds) / 1000) * framerate
    
             
def timecode_to_milliseconds(timecode, smpte=True, framerate=None):
    '''
    from a properly formatted timecode return it in milliseconds
    r9Audio.timecode_to_milliseconds('09:00:00:00')
    
    :param timecode: '09:00:00:20' as a string
    :param smpte: calculate the milliseconds based on HH:MM:SS:FF (frames as last block)
    :param framerate: only used if smpte=True, the framerate to use in the conversion, 
        default (None) uses the current scenes framerate
    '''
    if not framerate:
        framerate=r9General.getCurrentFPS()
            
    data = timecode.split(':')
    if not len(data) ==4:
        raise IOError('timecode should be in the format "09:00:00:00"')
    if smpte and int(data[3])>framerate:
        raise IOError('timecode is badly formatted, frameblock is greater than given framerate')
    actual = int(data[0]) * 3600000
    actual += int(data[1]) * 60000
    actual += int(data[2]) * 1000
    if smpte:
        actual += (int(data[3]) * 1000) / float(framerate)
    else:
        actual += int(data[3])
    return actual

def timecode_to_frame(timecode, smpte=True, framerate=None):
    '''
    from a properly formatted timecode return it in frames
    r9Audio.timecode_to_milliseconds('09:00:00:00')
    
    :param timecode: '09:00:00:20' as a string
    :param smpte: calculate the milliseconds based on HH:MM:SS:FF (frames as last block)
    :param framerate: only used if smpte=True, the framerate to use in the conversion, 
        default (None) uses the current scenes framerate
    ''' 
    ms=timecode_to_milliseconds(timecode, smpte=smpte, framerate=framerate)
    return milliseconds_to_frame(ms, framerate)
    
def frame_to_timecode(frame, smpte=True, framerate=None):
    '''
    from a given frame return that time as timecode
    relative to the given framerate
    
    :param frame: current frame in Maya
    :param smpte: calculate the milliseconds based on HH:MM:SS:FF (frames as last block)
    :param framerate: the framerate to use in the conversion, 
        default (None) uses the current scenes framerate
    '''
    ms=frame_to_milliseconds(frame, framerate)
    return milliseconds_to_Timecode(ms, smpte=smpte, framerate=framerate)
    
def frame_to_milliseconds(frame, framerate=None):
    '''
    from a given frame return that time in milliseconds 
    relative to the given framerate
    
    :param frame: current frame in Maya
    :param framerate: only used if smpte=True, the framerate to use in the conversion, 
        default (None) uses the current scenes framerate
    '''
    if not framerate:
        framerate=r9General.getCurrentFPS()
    return (frame / float(framerate)) * 1000
    


def combineAudio():
    '''
    this is a logic wrapper over the main compile call in the AudioHandler 
    I wanted to keep things simple in the base class. 
    
    '''
    prompt=False
    filepath = None
    audioHandler = AudioHandler()
    
    if not len(audioHandler.audioNodes)>1:
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
                prompt=True
            break
        
    scenepath = cmds.file(q=True, sn=True)
    if not filepath:
        if not scenepath or prompt:
            filepath = cmds.fileDialog2(fileFilter="Wav Files (*.wav *.wav);;", okc='Save')[0]
        else:
            filepath = '%s_combined.wav' % os.path.splitext(scenepath)[0]
    audioHandler.combineAudio(filepath)


def audioSelected():
    selected = cmds.ls(sl=True,type='audio')
    if selected:
        return selected[0]

def audioPathLoaded(filepath):
    '''
    return any soundNodes in Maya that point to the given 
    audio path
    '''
    nodes=[]
    if not os.path.exists(filepath):
        return nodes
    for audio in cmds.ls(type='audio'):
        if r9General.formatPath(cmds.getAttr('%s.filename' % audio)) == r9General.formatPath(filepath):
            nodes.append(audio)
    return nodes
    
def inspect_wav():
    '''
    Simple UI to show internal Wav file properties. Supports full Broadcast Wav inspection
    '''
    audioNodes=audioSelected()
    if not audioNodes:
        raise StandardError('Please select the soundNode you want to inspect - no Sound nodes selected')
    audio = AudioNode(audioNodes)
    data = audio.bwav_getHeader()
    
    formatData='SoundNode : %s\n' % audio.audioNode
    formatData+='Sample_Width : %s\n' % audio.sample_width
    formatData+='BitsPerSample : %s\n' % audio.sample_bits
    formatData+='SampleRate : %s\n' % audio.sampleRate
    formatData+='Channels : %s\n' % audio.channels
    formatData+='Filepath : %s\n\n' % audio.path
    bWavData=''
    if data:
        bWavData+='TimecodeFormatted : %s\n' % audio.bwav_timecodeFormatted()
        bWavData+='TimecodeReference : %i\n\n' % audio.bwav_timecodeReference()
        for key, value in sorted(audio.bwav_HeaderData.items()):
            bWavData += '%s : %s\n' % (key, value)
    
    win=cmds.window(title="Red9 Wav Inspector: %s" % audio.audioNode)
    cmds.columnLayout(adjustableColumn=True, columnOffset=('both',20))
    cmds.separator(h=15, style='none')
    cmds.text(l='Inspect Internal Sound file data:', font='boldLabelFont')
    cmds.text(l='Note that if the wav is in Bwav format you also get additional metaData')
    cmds.separator(h=15, style='in')
    cmds.text(l=formatData,align='left')
    if data:
        cmds.separator(h=10, style='in')
        cmds.text(l='Broadcast Wav metaData', font='boldLabelFont')
        cmds.separator(h=15, style='in')
        cmds.text(l=bWavData, align='left')
    cmds.showWindow(win)
   
    
    
## Audio Handlers  -----------------------------------------------------
    
class AudioHandler(object):
    '''
    process on multiple audio nodes within the Maya scene, ie, already loaded
    '''
    def __init__(self, audio=None):
        self._audioNodes = None
        if audio:
            self.audioNodes = audio
        else:
            if cmds.ls(sl=True,type='audio'):
                self.audioNodes = cmds.ls(sl=True,type='audio')
            else:
                self.audioNodes = cmds.ls(type='audio')

    @property
    def audioNodes(self):
        if not self._audioNodes:
            raise StandardError('No AudioNodes selected or given to process')
        return self._audioNodes
    
    @audioNodes.setter
    def audioNodes(self, val):
        #print val, type(val)
        if not val:
            raise StandardError('No AudioNodes selected or given to process')
        if not type(val)==list:
            val = [val]
        self._audioNodes = [AudioNode(audio) for audio in val]
    
    @property
    def mayaNodes(self):
        return [audio.audioNode for audio in self.audioNodes]
    
    def getOverallRange(self):
        '''
        return the overall frame range of the given audioNodes (min/max)
        '''
        minV=self.audioNodes[0].startFrame
        maxV=self.audioNodes[0].endFrame
        for a in self.audioNodes:
            minV=min(minV, a.startFrame)
            maxV=max(maxV, a.endFrame)  # why the hell does this always come back 1 frame over??
        return (minV, maxV)

    def getOverallBwavTimecodeRange(self, ms=False):
        '''
        return the overall internal BWAV timecode range for the given nodes
        NOte this is the internal timecode plus the length of the files
        
        :param ms: return the (minV,maxV) in milliseconds or SMPTE timecode 
        '''
        maxV = None
        minV = None
        for a in self.audioNodes:
            if a.isBwav():
                tcStart = a.bwav_timecodeMS()
                tcEnd = tcStart + frame_to_milliseconds(a.getLengthFromWav())
                if not minV:
                    minV=tcStart
                    maxV=tcEnd
                else:
                    minV=min(minV, tcStart)
                    maxV=max(maxV, tcEnd)
        if ms:
            return (minV,maxV)
        else:
            return (milliseconds_to_Timecode(minV), milliseconds_to_Timecode(maxV))
         
    def setTimelineToAudio(self, audioNodes=None):
        '''
        set the current TimeSlider to the extent of the given audioNodes
        '''
        frmrange=self.getOverallRange()
        cmds.playbackOptions(min=int(frmrange[0]), max=int(frmrange[1]))
      
    def setActive(self):
        if len(self.audioNodes)==1:
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
            
    def offsetTo(self, startFrame):
        '''
        offset all audio such that they start relative to a given frame,
        takes the earliest startpoint of the given audio to calculate how much
        to offset by
        '''
        minV, _ = self.getOverallRange()
        offset = startFrame-minV
        for node in self.audioNodes:
            node.offsetTime(offset)
            
    def muteSelected(self, state=True):
        for a in self.audioNodes:
            a.mute(state)
    
    def lockTimeInputs(self, state=True):
        for a in self.audioNodes:
            a.lockTimeInputs(state)
            
    def deleteSelected(self):
        for a in self.audioNodes:
            a.delete()
    
    def formatNodes_to_Path(self):
        for a in self.audioNodes:
            a.formatAudioNode_to_Path()
            
    def bwav_sync_to_Timecode(self, relativeToo=None, offset=0, *args):
        '''
        process either selected or all audio nodes and IF they are found to be
        BWav's with valid timecode references, sync them in Maya such
        that their offset = Bwav's timecode ie: sync them on the timeline to
        the bwavs internal timecode.
        
        :param relativeToo: This is fucking clever, even though I do say so. Pass in another bWav node and I 
            calculate it's internal timecode against where it is in the timeline. I then use any difference in 
            that nodes time as an offset for all the other nodes in self.audioNodes. Basically syncing multiple 
            bwav's against a given sound.
        :param offset: given offset to pass to the sync call, does not process with the relativeToo flag
        '''
        fails=[]
        if not relativeToo:
            for audio in self.audioNodes:
                if audio.isBwav():
                    audio.bwav_sync_to_Timecode(offset=offset)
                else:
                    fails.append(audio.audioNode)
        else:
            relativeNode=AudioNode(relativeToo)
            if not relativeNode.isBwav():
                raise StandardError('Given Reference audio node is NOT  a Bwav!!')
            
            relativeTC = milliseconds_to_frame(relativeNode.bwav_timecodeMS())
            actualframe = relativeNode.startFrame
            diff = actualframe - relativeTC
            
            log.info('internalTC: %s , internalStartFrm %s, offset required : %f' % (relativeNode.bwav_timecodeFormatted(), relativeTC, diff))
            for audio in self.audioNodes:
                if audio.isBwav():
                    audio.bwav_sync_to_Timecode(offset=diff)
                else:
                    fails.append(audio.audioNode)
        if fails:
            for f in fails:
                print 'Error : Audio node is not in Bwav format : %s' % f
            log.warning('Some Audio Node were not in Bwav format, see script editor for debug')
            #self.offsetBy(diff)
              
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
        the issues with Maya not playblasting multip audio tracks.
        
        :param filepath: filepath to store the combined audioTrack
        TODO: Deal with offset start and end data + silence
        '''
        status=True
        if not len(self.audioNodes)>1:
            raise ValueError('We need more than 1 audio node in order to compile')

        for audio in cmds.ls(type='audio'):
            audioNode=AudioNode(audio)
            if audioNode.path==filepath:
                if audioNode.isCompiled:
                    log.info('Deleting currently compiled Audio Track : %s' % audioNode.path)
                    if audioNode in self.audioNodes:
                        self.audioNodes.remove(audioNode)
                    audioNode.delete()
                    break
                else:
                    raise IOError('Combined Audio path is already imported into Maya')
            
        frmrange = self.getOverallRange()
        neg_adjustment=0
        if frmrange[0] < 0:
            neg_adjustment=frmrange[0]
            
        duration = ((frmrange[1] + abs(neg_adjustment)) / r9General.getCurrentFPS()) * 1000
        log.info('Audio BaseTrack duration = %f' % duration)
        baseTrack = audio_segment.AudioSegment.silent(duration)

        for audio in self.audioNodes:
            sound = audio_segment.AudioSegment.from_wav(audio.path)
            if sound.sample_width not in [1, 2, 4]:
                log.warning('24bit Audio is NOT supported in Python audioop lib!  : "%s" == %i' % (audio.audioNode, sound.sample_width))
                status = False
                continue
            insertFrame = (audio.startFrame + abs(neg_adjustment))
            log.info('inserting sound : %s at %f adjusted to %f' % \
                     (audio.audioNode, audio.startFrame, insertFrame))
            baseTrack = baseTrack.overlay(sound, position=(insertFrame / r9General.getCurrentFPS()) * 1000)

        baseTrack.export(filepath, format="wav")
        compiled=AudioNode(filepath=filepath)
        compiled.importAndActivate()
        compiled.stampCompiled(self.mayaNodes)
        compiled.startFrame=neg_adjustment
        
        if not status:
            raise StandardError('combine completed with errors: see script Editor for details')

        
        
class AudioNode(object):
    '''
    Single AudioNode handler for simple audio management object
    
    "Broadcast Wav" format now supported using specs from :
    https://tech.ebu.ch/docs/tech/tech3285.pdf

    '''
    def __init__(self, audioNode=None, filepath=None):
        self.__path=''
        self.__audioNode=None
        self.isLoaded=False  # if true we're only working on an audioPath, NOT an active Maya soundNode
        
        if not filepath:
            if audioNode:
                self.audioNode = audioNode
            else:
                self.audioNode = audioSelected()
            if self.audioNode:
                self.isLoaded=True
        else:
            #You can't load a wav more than once, if path is mapped to a current node, switch the class to that
            isAudioloaded = audioPathLoaded(filepath)
            if isAudioloaded:
                log.info('given audio filePath is already assigned to a Maya node, connecting to that : %s' % isAudioloaded[0])
                self.isLoaded=True
                self.audioNode=isAudioloaded[0]
            else:
                self.isLoaded=False
            self.path=filepath
    
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
                return self.audioNode==val.audioNode
            elif cmds.nodeType(val)=='audio':
                return self.audioNode==val
        else:
            return self.path==val.path

    def __ne__(self, val):
        return not self.__eq__(val)

    @property
    def path(self):
        if self.isLoaded and self.audioNode:
            return cmds.getAttr('%s.filename' % self.audioNode)
        else:
            return self.__path
    @path.setter
    def path(self,path):
        self.__path=path
    
    @property
    def audioNode(self):
        return self.__audioNode
    @audioNode.setter
    def audioNode(self, node):
        if node and cmds.objExists(node):
            self.isLoaded=True
            self.__audioNode=node
            
    @property
    def sampleRate(self):
        '''
        sample rate in milliseconds
        '''
        return audio_segment.AudioSegment.from_wav(self.path).frame_rate

    @property
    def sample_width(self):
        return audio_segment.AudioSegment.from_wav(self.path).sample_width
    
    @property
    def sample_bits(self):
        data={'1':8, '2':16, '3':24, '4':32}
        return data[str(audio_segment.AudioSegment.from_wav(self.path).sample_width)]
    
    @property
    def channels(self):
        return audio_segment.AudioSegment.from_wav(self.path).channels
    
    @property
    def startFrame(self):
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
        if self.isLoaded:
            cmds.setAttr('%s.offset' % self.audioNode, val)
           
    @property
    def startTime(self):
        '''
        this is in milliseconds
        '''
        if self.isLoaded:
            return (self.startFrame / r9General.getCurrentFPS()) * 1000
        return 0
    
    @startTime.setter
    def startTime(self, val):
        '''
        this is in milliseconds
        '''
        if self.isLoaded:
            cmds.setAttr('%s.offset' % self.audioNode, milliseconds_to_frame(val, framerate=None))

    @property
    def endTime(self):
        '''
        this is in milliseconds
        '''
        return (self.endFrame / r9General.getCurrentFPS()) * 1000
    
    @endTime.setter
    def endTime(self, val):
        '''
        this is in milliseconds
        '''
        if self.isLoaded:
            cmds.setAttr('%s.offset' % self.audioNode, milliseconds_to_frame(val, framerate=None))
    
    # BWAV support ##=============================================

    def isBwav(self):
        '''
        validate if the given source wav is a BWav or not
        '''
#        test = False
        binarymap = self.__get_chunkdata()
        if "bext" in binarymap:
            return True
#         fileIn = open(self.path, 'rb')
#         bufHeader = fileIn.read(512)
#         print bufHeader
#         # Verify that the correct identifiers are present
#         if (bufHeader[0:4] != "RIFF") or (bufHeader[12:16] != "fmt "):
#             #print("Input file not a standard WAV file")
#             if (bufHeader[12:16] == "bext"):
#                 test = True
#         fileIn.close()
#        return test
    
    def __readnumber(self, f):
        s = 0
        c = f.read(4)
        for i in range(4):
            s += ord(c[i]) * 256 ** i
        return s

    def __readchunk(self, f, data, level=0):
        '''
        inspect the binary chunk structure
        '''
        pos = f.tell()
        name = f.read(4)
        leng = self.__readnumber(f)
        totleng = leng + 8
        print "   "*level, name, "len-8 =%8d" % leng, "   start of chunk =", pos, "bytes"
        data[name]=(pos, leng)
        if name in ("RIFF", "list"):
            print "   "*level, f.read(4), "recursive sublist"
            sublen = leng - 4
            while sublen > 0:
                sublen -= self.__readchunk(f, data, level + 1)
            if sublen != 0:
                print "ERROR:", sublen
        else:
            f.seek(leng, 1)  # relative skip
        return totleng

    def __get_chunkdata(self, filedata=None):
        '''
        read the internal binary chunks of the wav file and return
        a dict of the binary map
        '''
        data={}  # pass by reference
        fopen=False
        if not filedata:
            filedata=open(self.path, "r")
            fopen=True
        self.__readchunk(filedata, data)
        if fopen:
            #print 'file closed'
            filedata.close()
        return data
        
    def bwav_getHeader(self):
        '''
        retrieve the BWav header info and push it into an internal dic
        that you can inspect self.bwav_HeaderData. This is designed to be cached
        against this instance of the audioNode object.
        Note that this code uses a binary seek to first find the starting chunk 
        in the binary file where the 'bext' data is written.
        
        .. note::
        
            We could, if we could ensure it was available, use ffprobe.exe (part of the ffmpeg project)
            This would also cover most media file formats including Mov, avi etc 
            There is coverage for this in this module getMediaFileMetaData() does just that
        '''
        with open(self.path, 'r') as filedata:
            binarymap = self.__get_chunkdata(filedata)
            if not "bext" in binarymap:
                log.info('Audio file is not a formatted BWAV')
                return

            self.bwav_HeaderData = {'ChunkSize' : 0,
                        'Format' : '',
                        'Subchunk1Size' : 0,
                        'AudioFormat' : 0,
                        'BitsPerSample' : 0,
                        'Description' : '',
                        'Originator' : '',
                        'OriginatorReference' : '',
                        'OriginationDate' : '',
                        'OriginationTime' : '',
                        'TimeReference' : 0,
                        'TimeReferenceHigh' : 0,
                        'BextVersion' : 0
                }

            chunkPos = int(binarymap['bext'][0]) + 8  # starting position in the binary to start reading the 'bext' data from
            filedata.seek(0)
            bufHeader = filedata.read(chunkPos+360)
            #print 'buffdata:', filedata.tell(), bufHeader

            # Parse fields
            self.bwav_HeaderData['ChunkSize'] = struct.unpack('<L', bufHeader[4:8])[0]
            self.bwav_HeaderData['Format'] = bufHeader[8:12]
            self.bwav_HeaderData['InternalFormat'] = bufHeader[12:16]
            self.bwav_HeaderData['Subchunk1Size'] = struct.unpack('<L', bufHeader[16:20])[0]
            
            # bwav chunk data
            self.bwav_HeaderData['Description']=struct.unpack('<256s', bufHeader[chunkPos:chunkPos+256])[0].replace('\x00','')
            self.bwav_HeaderData['Originator']=struct.unpack('<32s', bufHeader[chunkPos+256:chunkPos+288])[0].replace('\x00','')
            self.bwav_HeaderData['OriginatorReference']=struct.unpack('<32s', bufHeader[chunkPos+288:chunkPos+320])[0].replace('\x00','')
            self.bwav_HeaderData['OriginationDate']=struct.unpack('<10s', bufHeader[chunkPos+320:chunkPos+330])[0].replace('\x00','')
            self.bwav_HeaderData['OriginationTime']=struct.unpack('<8s', bufHeader[chunkPos+330:chunkPos+338])[0].replace('\x00','')
            self.bwav_HeaderData['TimeReference'] = struct.unpack('<L', bufHeader[chunkPos+338:chunkPos+342])[0]
            self.bwav_HeaderData['TimeReferenceHigh'] = struct.unpack('<L', bufHeader[chunkPos+342:chunkPos+346])[0]
            self.bwav_HeaderData['BextVersion'] = struct.unpack('<L', bufHeader[chunkPos+346:chunkPos+350])[0]

        #print self.bwav_HeaderData
        return self.bwav_HeaderData
        
    def bwav_timecodeMS(self):
        '''
        read the internal timecode reference form the bwav and convert that number into milliseconds
        '''
        if not self.isBwav():
            raise StandardError('audioNode is not in BWav format')
        if not hasattr(self, 'bwav_HeaderData'):
            self.bwav_getHeader()
        return float(self.bwav_HeaderData['TimeReference']) / float(self.sampleRate) * 1000.0
    
    def bwav_timecodeReference(self):  # frameRate=29.97):
        '''
        internal timeReference in the bwav
        '''
        if not hasattr(self, 'bwav_HeaderData'):
            self.bwav_getHeader()
        return float(self.bwav_HeaderData['TimeReference'])
    
    def bwav_timecodeFormatted(self, smpte=True, framerate=None):
        '''
        convert milliseconds into timecode

        :param smpte: format the timecode HH:MM:SS:FF where FF is frames, else milliseconds
        :param framerate: when using smpte this is the framerate used in the FF block
        '''
        return milliseconds_to_Timecode(self.bwav_timecodeMS(), smpte=smpte, framerate=framerate)

    def bwav_sync_to_Timecode(self, offset=0):
        '''
        given that self is a Bwav and has timecode reference, sync it's position
        in the Maya timeline to match
        
        :param offset: offset to apply to the internal timecode of the given wav's
        '''
        if self.isLoaded and self.isBwav():
            #print milliseconds_to_Timecode(self.bwav_timecodeMS(), smpte=True, framerate=None)
            #print milliseconds_to_frame(self.bwav_timecodeMS(), framerate=None)
            self.startFrame=milliseconds_to_frame(self.bwav_timecodeMS()) + offset
      

    # Bwav end =========================================================
    
    def isValid(self):
        if self.isLoaded:
            return (self.audioNode and cmds.objExists(self.audioNode)) or False
        else:
            return os.path.exists(self.path)
    
    def delete(self):
        if self.isLoaded:
            cmds.delete(self.audioNode)
            
    def offsetTime(self, offset):
        if self.isLoaded:
            if r9Setup.mayaVersion() == 2011:
                #Autodesk fucked up in 2011 and we need to manage both these attrs
                cmds.setAttr('%s.offset' % self.audioNode, self.startFrame + offset)
                cmds.setAttr('%s.endFrame' % self.audioNode, self.length + offset)
            else:
                cmds.setAttr('%s.offset' % self.audioNode, self.startFrame + offset)
    
    def importAndActivate(self):
        '''
        If self was instantiated with filepath then this will import that wav
        into Maya and activate it on the timeline. Note that if there is already
        an instance of a sound node in Maya that points to this path them the 
        class will bind itself to that node.
        
        >>> #example of use:
        >>> audio = r9Audio.AudioNode(filepath = 'c:/my_audio.wav')
        >>> audio.importAndActivate()
        '''
        a=cmds.ls(type='audio')
        cmds.file(self.path, i=True, type='audio', options='o=0')
        b=cmds.ls(type='audio')
 
        if not a == b:
            self.audioNode = (list(set(a) ^ set(b))[0])
        else:
            matchingnode = [audio for audio in a if cmds.getAttr('%s.filename' % audio) == self.path]
            if matchingnode:
                self.audioNode = matchingnode[0]
            else:
                log.warning("can't find match audioNode for path : %s" % self.path)
                return
        self.isLoaded=True
        self.setActive()
        
    def setActive(self):
        '''
        Set sound node as active on the timeSlider
        '''
        if self.isLoaded:
            gPlayBackSlider = mel.eval("string $temp=$gPlayBackSlider")
            cmds.timeControl(gPlayBackSlider, e=True, ds=1, sound=self.audioNode)

    def getLengthFromWav(self):
        '''
        This uses the wav itself bypassing the Maya handling, why?
        In maya.standalone the audio isn't loaded correctly and always is of length 1!
        '''
        with contextlib.closing(wave.open(self.path,'r')) as f:
            frames=f.getnframes()
            rate=f.getframerate()
            duration=frames/float(rate)
            return (duration) * r9General.getCurrentFPS()
                    
    def setTimeline(self):
        if self.isLoaded:
            cmds.playbackOptions(min=int(self.startFrame), max=int(self.endFrame))

    def mute(self, state=True):
        if self.isLoaded:
            cmds.setAttr('%s.mute' % self.audioNode, state)

    def openAudioPath(self):
        path=self.path
        if path and os.path.exists(path):
            r9General.os_OpenFileDirectory(path)
    
    def formatAudioNode_to_Path(self):
        '''
        rename the AudioNode so it ties to the wav name
        '''
        try:
            cmds.rename(self.audioNode, r9Core.nodeNameStrip(os.path.splitext(os.path.basename(self.path))[0]))
        except:
            if cmds.referenceQuery(self.audioNode,inr=True):
                log.info('failed to Rename Referenced Audio Node : %s' % self.audioNode)
            else:
                log.info('failed to Rename Audio node : %s' % self.audioNode)
        
    def lockTimeInputs(self, state=True):
        '''
        lock the audio in time so it can't be accidentally shifted
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
        Used by the compiler - stamp the audioNodes from which this audio
        track was compiled from
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
        self.__bwav_reference=None
        
    @classmethod
    def show(cls):
        cls()._showUI()
    
    def _showUI(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        cmds.window(self.win, title=self.win, widthHeight=(400, 180))
        cmds.columnLayout('uicl_audioMain',adjustableColumn=True)
        cmds.separator(h=15, style='none')
        cmds.separator(h=15, style='in')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 90), (3, 100)])
        cmds.button(label='<< Offset',
                    ann='Nudge selected Audio Backwards',
                    command=partial(self.offsetSelectedBy,'negative'))
        cmds.floatField('AudioOffsetBy', value=10)
        cmds.button(label='Offset >>',
                    ann='Nudge selected Audio Forwards',
                    command=partial(self.offsetSelectedBy,'positive'))
        cmds.setParent('..')
        cmds.separator(h=15, style='in')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 200), (2, 90)])
        cmds.button(label='Offset Range to Start at:',
                    ann='offset the selected range of audionodes such that they start at the given frame',
                    command=self.offsetSelectedTo)
        cmds.floatField('AudioOffsetToo', value=10)
        cmds.setParent('..')
        cmds.separator(h=15, style='none')
        cmds.frameLayout(label='Broadcast Wav support', cll=True, borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=5, style='none')
        cmds.text(label="NOTE: These will only run if the audio is\nin the Bwav format and has internal timecode data.")
        cmds.separator(h=10, style='none')
        cmds.button(label='Sync Bwavs to Internal Timecode',
                    ann='Sync audio nodes to their originally recorded internal timecode reference',
                    command=self.sync_bwavs)
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 100)], columnSpacing=[(2,20)])
        cmds.button(label='Set Timecode Ref',
                    ann="Set the audio node to use as the reference timecode so all other become relative to this offset",
                    command=self.__uicb_setReferenceBwavNode)
        cmds.text('bwavRefTC', label='No Reference Set')
        cmds.setParent('..')
        cmds.button(label='Sync Bwavs Relative to Selected',
                    ann="Sync audio nodes via their internal timecodes such that they're relative to that of the given reference",
                    command=self.sync_bwavsRelativeToo)
        cmds.setParent('uicl_audioMain')
        cmds.separator(h=10, style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                             c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
        cmds.showWindow(self.win)
        cmds.window(self.win, e=True, widthHeight=(290, 300))

    def __uicb_cacheAudioNodes(self,*args):
        self.audioHandler=AudioHandler()
        
    def offsetSelectedBy(self,direction,*args):
        self.audioHandler=AudioHandler()
        offset=cmds.floatField('AudioOffsetBy', q=True,v=True)
        if direction == 'negative':
            offset=0-offset
        self.audioHandler.offsetBy(float(offset))
           
    def offsetSelectedTo(self,*args):
        self.audioHandler=AudioHandler()
        offset=cmds.floatField('AudioOffsetToo', q=True,v=True)
        self.audioHandler.offsetTo(float(offset))
    
    def __uicb_setReferenceBwavNode(self, *args):
        '''
        set the internal reference offset used to offset the audionode. 
        
        .. note:
                If you pass this a bwav then it caches that bwav for use as the offset. If you 
                pass it a node, and that node has the timecode attrs, then it caches the offset itself.
        '''
        selected=cmds.ls(sl=True, type='audio')
        self.__bwav_reference=None
        self.__cached_tc_offset=None
        if selected:
            if not len(selected)==1:
                log.warning("Please only select 1 piece of Audio to use for reference")
                return
            reference=AudioNode(selected[0])
            if reference.isBwav():
                self.__bwav_reference=selected[0]
                cmds.text('bwavRefTC', edit=True,
                          label='frame %s == %s' % (reference.startFrame,reference.bwav_timecodeFormatted()))
            else:
                raise IOError("selected Audio node is NOT a Bwav so can't be used as reference")
        else:
            selected = cmds.ls(sl=True)
            if len(selected)==1:
                relativeTC = Timecode.getTimecode_from_node(cmds.ls(sl=True)[0])
                actualframe = cmds.currentTime(q=True)
                self.__cached_tc_offset = actualframe - timecode_to_frame(relativeTC)
                cmds.text('bwavRefTC', edit=True,
                          label='frame %s == %s' % (cmds.currentTime(q=True), relativeTC))
            else:
                log.warning("No reference audio track selected for reference")
            return
       
    def sync_bwavsRelativeToo(self, *args):
        self.audioHandler=AudioHandler()
        if self.__bwav_reference:
            self.audioHandler.bwav_sync_to_Timecode(relativeToo=self.__bwav_reference)
        elif self.__cached_tc_offset:
            self.audioHandler.bwav_sync_to_Timecode(offset=self.__cached_tc_offset)
        else:
            raise IOError("No timecode reference currently set")
            
    def sync_bwavs(self, *args):
        self.audioHandler=AudioHandler()
        self.audioHandler.bwav_sync_to_Timecode()
            
def __ffprobeGet():
    '''
    I don not ship ffprobe as it's lgpl license and fairly large, however
    if you download it for use with the getMediaFileInfo then this is where it goes
    Red9/packages/ffprobe.exe
    '''
    expectedPath=os.path.join(r9Setup.red9ModulePath(),'packages','ffprobe.exe')
    if os.path.exists(expectedPath):
        return expectedPath
    else:
        log.warning('ffprobe.exe not currently installed, aborting')
    
def getMediaFileMetaData(filepath, ffprobePath=None):
    '''
    This function is capable of returning most metaData from mediaFiles, the return
    is in a json format so easily accessed.
    :param ffprobePath: if not given the code will asume that ffprobe.exe has been 
        dropped into teh Red9/packages folder, else it'll use the given path
        
    .. note::
        
        This is a stub function that requires ffprobe.exe, you can download from 
        http://www.ffmpeg.org/download.html it's part of the ffmpeg tools.
        Once downloaded drop it here Red9/pakcages/ffprobe.exe
        This inspect function will then be available to use for many common media formats.
        More info: http://www.ffmpeg.org/ffprobe.html
    '''
    import subprocess
    pipe = subprocess.Popen([__ffprobeGet(),'-v','quiet',
                                    '-print_format','json',
                                  '-show_format','-show_streams',
                                     os.path.normpath(filepath)], stdout=subprocess.PIPE).communicate()
    pipe = pipe[0].replace('\r', '')
    return eval(pipe.replace('\n', ''))


