#!/usr/bin/env python

import collections
import json
import operator
import optparse
import os
import shutil
import subprocess
import sys

from Cheetah import Template

INDEX_TMPL = os.path.abspath('index.tmpl')
SHOW_TMPL = os.path.abspath('show.tmpl')
VIDEO_TMPL = os.path.abspath('video.tmpl')
STATICS = os.path.abspath('static')
THUMBNAIL_TIME = 60

def findVideos(folder):
    for root, dirs, files in os.walk(folder, followlinks=True):
        if not files:
            continue

        for f in files:
            if not f.endswith('.flv'):
                continue
            yield os.path.join(root, f)


def generateThumbnail(fullpath, output, page):
    # ffmpeg  -itsoffset -4  -i test.avi -vcodec mjpeg -vframes 1 -an -f
    # rawvideo -s 320x240 test.jpg
    image = page.replace('.php', '.jpg')
    output = os.path.join(output, image)
    if os.path.exists(output):
        print '>>> Thumbnail exists!'
        return image

    print '>>> Generating thumbnail for %s' % fullpath
    command = 'ffmpeg -itsoffset -%d -i "%s" -vcodec mjpeg -vframes 1 -an -f rawvideo -s 320x240 "%s"' % (THUMBNAIL_TIME, fullpath, output)
    os.system(command)
    return image


def main():
    options = optparse.OptionParser()
    options.add_option('-o', '--output', default='output',
                dest='output', help='Output directory')
    options.add_option('-i', '--input', default='.',
                dest='input', help='Input directory (of FLVs)')
    opts, args = options.parse_args()

    if not opts.output or not opts.input:
        print '>>> Missing arguments!'
        return 1

    input = os.path.abspath(opts.input)
    output = os.path.abspath(opts.output)

    print '>>> Scanning %(input)s for .flv files' % locals()
    print

    files = list(findVideos(input))

    print '>>> Discovered %d videos:\n\n\t %s' % (len(files), '\n\t '.join(files))

    tv = {}
    movies = []

    with open(VIDEO_TMPL, 'r') as fd:
        template = fd.read()

        for f in files:
            link = f[len(input):]
            # Trim the leading slash and trailing ".flv"
            name = link[1:-4].replace(os.path.sep, '-')
            name = name.replace(' ', '_')

            filename = '%s.php' % name
            pieces = [p for p in link.split(os.path.sep) if p]
            title = os.path.basename(link[:-4])
            isTV = False
            showName = None
            showSeason = None
            info = 'No info'
            if pieces and pieces[0]:
                # Assuming that televisions shows are
                # .../television/SHOW/SEASON/...
                if pieces[0] == 'television':
                    isTV = True
                    showName = pieces[1]
                    showSeason = pieces[2]
                    info = '%s<br/>%s<br/>' % (pieces[1], pieces[2])


            videopage = Template.Template(template, searchList=[{'link' : link,
                'name' : name, 'title' : title, 'info' : info}])

            with open(os.path.join(output, filename), 'w') as wfd:
                wfd.write(str(videopage))

            thumbnail = generateThumbnail(f, output, filename)
            if not isTV:
                movies.append((title, filename, thumbnail, info))
                continue
        
            if not tv.has_key(showName):
                tv[showName] = {}
            if not tv[showName].has_key(showSeason):
                tv[showName][showSeason] = []

            tv[showName][showSeason].append((title, filename, thumbnail, info))


    print
    print '>>> Copying static files into %s' % output
    for path in os.listdir(STATICS):
        fullpath = os.path.abspath(os.path.join(STATICS, path))
        try:
            if os.path.isdir(fullpath):
                shutil.copytree(fullpath, os.path.join(output, path))
            else:
                shutil.copy(fullpath, os.path.join(output, path))
        except Exception, ex:
            print ('Exception processing', path, ex)

    with open(SHOW_TMPL, 'r') as fd:
        template = fd.read().decode('utf-8')
        for show, episodes in tv.iteritems():
            showpage = Template.Template(template, searchList=[{'show' : show, 'shows' : episodes}])
            with open(os.path.join(output, '%s.html' % show), 'w') as wfd:
                wfd.write(str(showpage))


    with open(INDEX_TMPL, 'r') as fd:
        template = fd.read().decode('utf-8')
        indexpage = Template.Template(template, searchList=[{'tv' : tv, 'movies' : movies}])
        with open(os.path.join(output, 'index.html'), 'w') as wfd:
            wfd.write(str(indexpage))
    return 0


if __name__ == '__main__':
    exit(main())



