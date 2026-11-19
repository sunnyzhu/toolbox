import sys
import getopt
from datetime import datetime
from pathlib import Path,WindowsPath
import subprocess

def format_time(start,end):
    delta =  (datetime.strptime(end,'%H:%M:%S') - datetime.strptime(start,'%H:%M:%S')).seconds
    return start,'{}:{}:{}'.format(delta //3600,delta%3600//60,delta%3600%60)

def parse_name(in_file):
    suffix = in_file.split('.')[-1]
    return in_file.split('.')[0].split('\\')[-1],suffix

def part_command(part,in_file,out_file,vcodec='copy',acodec='copy'):
    _part=part.split("-")
    _codec='-c:v {} -c:a {}'.format(vcodec,acodec)
    if len(_part)==1 or _part[1]=='':
        start = _part[0]
        command= 'ffmpeg -ss {} -i {} {} -y {}'.format(start,in_file,_codec,out_file)
    else:
        start,end = format_time(_part[0],_part[1])
        command= 'ffmpeg -ss {} -i {} -to {} {} -y {}'.format(start,in_file,end,_codec,out_file)
    return command


def gen_split(in_file,parts,name=None,vcodec='copy',acodec='copy',output_ext=None):
    name,suffix = parse_name(in_file)
    suffix = output_ext if output_ext else suffix
    
    if len(parts)==1: 
        yield part_command(parts[0],in_file,"{}-m.{}".format(name,suffix),vcodec=vcodec,acodec=acodec)
    else:   #生成合并多个片段命令
        concat="\"concat:"
        for i,part in enumerate(parts):
            out_file = '{}.{}'.format(i,'ts')
            concat+=out_file+"|"
            yield part_command(part,in_file,out_file,vcodec=vcodec,acodec=acodec)
        yield 'ffmpeg -i {}\" -c copy {}-m.{}'.format(concat,name,suffix)   #合并不改变片段编码
    for i in range(len(parts)):
        yield 'del {}.ts'.format(i)

def main(argv):
    usage = "split.py [-h] [-d] [-v vcodec] [-a acodec] [-o output_ext] <input file> <hh:mm:dd-hh:mm:dd [hh:mm:dd-hh:mm:dd [...]]>"
    try:
        opts, args = getopt.getopt(
            argv, "hdv:a:o:", ["help", "dryrun", "vcodec=", "acodec=", "output="])
        if len(args)<2:
            raise getopt.GetoptError("less then two arguments.")
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)

    def run_sub(x):
        result=subprocess.run(x,shell=True,stdout=subprocess.PIPE,stderr=sys.stdout)
        print(result.stdout)
 
    executor=run_sub
    vcodec='copy'
    acodec='copy'
    output_ext=None
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
        elif opt in ("-d","--dryrun"):
            executor=lambda x:print(x)
        elif opt in ("-v", "--vcodec"):
            vcodec = arg
        elif opt in ("-a", "--acodec"):
            acodec = arg
        elif opt in ("-o", "--output"):
            output_ext = arg
            
    for cmd in gen_split(args[0],args[1:],vcodec=vcodec,acodec=acodec,output_ext=output_ext):        
        executor(cmd)


if __name__ == "__main__":
    main(sys.argv[1:])
