<a name="readme-top"></a>

<!-- ABOUT THE PROJECT -->
## About The Project


This program provides a pronounced acceleration for transcribing audio using Whisper by changing the workflow, through  multiprocessing. The user chooses the number of processes to run in parallel (forked), up to the number of available CPUs and the input file is chunked\fragmented into the number of processes.  By consuming and processing each audio chunk in parallel, we obtain our dramatic acceleration using only CPUs.

Why?  

I had been looking for ways to maximize CPU utilization to  abbreviate transcription time because I do not have a machine with a supported GPU. I used the command line options for threading, but was not obtaining additional benefits from increasing the number of threads. I expected that it could be done through parallelization.

## Note:  

Whisper was trained on and uses 30 second windows of audio, so chunks shorter than 30 seconds are inefficiently processed.
Acceleration flattens at a certain point, so more processes are not always better.


### Caveats

1. A copy of the input file is created and broken into chunks for parallel consumption, which temporarily increases disk space.
2. The concatenated transcriptions may lose a word or context at each fragment boundary because a word is cut off.
3. The text normalization, on the ending and beginning word may be incorrect because context at each boundary is lost.  
	An example is gaining a period at the end of fragment or capitalization at the beginning of a new fragment.
4. The processes are forked, so when the parent process is terminated, the forked process must be manually terminated 
	(e.g. Activity Monitor, Task Manager)
5. The timeline on the output must be concatenated and repaired because each fragment will begin at zero.  
	This problem has been resolved but may need an extra set of eyes.

These are small costs to increase processing speed.


<!-- USAGE EXAMPLES -->
## Usage

Define 
- The input file, which may be an audio or video file.  
- The output folder for the transcription file.  
- The number of processes to execute in parallel
- The Whisper model you will use to transcribe
- Supply this to transcribeChunks(...)


<p align="right">(<a href="#readme-top">back to top</a>)</p>


```Python
def transcribe():
    print("loading model...\n")
    targetPath    = useSampleAudioVideoFile()	# File to be transcribed
    outDirectory  = useSampleOutputDirectory()  # Directory to place results
    maxProcesses  = 15				# The number of processes to execute (up to the number of CPUs)
    modelName     = "base.en"                   # Examples: "tiny.en","base.en","small.en","medium.en"
    loadWhisperModel(modelName)                 # Explicitly load Whisper model
    transcribeChunks(modelName, targetPath, outDirectory, maxProcesses)

transcribe()
```


## Performance Testing

All testing was done on a MacBook, macOS Big Sur using 2.3 GHz Intel Core i9, 16 cores, with 16G of RAM.  
Testing of "medium.en" model was very limited because I quickly ran out of memory, so those test were not included.


The input file duration was 3706.393 seconds - 01:01:46(H:M:S)  

Foundation is the base\natural speed (no acceleration) for that Whisper model,  
which is a single process using the multiprocessing module on the above computer.  

The larger the model, the more time is required to process the input.  

For the largest model tested ("small.en", due to memory constraints) our gross  
foundation speed (without acceleration) is 00:31:24(H:M:S), for a speed of 1.967x.  
Using 9 processes brings that down to 00:11:02(H:M:S), for a speed of 5.595x 

.

| Processes | Model | Completed | Speed |
| --------------- | --------- | ---------------------------------- | -------- |
|  001 on 16CPUs |  tiny.en  | 320.270 seconds - 00:05:20(H:M:S)  | 11.573x (foundation)  |
|  002 on 16CPUs |  tiny.en  | 204.101 seconds - 00:03:24(H:M:S)  | 18.160x  |
|  003 on 16CPUs |  tiny.en  | 159.478 seconds - 00:02:39(H:M:S)  | 23.241x  |
|  004 on 16CPUs |  tiny.en  | 142.867 seconds - 00:02:22(H:M:S)  | 25.943x  |
|  005 on 16CPUs |  tiny.en  | 130.071 seconds - 00:02:10(H:M:S)  | 28.495x  |
|  006 on 16CPUs |  tiny.en  | 120.219 seconds - 00:02:00(H:M:S)  | 30.830x  |
|  007 on 16CPUs |  tiny.en  | 114.270 seconds - 00:01:54(H:M:S)  | 32.435x  |
|  008 on 16CPUs |  tiny.en  | 113.579 seconds - 00:01:53(H:M:S)  | 32.633x  |
|  009 on 16CPUs |  tiny.en  | 116.303 seconds - 00:01:56(H:M:S)  | 31.869x  |
|  010 on 16CPUs |  tiny.en  | 114.806 seconds - 00:01:54(H:M:S)  | 32.284x  |
|  011 on 16CPUs |  tiny.en  | 113.300 seconds - 00:01:53(H:M:S)  | 32.713x  |
|  012 on 16CPUs |  tiny.en  | 116.954 seconds - 00:01:56(H:M:S)  | 31.691x  |
|  013 on 16CPUs |  tiny.en  | 119.148 seconds - 00:01:59(H:M:S)  | 31.108x  |
|  014 on 16CPUs |  tiny.en  | 119.249 seconds - 00:01:59(H:M:S)  | 31.081x  |
|  001 on 16CPUs |  base.en  | 630.402 seconds - 00:10:30(H:M:S)  | 5.879x   (foundation) |
|  002 on 16CPUs |  base.en  | 402.318 seconds - 00:06:42(H:M:S)  | 9.213x   |
|  003 on 16CPUs |  base.en  | 321.623 seconds - 00:05:21(H:M:S)  | 11.524x  |
|  004 on 16CPUs |  base.en  | 296.263 seconds - 00:04:56(H:M:S)  | 12.510x  |
|  005 on 16CPUs |  base.en  | 264.880 seconds - 00:04:24(H:M:S)  | 13.993x  |
|  006 on 16CPUs |  base.en  | 239.005 seconds - 00:03:59(H:M:S)  | 15.508x  |
|  007 on 16CPUs |  base.en  | 225.773 seconds - 00:03:45(H:M:S)  | 16.416x  |
|  008 on 16CPUs |  base.en  | 237.162 seconds - 00:03:57(H:M:S)  | 15.628x  |
|  009 on 16CPUs |  base.en  | 242.201 seconds - 00:04:02(H:M:S)  | 15.303x  |
|  010 on 16CPUs |  base.en  | 241.885 seconds - 00:04:01(H:M:S)  | 15.323x  |
|  011 on 16CPUs |  base.en  | 234.943 seconds - 00:03:54(H:M:S)  | 15.776x  |
|  012 on 16CPUs |  base.en  | 233.985 seconds - 00:03:53(H:M:S)  | 15.840x  |
|  013 on 16CPUs |  base.en  | 228.198 seconds - 00:03:48(H:M:S)  | 16.242x  |
|  014 on 16CPUs |  base.en  | 232.113 seconds - 00:03:52(H:M:S)  | 15.968x  |
|  001 on 16CPUs |  small.en | 1884.421 seconds - 00:31:24(H:M:S) | 1.967x   (foundation) |
|  002 on 16CPUs |  small.en | 1155.361 seconds - 00:19:15(H:M:S) | 3.208x   |
|  003 on 16CPUs |  small.en | 988.958 seconds - 00:16:28(H:M:S)  | 3.748x   |
|  004 on 16CPUs |  small.en | 808.133 seconds - 00:13:28(H:M:S)  | 4.586x   |
|  005 on 16CPUs |  small.en | 813.511 seconds - 00:13:33(H:M:S)  | 4.556x   |
|  006 on 16CPUs |  small.en | 745.613 seconds - 00:12:25(H:M:S)  | 4.971x   |
|  007 on 16CPUs |  small.en | 672.915 seconds - 00:11:12(H:M:S)  | 5.508x   |
|  008 on 16CPUs |  small.en | 668.179 seconds - 00:11:08(H:M:S)  | 5.547x   |
|  009 on 16CPUs |  small.en | 662.412 seconds - 00:11:02(H:M:S)  | 5.595x   |
|  010 on 16CPUs |  small.en | 731.510 seconds - 00:12:11(H:M:S)  | 5.067x   |
|  011 on 16CPUs |  small.en | 666.586 seconds - 00:11:06(H:M:S)  | 5.560x   |
|  012 on 16CPUs |  small.en | 698.039 seconds - 00:11:38(H:M:S)  | 5.310x   |
|  013 on 16CPUs |  small.en | 714.755 seconds - 00:11:54(H:M:S)  | 5.186x   |
|  014 on 16CPUs |  small.en | 731.595 seconds - 00:12:11(H:M:S)  | 5.066x   |


<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [ ] Find and replace the word in the transcript, at the boundaries that may have been lost or misinterpreted
- [ ] Developing a performance curve, to suggest the number of processes to execute, based on machine resources
- [ ] Calculate the amount of RAM will be used based on the model and processes requested, prevent memory exhaustion
- [ ] Learn from someone on how to implement forced-alignment, for word-level time-stamps (versus the current phrase-level)
- [ ] Trap the signal for the parent application termination and then terminate the forked processes
- [ ] Limiting CPU utilization to X percent.  Currently the processes will utilize all available CPU power.

If there are 8 processes, the program will still use ~1600 % for 16 cores, spread amongst the 8 processes,  
instead 100% per process, which is ~800% (based on resource availability).

I'm not sure the extra horsepower is being utilized.  If I understand how to limit a process to a specified number  
of CPU\core, the difference can be determined though performance timing.


<p align="right">(<a href="#readme-top">back to top</a>)</p>




<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* OpenAI
* Github Community
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>


