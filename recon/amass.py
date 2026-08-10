"""Using Amass -- Takes too much time """


import os


class Amass:

    def __init__(self,target):
        self.target = target


#using acitve scans

    def active(self):
        print('[*]Now running amass')
        print('[*]Using active scan')

        cmd = f"amass enum -active -d {self.target} | grep -oE '([a-zA-Z0-9_-]+\\.)' | sort -u | anew Amass_A.txt"
        os.system(cmd)

        print("[+]Scan completed")
        print(f"[+]Amass found: {os.popen('wc -l < Amass_P.txt').read().strip()} ")
        print("[+]File saved to Amass_A.txt")

#using passive scan
    def passive(self):
        print('[*]Now running amass')
        print('[*]Using passive scan')

        cmd = f"amass enum -passive -d {self.target} | grep -oE '([a-zA-Z0-9_-]+\\.)' | sort -u | anew Amass_P.txt"
        os.system(cmd)

        print("[+]Scan completed")
        print(f"[+]Amass found: {os.popen('wc -l < Amass_P.txt').read().strip()} ")
        print("[+]File saved to Amass_P.txt")


    











obj = Amass('tvh.com')
obj.active()
obj.passive()