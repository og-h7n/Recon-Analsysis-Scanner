""" This is used to get all the urls from the subdomain and make the 
process fast  , The Urls will then be further divided into specific endpoints 
in order to run analysis on them """

import subprocess 
import os
import concurrent.futures
from pathlib import Path
import threading

class GetAllUrls:

    def __init__(self,target):
        self.target = target

    #for creating folder
    def __make__folder(self,folder):
        os.makedirs(folder)

    
    #for creating files for the tools and store there output indivisually   
    def __make__file(self,tool):
        Path(f"{tool}.txt").touch()

    #for runnning gau

    def run_gau(self):
        self.__make__file('_gau_')
        print(f'[+] File created _gau_.txt')
        

        cmd = (
            f"gau --threads 5 "
            f"--providers wayback,commoncrawl,otx,urlscan "
            f"--blacklist png,jpg,gif,svg,css,woff,ttf "
            f"{self.target} | anew _gau_.txt"
        )
        os.system(cmd)
        print(f'[+] GAU Scan done')
        print(f'[+] File saved to _gau_.txt')
        
        count = os.popen('wc -l < _gau_.txt').read().strip()
        print(f'[+] Gau found: {count}')

# for running katana
    def run_katana(self):
        self.__make__file('_katana_')
        print(f'[+] File created _katana_.txt')
        

        cmd = f'katana -u https://{self.target} -d 3 | anew _katana_.txt'

        os.system(cmd)
        print(f'[+] Katana Scan done')
        print(f'[+] File saved to _katana_.txt')
        
        count = os.popen('wc -l < _katana_.txt').read().strip()
        print(f'[+] Katana found: {count}')
#for spider
    def run_gospider(self):
        self.__make__file("_gospider_")
        print('[+]File created _gospider_.txt')


        cmd = (
            f'gospider -s "https://{self.target}" '
            f'-c 10 -d 5 --other-source --include-subs --include-other-source '
            f'--sitemap --robots -w -r -t 20 --js -a '
            f'-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" '
            f'--timeout 15 -q | anew _gospider_.txt'
        )
        os.system(cmd)

        count = os.popen('wc -l < _gospider_.txt').read().strip()
        print(f'[+] Gospider found {count} endpoints')



#Removing duplicates -> then checking for their live -> separating 403 for bypassing

    def rm_junk(self):
        self.__make__file('_LiveUrls_')
        print('[+] Removing duplicates and checking for liveness')

        # run httpx with status codes into a temp file
        cmd = 'cat _gau_.txt _katana_.txt _gospider_.txt | uro | httpx -mc 200,301,302,403,401 -silent -sc > _live_with_status_.txt'
        os.system(cmd)

        # clean URLs only → _LiveUrls_.txt (for downstream tools)
        os.system("awk '{print $1}' _live_with_status_.txt > _LiveUrls_.txt")

        # 403/401 URLs only → _bypass_.txt (for bypass testing)
        os.system("grep -E '\\[403\\]|\\[401\\]' _live_with_status_.txt | awk '{print $1}' > _bypass_.txt")

        # cleanup temp file
        os.remove('_live_with_status_.txt')

        count = os.popen('wc -l < _LiveUrls_.txt').read().strip()
        bypass_count = os.popen('wc -l < _bypass_.txt').read().strip()

        print(f'[+] _LiveUrls_.txt — {count} live endpoints (clean URLs)')
        print(f'[+] _bypass_.txt   — {bypass_count} potential bypass targets (403/401)')


    def screen_shot(self):
        print(f"[*]Now Taking screen shot of worth it targets , {'\033[91m'}Use brave browser ! {'\033[0m'}")

        cmd = (
                "cat _LiveUrls_.txt | grep -viE '\\.(js|css|json|woff|ttf|svg|png|jpg|gif)($|\\?)' > _screenshot_targets_.txt "
                "&& gowitness scan file -f _screenshot_targets_.txt --threads 5 --chrome-path $(which brave-browser)"
            )
        os.system(cmd)

        print("[+]Screen shots taken , Thank you for your time :)")

#Now running all with threads 

        
        



