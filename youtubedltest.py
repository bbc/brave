from __future__ import unicode_literals
import youtube_dl
streamurl = 'https://www.youtube.com/watch?v=vQ8xjg7mcgE'

purl = 'notset'

# should be able to just pass a -g and get the url

# forceurl or --get-url
# extracting and examples https://www.bogotobogo.com/VideoStreaming/YouTube/youtube-dl-embedding.php
# sudo -H pip install --upgrade youtube-dl
# /usr/local/lib/python2.7/dist-packages/youtube_dl/

# need to look at the info dict.. f['url']

class MyLogger(object):
    #purl = 'notset'
    def debug(self, msg):
        global purl
        if "https" in msg:
            #print(msg)
            purl = msg
        pass

    def warning(self, msg):
#        print(msg)
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')
    if d['status'] == 'downloading':
        print(d)


ydl_opts_audio = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}

ydl_opts = {
    'simulate': True,
    'noplaylist' : True,
    'forceurl' : True,
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([streamurl])
    #meta = ydl.extract_info([streamurl],download=False)

    #print("url:",meta['title'])
    print("url:", purl)



#print("url:", purl)
