""" Using curl to fetch subdomains from the web """

import os
import threading



class curl:
    #defining target
    def __init__(self,site):
        self.site = site 

    
    #Creating a folder CURL
    def folder(self):
        print('[+]Created Folder CURL to store files')
        os.makedirs(name='CURL')
        os.chdir('CURL')

    #using certspotter api to fetch subdomains from SSL certs    
    def crt(self):
        print(f'[*]Searching for related subdomains')
        print(f'[*]Target : {self.site}')

        cmd = f"""curl -s "https://api.certspotter.com/v1/issuances?domain={self.site}&include_subdomains=true&expand=dns_names" \
                    | jq -r '.[].dns_names[]' | sort -u > crt.txt"""

        os.system(cmd)
        count = os.popen('wc -l < crt.txt').read().strip()

        print(f'[+]Certspotter found: {count} entries')
        print('[+]Results stored in crt.txt')


    #using virus total    
    def virus_total(self):
        print(f'[*]Using Virus total api to search')
        print(f'[*]Requires an API key')

        cmd = (
            f'curl -s -H "x-apikey: $VIRUS_TOTAL" '
            f'"https://www.virustotal.com/api/v3/domains/{self.site}/subdomains?limit=40" '
            f"| jq -r \'.data[].id\' > vt.txt"
        )

        os.system(cmd)
        count = os.popen('wc -l < vt.txt').read().strip()

        print(f'[+]Virus Total found: {count} entries')
        print('[+]Results stored in vt.txt')
        
        
        
    #using alien vault to get ip addresses
    def alien_vault(self):
        print('[*] Running AlienVault OTX lookup')

        cmd = (
            f"curl -s 'https://otx.alienvault.com/api/v1/indicators/hostname/{self.site}/url_list?limit=500&page=1' "
            f"| jq -r '.url_list[].result.urlworker.ip // empty' "
            f"| grep -Eo '([0-9]{{1,3}}\\.){{3}}[0-9]{{1,3}}' | sort -u > Alien_v_IP.txt"
        )
        os.system(cmd)

        count = os.popen('wc -l < Alien_v_IP.txt').read().strip()
        print(f'[+] AlienVault found: {count} IPs')
        print('[+] Results stored in Alien_v_IP.txt')

    
    #using wayback machine for subdomains archives 
    def wayback(self):
        print('[*]Searcing for archive subdomains')
        print('[*]Using wayback machine')

        cmd = (
            f'curl -s "http://index.commoncrawl.org/CC-MAIN-2024-10-index?url=*.{self.site}&output=json" '
            f"| jq -r '.url' "
            f"| grep -oE '^https?://[^/]+' "
            f"| sort -u > commoncrawl_subdomains.txt"
        )
        os.system(cmd)
        
        count = os.popen('wc -l < commoncrawl_subdomains.txt').read().strip()
        print(f'[+]Archives found : {count}')
        print('[+]Results are stored in commoncrawl_subdomains.txt')


    #Now using CSP headers to get sites which share the same header
    def CSP_header(self):
        print('[*]Using CSP header')
        
        cmd = (
            f'curl -I -s "https://{self.site}" '
            f"| grep -iE 'content-security-policy|CSP' "
            f'| tr " " "\\n" '
            f'| grep "\\." '
            f'| tr -d ";" '
            f"| sed 's/\\*\\.//g' "
            f"| sort -u > csp.txt"
        )
        os.system(cmd)
        count = os.popen('wc -l < csp.txt').read().strip()
        print(f'[+]CSP related subdomains found : {count}')
        print('[+]Results are stored in csp.txt')
    
    def cleaner(self):
        print('[*]Clearing duplicates and checking for Liveness')
        cmd = (
            "cat *.txt "
            "| sed -E 's#^(https?://)##; s#^#https://#' "
            "| uro "
            "| httpx -mc 200,301,403,401 -silent --status-code > Curl_Url.txt"
        )
        os.system(cmd)
        count = os.popen('wc -l < Curl_Url.txt').read().strip()

        print(f'[+] {count} live subdomains found')
        print('[+] Moving to root directory')

        os.system('cp Curl_Url.txt ../')
        print('[+] Transfer successful')
        

if __name__ == '__main__':
    obj = curl('tvh.com') #use site.com 
    obj.folder()
    obj.crt()
    obj.alien_vault()
    obj.virus_total()
    obj.wayback()
    obj.CSP_header()
    obj.cleaner()
