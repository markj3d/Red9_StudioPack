'''
..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com
    
    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk
    

This is the Audio library of utils used throughout the modules


'''
import maya.cmds as cmds
import maya.mel as mel
import os
import struct
import math

import Red9.startup.setup as r9Setup
import Red9_General as r9General
import Red9.startup.setup as r9Setup

import wave
import contextlib
from ..packages.pydub.pydub import audio_segment

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)



def milliseconds_to_Timecode(milliseconds, smpte=True, framerate=None):
        '''
        convert milliseconds into correctly formatted timecode
        
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
    actual = int(data[0]) * 3600000
    actual += int(data[1]) * 60000
    actual += int(data[2]) * 1000
    if smpte:
        actual += (int(data[3]) * 1000) / float(framerate)
    else:
        actual += int(data[3])
    return actual


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
    I wanted to keep things simple in the base class
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
    for audio in cmds.ls(type='audio'):
        if cmds.getAttr('%s.filename' % audio):
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
    process on multiple audio nodes
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
    
    def getOverallRange(self, ms=False):
        '''
        return the overall frame range of the given audioNodes (min/max)
        '''
        maxV = self.audioNodes[0].startFrame  # initialize backwards
        minV = self.audioNodes[0].endFrame  # initialize backwards
        for a in self.audioNodes:
            audioOffset=a.startFrame
            audioEnd=a.endFrame  # why the hell does this always come back 1 frame over??
            if audioOffset<minV:
                minV=audioOffset
            if audioEnd>maxV:
                maxV=audioEnd
        #print 'min : ', minV
        #print 'max : ', maxV
        return (minV, maxV)
        
    def setTimelineToAudio(self, audioNodes=None):
        '''
        set the current TimeSlider to the extent of the given audioNodes
        '''
        frmrange=self.getOverallRange()
        cmds.playbackOptions(min=int(frmrange[0]), max=int(frmrange[1]))
        
    def muteSelected(self, state=True):
        for a in self.audioNodes:
            a.mute(state)
            
    def deleteSelected(self):
        for a in self.audioNodes:
            a.delete()
    
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
        compiled=AudioNode.importAndActivate(filepath)
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

    def __init__(self, audioNode=None):
        self.audioNode = audioNode
        if not self.audioNode:
            self.audioNode = audioSelected()
    
    def __repr__(self):
        if self.audioNode:
            return "%s(AudioNode InternalAudioNodes: '%s')" % (self.__class__, self.audioNode)
        else:
            return "%s(AudioNode NO AudioNodes: )" % self.__class__
    
    def __eq__(self, val):
        if isinstance(val, AudioNode):
            if self.audioNode==val.audioNode:
                return True
        elif cmds.nodeType(val)=='audio':
            if self.audioNode==val:
                return True
            
    def __ne__(self, val):
        return not self.__eq__(val)

    @property
    def path(self):
        return cmds.getAttr('%s.filename' % self.audioNode)
        
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
        return cmds.getAttr('%s.offset' % self.audioNode)
    
    @startFrame.setter
    def startFrame(self, val):
        cmds.setAttr('%s.offset' % self.audioNode, val)
        
    @property
    def endFrame(self):
        '''
        Note in batch mode we calculate via the Wav duration
        NOT the Maya audioNode length as it's invalid under batch mode!
        '''
        if not cmds.about(batch=True):
            return cmds.getAttr('%s.endFrame' % self.audioNode)  # why the hell does this always come back 1 frame over??
        else:
            return self.getLengthFromWav() + self.startFrame
        
    @property
    def startTime(self):
        '''
        this is in milliseconds
        '''
        return (self.startFrame / r9General.getCurrentFPS()) * 1000
    
    @property
    def endTime(self):
        '''
        this is in milliseconds
        '''
        return (self.endFrame / r9General.getCurrentFPS()) * 1000
    
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
            print 'file closed'
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


    # Bwav end =========================================================
    
    def isValid(self):
        return (self.audioNode and cmds.objExists(self.audioNode)) or False
    
    def delete(self):
        cmds.delete(self.audioNode)
            
    def offsetTime(self, offset):
        if r9Setup.mayaVersion() == 2011:
            #Autodesk fucked up in 2011 and we need to manage both these attrs
            cmds.setAttr('%s.offset' % self.audioNode, self.startFrame + offset)
            cmds.setAttr('%s.endFrame' % self.audioNode, self.length + offset)
        else:
            cmds.setAttr('%s.offset' % self.audioNode, self.startFrame + offset)
    
    @staticmethod
    def importAndActivate(path):
        a=cmds.ls(type='audio')
        cmds.file(path, i=True, type='audio', options='o=0')
        b=cmds.ls(type='audio')
        if not a == b:
            audio = AudioNode(list(set(a) ^ set(b))[0])
        else:
            matchingnode = [audio for audio in a if cmds.getAttr('%s.filename' % audio) == path]
            if matchingnode:
                audio = AudioNode(matchingnode[0])
            else:
                return
        audio.setActive()
        return audio
        
    def setActive(self):
        '''
        Set sound node as active on the timeSlider
        '''
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
        cmds.playbackOptions(min=int(self.startFrame), max=int(self.endFrame))

    def mute(self, state=True):
        cmds.setAttr('%s.mute' % self.audioNode, state)

    def openAudioPath(self):
        path=self.path
        if path and os.path.exists(path):
            r9General.os_OpenFileDirectory(path)
            
    @property
    def isCompiled(self):
        '''
        return if the audioNode in Maya was generated via the compileAudio
        call in the AudioHandler.
        '''
        if cmds.attributeQuery('compiledAudio', exists=True, node=self.audioNode):
            return True

    def stampCompiled(self, audioNodes):
        '''
        Used by the compiler - stamp the audioNodes from which this audio
        track was compiled from
        '''
        cmds.addAttr(self.audioNode, longName='compiledAudio', dt='string')
        cmds.setAttr('%s.compiledAudio' % self.audioNode, ','.join(audioNodes), type="string")
                


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


