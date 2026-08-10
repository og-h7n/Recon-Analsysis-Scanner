"""Using Shodan, chaos and AlterX"""

import os

class Scanner:

    def __init__(self, target):
        self.target = target


#using chaos
    def chaos(self):
        print("[*] Now running chaos")
        print(f"[*] Scan starting on: {self.target}")

        cmd = f"chaos -d {self.target} | alterx -enrich | dnsx > chaos.txt"
        os.system(cmd)

        print(f'[+] Scan completed, file saved to chaos.txt')
        print(f"[+] Chaos found: {os.popen('wc -l < chaos.txt').read().strip()}")


#using alterX for permutations (abc.com --> xyz.abc.com )

    def permutation(self):
        print("[*] Now Running AlterX")
        print(f'[*] Permutation starting on: {self.target}')

        cmd = f'echo {self.target} | alterx -enrich | httpx -sc -td -title -server > permutation.txt'
        os.system(cmd)

        print('[+] AlterX scan done')
        print(f'[+] Alterx Found: {os.popen("wc -l < permutation.txt").read().strip()}')


#using subfinder
    def subfinder(self):
        print(f'[*] Running subdomain discovery on {self.target}')
        print('[*] Using subfinder')

        cmd = f'subfinder -d {self.target} -all -silent | anew subfinder.txt'
        os.system(cmd)

        print('[+] Subdomains Discovery Done')
        print(f'[+] Found {os.popen("wc -l < subfinder.txt").read().strip()} domains')


# using github scanner to scan github repos
    def github(self):
        print(f'[*] Running domain scan on {self.target}')
        print('[*] Using Github scanner')

        cmd = f'github-subdomains -d {self.target} -t $GITHUB_TOKEN '
        os.system(cmd)

        print('[+] Subdomains Discovery Done')
        print(f'[+] Github found {os.popen(f"wc -l < {self.target}.txt").read().strip()} domains')



#subdomain bruteforcing using puredns (resolvers - then bruteforce)
    def subdomain_brtFC(self):
        print(f'[*] Getting DNS resolvers')

        cmd = 'dnsvalidator -tL https://public-dns.info/nameservers.txt -threads 100 -o resolvers.txt'
        os.system(cmd)

        print('[+] File created: resolvers.txt')
        print(f'[*] Bruteforcing on {self.target}')
        print('[*] Using puredns')

        wordlist = '/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt'
        cmd = f'puredns bruteforce {wordlist} -d {self.target} -r resolvers.txt -w BrtFC.txt'
        os.system(cmd)

        print('[+] Subdomain Bruteforcing Done')
        print(f'[+] puredns found {os.popen("wc -l < BrtFC.txt").read().strip()} domains')


if __name__ == "__main__":
    obj = Scanner('tvh.com')
    obj.permutation()
    obj.subfinder()
    obj.github()