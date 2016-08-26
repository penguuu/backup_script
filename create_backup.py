# TODO:
# - kryptaus?
# - incremental backup?

import tarfile
import sys, getopt
import hashlib
import os
from os.path import join,getsize
from glob import glob

verb_flag = 0
chk_flag = 0
chk_fh = 0 

def gethash(path):
    BLOCKS = 65536
    hasher = hashlib.sha256()
    with open(path,'rb') as hfile:
	buf = hfile.read(BLOCKS)
	while len(buf) > 0:
		hasher.update(buf)
		buf = hfile.read(BLOCKS)

    return(hasher.hexdigest())

def size_to_string(s):
    size_str = ""

    if s<1024:        
        units = "bytes"
    elif s<pow(1024,2):
        s/=1024;
        units = "KB"
    elif s<pow(1024,3):
        s/=pow(1024,2)
        units = "MB"
    elif s<pow(1024,4):
        s/=pow(1024,3)
        units = "GB"
    elif s<pow(1024,5):
        s/=pow(1024,4)
        units = "TB"
    else:
        units = "bytes"

    size_str = str(s)+" "+units
    return size_str

def go_through_files(backup_path,tar):
    f_count = 0
    dir_count = 0
    f_sizes = 0
    units = ""

    for dname,dirs,files in os.walk(backup_path,followlinks=False,topdown=True):
	    for f in files:
	        fullpath = os.path.join(dname,f)
		if os.path.isfile(fullpath):
		    fsize = getsize(fullpath)
		    f_sizes += fsize
                    if chk_flag == 1:
                        checksum = gethash(fullpath)
                    if verb_flag == 1:
                        print("Processing file "+dname+f+" size: "+size_to_string(fsize) + " ("+str(fsize)+" bytes)")
                        if chk_flag == 1:
                            print("File checksum: ["+checksum+"]")
                    tar.add(fullpath)
                    if chk_flag == 1:
                        chk_fh.write(checksum+"\t"+fullpath+"\n")
		    f_count = f_count+1			
		dir_count = dir_count+1

    print("Went through "+str(f_count)+" files in "+str(dir_count)+" directories")
    print("Total size of files: "+size_to_string(f_sizes)+" " +units+" ("+str(f_sizes)+" bytes)")

def go_through_inc_file(backup_path,tar,inc_fh):
    f_sizes = 0
    f_count = 0
    f_total = 0

    for l in inc_fh:
        l = l.strip()
        f_total +=1
        (sha256sum,path) = l.split("\t")    
        checksum = gethash(path)
        if checksum != sha256sum:
            tar.add(path)
            if verb_flag == 1:
                print("File "+path+" has been changed  [old checksum: "+sha256sum+"] [new checksum: "+checksum+"]")                
                f_sizes += getsize(path)
                f_count +=1
                tar.add(path)
                if chk_flag == 1:
                    chk_fh.write(checksum+"\t"+path+"\n")

    print("Went through "+str(f_total)+" files in which "+str(f_count)+" has been changed")
    print("Total size of changed files: "+size_to_string(f_sizes))
            
def print_help():
    print("create_backup.py [OPTIONS] -f <backup_file> {-p <path>|-i <sha256 file>}")
    print("\t-f --backupfile <file>\tdefine in which file to write the backup")
    print("\t-p --path       <path>\tdefine path to be backed up")
    print("\t-v --verbose\t\tset verbose mode on")
    print("\t-c --checksum\t\tcalculate checksums and add write them to file")
    print("\t-i --incremental <sha256 file>\tcreate incremental backups")

def main(argv):
    global chk_fh
    inc_fh = 0
    inc_flag = 0
    backupfile = ''
    inc_file = ''
    path = ''
    tar = 0

    try:
        opts,args = getopt.getopt(sys.argv[1:],"hf:p:vci:",["help","backupfile=","path=","verbose","checksum","incremental"])
    except getopt.GetoptError:
        print_help()
	sys.exit(2)

    for opt, arg in opts:
	if opt in ("-h","--help"):
            print_help()
	    sys.exit()
	elif opt in ("-f","--backupfile"):
	    backupfile = arg
	elif opt in ("-p","--path"):
	    path = arg
        elif opt in ("-v","--verbose"):
            global verb_flag
            verb_flag = 1
        elif opt in ("-c","--checksum"):
            global chk_flag
            chk_flag = 1
        elif opt in ("-i","--incremental"):
            inc_flag = 1
            inc_file = arg

    if(not backupfile or (not inc_file and not path)):        
        print_help()
	sys.exit()

    if chk_flag == 1:
        try:
            if os.path.isfile(backupfile+".sha256"):
                l=0
                for l in range(1,9999):
                    if not os.path.isfile(backupfile+".sha256."+str(l)):
                        break
                chk_fh = open(backupfile+".sha256."+str(l),"w")                
            else:
                chk_fh = open(backupfile+".sha256","w")
        except IOError:
            print("Error: Unable to open "+backupfile+".sha256 for writing")
            sys.exit()

    if inc_flag == 1:
        try:
            inc_fh = open(inc_file,"r")
        except IOError:
            print("Error: Unable to open "+inc_file+" for reading")
            sys.exit()

        print("Staring incremental backup from "+ inc_file + " files to "+ backupfile)
        tar = tarfile.open(name=backupfile,mode='w:gz')
        go_through_inc_file(path,tar,inc_fh)
        tar.close()

    else:
        print("Starting backup for "+ path +" to "+ backupfile)
        tar = tarfile.open(name=backupfile,mode='w:gz')
        go_through_files(path,tar)
        tar.close()

    if chk_flag == 1:
        chk_fh.close()

    
if __name__ == "__main__":
    main(sys.argv[1:])
