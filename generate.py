#!/usr/bin/env python

import json
import optparse
import os
import shutil
import subprocess
import sys

from Cheetah import Template

INDEX_TMPL = os.path.abspath('index.tmpl')
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

    pages = []

    with open(VIDEO_TMPL, 'r') as fd:
        template = fd.read()

        for f in files:
            link = f[len(input):]
            # Trim the leading slash and trailing ".flv"
            name = link[1:-4].replace(os.path.sep, '-')
            name = name.replace(' ', '_')

            filename = '%s.php' % name

            title = os.path.basename(link[:-4])
            infopath = '%s.info' % f
            info = 'No information available'
            if os.path.exists(infopath):
                with open(infopath, 'r') as infofd:
                    info = '<br/>\n'.join(infofd.readlines())


            videopage = Template.Template(template, searchList=[{'link' : link,
                'name' : name, 'title' : title, 'info' : info}])

            with open(os.path.join(output, filename), 'w') as wfd:
                wfd.write(str(videopage))

            thumbnail = generateThumbnail(f, output, filename)
            pages.append((title, filename, thumbnail, info))

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

    with open(INDEX_TMPL, 'r') as fd:
        template = fd.read().decode('utf-8')
        indexpage = Template.Template(template, searchList=[{'pages' : pages}])
        with open(os.path.join(output, 'index.html'), 'w') as wfd:
            wfd.write(str(indexpage))
    return 0


if __name__ == '__main__':
    exit(main())



