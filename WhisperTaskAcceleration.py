"""
    __author__    = "Waverly Edwards"
    __copyright__ = "Copyright (C) 2022 Waverly Edwards"
    __license__   = "Public Domain"
    __version__   = "0.75"
    __NOTE__      = "When you use this code, give me (Waverly Edwards) credit."
"""

"""
    Purpose:  Transcribe an audio or video file, using multiprocessing to accelerate processing time.

    This program provides a pronounced acceleration for transcribing audio using Whisper without changing Whisper, through multiprocessing. The user chooses the number of processes to run in parallel (forked), up to the number of available CPUs and the input file is chunked\fragmented into the number of processes.  By consuming and processing each audio chunk in parallel, we obtain our dramatic acceleration.

    See readme for caveats.

    Whisper was trained on and uses 30 second windows of audio, so chunks shorter than 30 seconds are inefficiently processed.
    Developed a "limiter" method that identifies when the number of desired processes will cause the fragment length to go below 30 seconds.
"""


"""
    Prevent AudioSegment module from complaining about not finding ffmpeg.
    It is already in environment variables path, but it complains anyway.
    Addiing the path before importing resolves the noisy warning
"""
import os

ffmpeg_path = "/usr/local/bin/" # use the path to your ffmpeg executable
os.environ["PATH"] += os.pathsep + ffmpeg_path

from   pydub import AudioSegment
from   pydub.utils import make_chunks
from   timeit import default_timer as timer
from   multiprocessing import Process, Queue, set_start_method, Manager
from   pathlib import Path
from   whisper.utils import write_srt
import whisper
import multiprocessing, time
import ffmpeg, json, subprocess


"""
    When launching the parallel processes from another process, you must fork
    or there will be a runtime error because of a looping back to the ___MAIN___ file.
    ENABLE MULITPLE PARALLEL PROCESSES WHILE ALSO RESOLVING THE RUNTIME ERROR
     
    set_start_method('fork') # MUST HAVE WHEN CALLING FROM PYTHONKIT
"""

set_start_method('fork') # MUST HAVE WHEN CALLING FROM PYTHONKIT


#   ___ UTILITY AND TESTING METHODS ___

def useSampleAudioVideoFile():
    # could be a video file but we will use an audio file here
    targetPath = "/Users/wedwards/Transcribe_Input/veryshortfile.wav" # file dureation is less than 30 seconds
    targetPath = "/Users/wedwards/Transcribe_Input/DonQuixote_OneHour.mp3"
    targetPath = "/Users/wedwards/Transcribe_Input/5 Minute_Test.wav"
    return targetPath


def useSampleOutputDirectory():
    return "/Users/wedwards/Transcribe_Temp/"
    
    
def useSampleInputImage():
    return "/Users/wedwards/Transcribe_Input/Wise Waverly Wolf - Overlay.png"
   

def add_ffmpeg_path():
    ffmpeg_path = "/usr/local/bin/" #/usr/local/bin"
    os.environ["PATH"] += os.pathsep + ffmpeg_path
    

def executeWhisperCLI(modelName, filePath, outputDir, threadCount, doCliTimer):
    gtime       = "/usr/local/bin/gtime" #CHANGE to reflect executable location of time or gtime
    gtimeArg    = "-v" # verbose timer information
    whisper     = "/Library/Frameworks/Python.framework/Versions/3.10/bin/whisper" #CHANGE to reflect executable location
    model       = "--model"
    targLang    = "English" #transcribing only English.  Could do others
    language    = "--language"
    outDir      = "--output_dir"
    fp16        = "--fp16"
    useGPU      = "False" # "False" is for CPU
    threads     = "--threads"
    thredStr    = str(threadCount)
    task        = "--task"
    transcribe  = "transcribe"
    translate   = "translate"
    timerArgs   = [gtime,gtimeArg]
    whisperArgs = [whisper, filePath, model, modelName, language, targLang, outDir, outputDir, fp16, useGPU, threads, thredStr, task, transcribe]
    processArgs = whisperArgs
    
    """
        https://askubuntu.com/questions/53444/how-can-i-measure-the-execution-time-of-a-terminal-process
        Are you using this command on Mac OS? If yes, you can brew install gnu-time and use the command gtime instead of time
        This works but you much change "gtime" and "whisper" variables to reflect the executable locations

        if ( doCliTimer == True ):
            processArgs = timerArgs + whisperArgs
        else:
            processArgs = whisperArgs
    """
    
    if ( doCliTimer == True ):
        processArgs = timerArgs + whisperArgs
    else:
        processArgs = whisperArgs

    result = subprocess.run(processArgs) #subprocess.run(processArgs, stdout=subprocess.PIPE)
    return result
   

def testCLI(threadsToUse):
    modelName   = "tiny.en"
    audioPath   = useSampleAudioVideoFile()
    outputDir   = useSampleOutputDirectory()
    useCliTimer = True
    start       = timer()
    result      = executeWhisperCLI( modelName, audioPath, outputDir, threadsToUse, useCliTimer)
    end         = timer()
    elapsed     = (end - start)
    print(result.stdout)
    print("Model test completed in %s seconds, (H:M:S) %s \n\n" %( elapsed, formatTime(elapsed) ))
    #whisper {audioPath} --model {modelName} --language {English} --output_dir {OUTPUT_DIR} --fp16 {useGPU} --threads {threadCount} --task {transcribe|translate}


def displayAudioFileInfo(filePath):
    root, fileExt      = os.path.splitext(filePath)
    fileExt            = fileExt.lstrip(".") # we dont need or want the "." for the extension
    fileDir, fileName  = os.path.split(filePath) # fileName = os.path.basename(filePath)
    audioSegment       = AudioSegment.from_file(filePath, fileExt)
    print(" Root: %s\n FileName: %s\n FileExt: %s\n Duration: %s" % (root, fileName, fileExt, audioSegment.duration_seconds))
    print("___________\n\n")
    print(" FileDir: %s\n FileName: %s\n FileExt: %s\n Duration:%s\n" % (fileDir, fileName, fileExt, audioSegment.duration_seconds))


def downloadModels():
    # These model will be downloaded if you dont have them
    models = ["tiny.en","base.en","small.en","medium.en"]
    for modelName in models:
        _ = whisper.load_model(modelName)
        

def makeStaticVideo(audioInput, imageInput, outputFile):
    """
        Make a video using an audio track and a single looped image
        we can use this video with VLC and an SRT file for subtitle
        synchronization testing
        https://stackoverflow.com/questions/64375367/python-convert-mp3-to-mp4-with-static-image
    """
    image    = ffmpeg.input(imageInput, loop='1', framerate='1')
    audio    = ffmpeg.input(audioInput)
    output   = ffmpeg.output(image,audio, outputFile,
#    map     = "0:v", # cant have two maps here
    map      = "1:a",
    r        = "10",
    vf       = "scale='iw-mod(iw,2)':'ih-mod(ih,2)',format=yuv420p",
    movflags = "+faststart",
    shortest = None,
    fflags   = "+shortest",
    max_interleave_delta = "100M")
    output.overwrite_output().run()
#    output.global_args('-report').overwrite_output().run() #change environnemt variable to poin to desired log location


#   ___ SUPPORTING METHODS ___

def writeTestfile(filePath, output_dir, usingSegments, chunkSeconds):
    audio_basename    = Path(filePath).stem
    transciptSegments = repairTranscriptSegments(usingSegments,chunkSeconds)
    with open(Path(output_dir) / (audio_basename + ".srt"), "w", encoding="utf-8") as outFile:
        write_srt(transciptSegments, outFile)
        outFile.close()
    with open(Path(output_dir) / (audio_basename + ".json"), "w", encoding="utf-8") as outFile:
        json.dump(transciptSegments, outFile)
        outFile.close()
    with open(Path(output_dir) / (audio_basename + ".txt"), "w", encoding="utf-8") as outFile:
        for segment in transciptSegments:
            print(segment['text'].strip(), file=outFile, end=" ", flush=True)
        outFile.close()


def writeTextFile(filePath, output_dir, text):
    audio_basename = Path(filePath).stem  # save JSON using the same base name
    with open(Path(output_dir) / (audio_basename + "_.txt"), "w", encoding="utf-8") as outFile:
        print(text, file=outFile, flush=True)


#    ____ MAIN METHODS  ___

def loadWhisperModel(modelName):
    global gWhisperModel    # This global is important
    gWhisperModel = whisper.load_model(modelName)
    
    
def loadDefaultWhisperModel():
    modelName = "base.en"
    loadWhisperModel(modelName)
    print("Initializing... loading model \"%s\"" % (modelName))


def repairTranscriptSegments(transcript, chunkSeconds):
    """
        We are repairing the timeline here.

        If we are just transcibing, repair of the timeline is not needed because
        we would simply not use the timeline information but if we want to develop
        an SRT, VTT or some other tool that makes use of timing, this is required.

        We expect that for every new audio chunk, the segment information will be
        re-initialized.  We concatenated each chunk's segments and determining an
        offset amount for each chunk, then adjust the "start" and "end" segments,
        so the timestamps are contiguous.

        "chunkSeconds" is the length of each chunk, so we know that the segment["end"]
        cant be beyond this. After repairing the timeline, from the concatenated chunks
        we can use the built-in functions to write TEXT, SRT and VTT files.
    """
    
    chunkCount = 0
    for segIndex, segment in enumerate(transcript):
        if (segment["id"] == 0):
            chunkCount += 1
            if (chunkCount > 1):
                prevSegment = transcript[segIndex-1] # look back to previous segment
                if (prevSegment["end"] > chunkSeconds): # impossible to be greater than chunk length
                    transcript[segIndex-1]["end"] = chunkSeconds

    chunkCount = 0 # re-initialize
    adjustTime = 0.0
    for segIndex, segment in enumerate(transcript):
        segID = segment["id"]
        if (segID == 0):
            chunkCount += 1
            adjustTime  = ((chunkCount - 1) * chunkSeconds)
                
#        if (segID == 0)   : segment["text"] += "@@@@@" # TESTING: This is a marker so we know where each new segment is located
        segment["start"] += adjustTime
        segment["end"]   += adjustTime
        segment["id"]     = segIndex # repair the sequence, so the IDs are now contiguous
    return transcript
    

def formatTime(seconds):
    # Easy way to get formatted time form seconds
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def removeTempFiles(filePathArray):
    # Remove the temporary files created
    for _, tempFile in enumerate(filePathArray):
        if os.path.exists(tempFile):
          os.remove(tempFile) #test before trying to delete just in case


def transcribeQueuedFile(idx, filePath, shared_list):
    # Transcribe the file and put the text
    # and segments into a queue for later use
    start    = timer()
    result   = gWhisperModel.transcribe(filePath,  fp16=False) # prevent complaint with fp16=False on CPU
    end      = timer()
    elapsed  = (end - start)
    _,name   = os.path.split(filePath)
    elapsStr = "{:0>3.3f}".format(elapsed)
    print("Completed:        %s in %s seconds" %(name, elapsStr)) # for testing purposes
    
    """
        ------ Hard-won, very painful lesson about shared memory here
        Note this is an incoming list\array of dictionaries [{"idx": idx, "text": "", "segments": []}]
        https://docs.python.org/2/library/multiprocessing.html#multiprocessing.managers.SyncManager.list
    """
    
    tempDict             = shared_list[idx]
    tempDict["text"]     = result["text"]
    tempDict["segments"] = result["segments"]
    shared_list[idx]     = tempDict # <<-- ***MUST REASSIGN or memory will not update.***  See note
    
    """
        Queues were originally working perfectly then without warning, they began to
        producing zombie processes and the program would not complete.
        
        Also, on macOS, you cant get the queue size because "qsize" is "not implemented", so you cant test the queue.
        https://stackoverflow.com/questions/65609529/python-multiprocessing-queue-notimplementederror-macos
        
        My alternative was to use a shared memory list.  More specifically, a list of dictionaries.
        
        For posterity, here is what does not work.
        
        shared_list[idx].update(dictToUpdate)       <- shared memory does not update
        shared_list[idx]["text"] = result["text"]   <- shared memory does not update
        
        This works
        shared_list.append({"idx": idx, "text": text, "segments":segm})  <- This works but...
        
        Appending DOES write back to shared memory but we must start with an empty list and
        we must manage the order of the data by post-processing because the method is pretty
        much guaranteed to append out of order, depending upon how long the transcribe process
        takes.  Its not horrible, we would just need to sort the dictionaries by the "idx" key
        to get them in the desired order.
        
        According to the Python docs, this works and it is working in this program
        
        https://docs.python.org/2/library/multiprocessing.html#multiprocessing.managers.SyncManager.list
        
        "multiprocessing.managers.ListProxy"
        
        "Note: Modifications to mutable values or items in dict and list proxies will not be propagated
        through the manager, because the proxy has no way of knowing when its values or items are modified.
        To modify such an item, you can re-assign the modified object to the container proxy:"
    """
    
    
def transcribeParallel(filePaths):
    # Create new transcription processes
    # that will be executed in parallel
    processes   = []
    manager     = Manager()
    shared_list = manager.list()

    for idx, filePath in enumerate(filePaths):
        tempDict = {"idx": idx, "text": "", "segments": []} # pre-populat the list with dictionaries
        shared_list.append(tempDict) # ensure the array index exist, which is already in order
        process = Process(target=transcribeQueuedFile, args=(idx, filePath, shared_list))
        processes.append(process)

    for p in processes:
        p.start()

    for p in processes:
        p.join()
    
    fullText     = ""
    fullSegments = []
    
    for index, itemDict in enumerate(shared_list):
        fullText += itemDict["text"]
        fullSegments.extend(itemDict["segments"]) #using EXTEND is the correct outcome here, **NOT** APPEND.
    return (fullText,fullSegments)


def overrideMaxProcs(inputFileLen, requestedProcs):
    """
        Whisper's sliding window is 30 seconds long.
        Override the number of process requests if the
        request forces the chunk size to less than 31 seconds
    """
    oneSecMillis    = 1000 # 1000 milliseconds in a second
    thirtySeconds   = 30 * oneSecMillis
    minChunkLength  = 31.0
    chunkSeconds    = ((inputFileLen / requestedProcs) / oneSecMillis)
    targetProcCount = max( int(inputFileLen / thirtySeconds), 1) # if input < 30 secs, leave it alone
    newChunkSecons  = ((inputFileLen / targetProcCount) / oneSecMillis)
    if (chunkSeconds < minChunkLength):
        print("Audio length is %s " %(inputFileLen / oneSecMillis))
        print("Chunks should be greater than 30.0 seconds.")
        print("The [%s] requested processes would make the chunks %s seconds." %(requestedProcs, chunkSeconds))
        print("Overriding the number of processes from [%s] to [%s], with a chunk size of %s seconds.\n" %(requestedProcs, targetProcCount, newChunkSecons))
    else:
        targetProcCount = requestedProcs
    return targetProcCount


def transcribeChunks(modelName, filePath, tempDirectory, maxProcesses):
    """
        Create chunked copies of the original audio files that are equal to
        the number of forked processes we will generate.  The number of
        forks will be no more than the number of CPUs/Cores on the machine.
        Each process will transcribe a chunk in parallel, then concatenate
        each of the results
    """
    internal_maxProcs = maxProcesses
    actualCPUs        = multiprocessing.cpu_count()
    oneSecMillis      = 1000 # 1000 milliseconds in a second
    overUtilized      = False
    
    if (internal_maxProcs <= 0):
        internal_maxProcs  = 1
    if (internal_maxProcs  > actualCPUs):
        internal_maxProcs  = actualCPUs # zero point in creating more processes than CPUs
        overUtilized       = True
        
    request = "Requested [%s] processes. Reducing number of processes to be no more than the number of CPUs/Cores, which are [%s]"
    if (overUtilized == True):
        print(request % (maxProcesses, actualCPUs))
        
    # Consume the input file and convert it into segments
    root, fileExt      = os.path.splitext(filePath)
    fileExt            = fileExt.lstrip(".") # we dont need or want the "." for the extension
    fileDir, fileName  = os.path.split(filePath)
    audioSegment       = AudioSegment.from_file(filePath, fileExt)
    inFileMillisecs    = len(audioSegment) # duration of input file in milliseconds
    oldInternMaxProcs  = internal_maxProcs
    internal_maxProcs  = overrideMaxProcs(inFileMillisecs, internal_maxProcs) # overrides process request depending on circumstances -- can comment out to unrestrict
    chunk_length_ms    = (inFileMillisecs / internal_maxProcs)# pydub calculates in millisec [[DO NOT TRUNCATE TO INTEGER]]
    chunks             = make_chunks(audioSegment, chunk_length_ms) #Make chunks of the audio
    chunkCountStr      = str(len(chunks))
    internalFormat     = "wav" # mp3, wav (mp3 is 300x (or more) slower because of the conversion which saves space but the time tradeoff is not justified)
    file_seconds       = (inFileMillisecs / oneSecMillis)
    chunk_seconds      = (len(chunks[0]) / oneSecMillis)
    tempFileArray      = []
    
    # Write the chunks to disk as temporary files for processing
    print('starting')
    start = timer()
    for index, chunk in enumerate(chunks):
        chunk_name = "chunk{:03d}.".format(index + 1) + internalFormat
        display    = "Exporting:        {:03d} of ".format(index + 1) + chunkCountStr + " -> "
        tempFile   = tempDirectory + chunk_name
        print (display, chunk_name)
        chunk.export(tempFile, format=internalFormat)
        tempFileArray.append(tempFile)
    end = timer()
    
    print("*---------------")
    print("Target File Time: %s seconds," %(file_seconds), "H:M:S %s" %(formatTime(file_seconds)))
    print("Chunk Seconds:    %s" %(chunk_seconds))
    print("Processes Used:   %s" %(internal_maxProcs), "(for %s chunks)" %(chunkCountStr))
    print("Built in CPUs:    %s" %(actualCPUs))
    print("Chunk Build Time: %s" %(end - start))
    print("*---------------")

    start    = timer()
    allText  , allSegments = transcribeParallel(tempFileArray)
    end      = timer()
    elapsed  = (end - start)
    convRate = file_seconds / elapsed
    finalStr = allText.encode('utf-8')      # Resolve Python exception: 'ascii' codec can't encode character '\ufffd' in position 2122:
    elapsStr = "{:0>3.3f}".format(elapsed)  # leading zeroes, three decimal places
    cpusStr  = "{:03d} on ".format(internal_maxProcs) + str(actualCPUs) + "CPUs" # leading zeroes
    convStr  = "{:0>3.3f}".format(convRate) # leading zeroes, three decimal places
    
    print("*---------------")
    actionStr = "!--[Transcribe]   TargetDuration: %s seconds - %s(H:M:S), ChunksProcessd: %s, Model: %s, Completed: %s seconds - %s(H:M:S), Speed: %sx"
    print(actionStr %(file_seconds,formatTime(file_seconds), cpusStr, modelName, elapsStr, formatTime(elapsed), convStr))
    print("\n")
    
    # alternate methods for writing the text or segments to disk
    writeTestfile(filePath, tempDirectory, allSegments, chunk_seconds) # write, TEXT, SRT and JSON to disk using segments
    writeTextFile(filePath, tempDirectory, finalStr) # take the final string returned and write it to disk
    
    removeTempFiles(tempFileArray)
    print(finalStr)

#    ____ MODEL PERFORMANCE AND TESTING METHODS ___

def performanceTest(modelName, filePath, tempDirectory):
    start    = timer()
    maxProc  = multiprocessing.cpu_count() - 1
    for cpusUtilized in range(1,maxProc):
        transcribeChunks(modelName, filePath, tempDirectory, cpusUtilized)
    end     = timer()
    elapsed = (end - start)
    print("Performance test with the \"%s\" model completed in %s seconds, (H:M:S) %s \n\n" %( modelName, elapsed, formatTime(elapsed) ))


def executeAllModelTest():
    start    = timer()
    models   = ["tiny.en","base.en","small.en","medium.en"]
    models   = ["tiny.en","base.en","small.en"]
    outDir   = useSampleOutputDirectory()
    targPath = useSampleAudioVideoFile()

    for modelName in models:
        print("loading model...\n")
        loadWhisperModel(modelName)
        performanceTest(modelName, targPath, outDir)
    end     = timer()
    elapsed = (end - start)
    print("All model test completed in %s seconds, (H:M:S) %s \n\n" %( elapsed, formatTime(elapsed) ))
    print("DONE.")


def testStaticVideo():
    audioInput = useSampleAudioVideoFile()
    imageInput = useSampleInputImage() #waverly-logo.png
    output_dir = useSampleOutputDirectory()
    outputFile = output_dir + Path(audioInput).stem + ".mp4"
    makeStaticVideo(audioInput, imageInput, outputFile)
    print("Video Complete")


def transcribe():
    print("loading model...\n")
    targetPath    = useSampleAudioVideoFile()   # File to be transcribed
    outDirectory  = useSampleOutputDirectory()  # Directory to place results
    maxProcesses  = 15                          # The number of processes to execute (up to the number of CPUs)
    modelName     = "base.en"                   # Examples: "tiny.en","base.en","small.en","medium.en"
    loadWhisperModel(modelName)                 # Explicitly load Whisper model
    transcribeChunks(modelName, targetPath, outDirectory, maxProcesses)


# Examples: Whisper model names include "tiny.en","base.en","small.en","medium.en"
loadDefaultWhisperModel() # Load our default or explictly load our Whisper model

#if __name__ == '__main__': # could be called from another application like PythonKit, so leave it out

#    ____ MODEL PERFORMANCE TESTING ___
transcribe()
#transcribeChunks(modelName, targetPath, outDirectory, maxCPUs)
#executeAllModelTest() # -- performance testing
#testStaticVideo()
#downloadModels()

