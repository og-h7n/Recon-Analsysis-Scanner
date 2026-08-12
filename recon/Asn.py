"""Using things such as Favicon , Asn numbers to get more 
attack surfaces"""


import subprocess
import os
import threading
from pathlib import Path


class asn:
    
    def __init__(self,target):
        self.target = target
        
        
    def asn_enum(self):
        print('[+] First Getting Asn number')
        print(f'[+] Target : {self.target}')

        result = subprocess.run(
            [
                "bash", "-c",
                'curl -s "https://stat.ripe.net/data/searchcomplete/data.json?resource=paypal" '
                '| jq -r \'.data.categories[] | select(.category=="ASNs") | .suggestions[].value\''
            ],
            capture_output=True,
            text=True
        )

        asn_list = result.stdout.strip().splitlines()

        for ASN in asn_list:
            print(f'[*] Getting IP ranges for {ASN}')
            cmd = (
                f'bgpq4 -A -4 {ASN} '
                f'| grep "permit" '
                f'| awk \'{{print $NF}}\' '
                f'| anew ip_ranges.txt'
            )
            os.system(cmd)
        count = os.popen('wc -l < ip_ranges.txt').read().strip()
        print(f'[+] Found {count} IP ranges saved to ip_ranges.txt')

        print('[+]Now reading Ip')


    #using reverse IP look up to find new domains linked to ips
    
    def reverse_ip_lookup(self):
        print(f'[*] Starting Reverse IP lookup for {self.target}')

        # step 1 - get IP ranges from ip_ranges.txt
        if not Path('ip_ranges.txt').exists():
            print('[!] ip_ranges.txt not found - run asn_to_ranges() first')
            return

        ranges = open('ip_ranges.txt').read().strip().splitlines()
        if not ranges:
            print('[!] ip_ranges.txt is empty')
            return

        print(f'[+] Found {len(ranges)} IP ranges to process')

        # step 2 - use interlace for multithreading across all ranges
        # write ranges to a temp file for interlace to consume
        with open('_ranges_temp_.txt', 'w') as f:
            f.write('\n'.join(ranges))

        cmd = (
            'interlace '
            '-tL _ranges_temp_.txt '
            '-threads 10 '
            '-c "curl -s \'https://rapiddns.io/sameip/_target_?full=1\' '
            '| grep -oP \'(?<=<td>)[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}(?=</td>)\' '
            '| sort -u | anew reverse_ip.txt" '
            '-v'
        )
        os.system(cmd)

        # cleanup temp file
        try:
            os.remove('_ranges_temp_.txt')
        except FileNotFoundError:
            pass

        count = os.popen('wc -l < reverse_ip.txt').read().strip()
        print(f'[+] Reverse IP lookup found: {count} domains')
        print('[+] Results saved to reverse_ip.txt')

    
    

obj = asn('paypal')
obj.reverse_ip_lookup()