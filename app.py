import tss
import time
import numpy as np
from urllib import request
from O365 import Account
from tss import Hash
from binascii import hexlify, unhexlify

#RUN FROM DESKTOP

class SecretSharing:
    def __init__(self, threshold: int, shareholders: int, remote_file: str) -> None:
        #ping storage bucket
        self.latency = self.ping_o365()

        #track time
        overall_time_start = time.time()

        #0365 auth and file download to desktop
        scopes = ['https://graph.microsoft.com/Files.ReadWrite.All']
        credentials = ('ID HERE', 'SECRET HERE')
        self.secret_download_time = self.o365_file_dl(remote_file, scopes, credentials)
        
        #read file contents
        with open(remote_file) as file:
            content = file.read()

        #create shares, encrypt and decrypt
        print('--- SECRET SHARING LOADING ---')
        share_creation_time_start = time.time()
        shares = self.create_shares(threshold, shareholders, content)
        share_creation_time_finish = time.time()
        share_files = self.encryption(shares)
        self.share_upload_time = self.o365_file_ul(share_files, scopes, credentials)
        self.share_download_time, self.secret_recovery_time = self.decryption(scopes, credentials, share_files)
        
        #track time
        overall_time_finish = time.time()
        self.share_creation_time = (share_creation_time_finish - share_creation_time_start) 
        self.overall_time = (overall_time_finish - overall_time_start)
        
        print('--- SECRET SHARING COMPLETE ---')
        print('----------------------------------------------------------------------------------------------\n')

    def ping_o365(self) -> int:
        url = 'https://onedrive.live.com/?id=root&cid=2C1F8E6B7BC6F585'
        r = request.urlopen(url)
        start = time.time()
        x = r.read()
        finish = time.time()
        difference = (finish - start)
        print('--- PING {} = {} (ms) ---'.format(url, difference))
        print('----------------------------------------------------------------------------------------------\n')
        r.close()
        
        return difference

    def o365_file_dl(self, remote_file: str, scopes: list, credentials: tuple) -> float:
        download_path = 'C:/Users/dell/Desktop/'

        print('--- CONNECTING TO O365 ---\n')
        account = Account(credentials)

        if not account.is_authenticated:
            account.authenticate(scopes = scopes)
            print('\n--- USER AUTHENTICATION SUCCESSFUL ---\n')

        print('--- CONNECTED TO O365 ---\n')

        storage = account.storage()
        my_drive = storage.get_default_drive()
        
        print('--- SEARCHING FOR: {} ---\n'.format(remote_file))
        secret_download_time_start = time.time()
        search = my_drive.search(remote_file, limit = 10)

        if search:
            document = next(search, None)
            print('--- COPYING {} TO LOCAL MACHINE ---'.format(remote_file))
            operation = document.download(to_path = download_path)
            print('\n--- COPIED FILE SUCCESSFULLY ---')
            print('----------------------------------------------------------------------------------------------\n')
        else:
            print('!!! FILE NOT FOUND !!!\n')
            exit()
        secret_download_time_finish = time.time()

        return (secret_download_time_finish - secret_download_time_start)
        
    def o365_file_ul(self, share_files: list, scopes: list, credentials: tuple) -> float:
        account = Account(credentials)
        
        if not account.is_authenticated:
            account.authenticate(scopes = scopes)
            print('\n--- USER AUTHENTICATION SUCCESSFUL ---\n')

        storage = account.storage()
        my_drive = storage.get_default_drive()
        root = my_drive.get_root_folder()

        share_upload_time_start = time.time()
        for i in share_files:
            operation = root.upload_file(i)
        share_upload_time_finish = time.time()
        print('\n--- SHARES DISTRIBUTED SUCCESSFULLY---')
        print('----------------------------------------------------------------------------------------------\n')

        return (share_upload_time_finish - share_upload_time_start)

    def create_shares(self, threshold: int, shareholders: int, file: str) -> list:
        shares = tss.share_secret(threshold, shareholders, file, Hash.NONE)
        print('\n--- SHARES CREATED ---')
        print('----------------------------------------------------------------------------------------------\n')

        return shares
        
    def encryption(self, shares: list) -> list:
        y = 0
        share_files = []
        for i in shares:
            encrypted_share = hexlify(i)
            output = open('Share {}.txt'.format(y + 1), 'wb')
            share_files.append(output.name)
            output = output.write(encrypted_share)
            y += 1
        
        print('\n--- SHARE ENCRYPTION COMPLETE ---')
        print('----------------------------------------------------------------------------------------------\n')

        return share_files

    def decryption(self, scopes: list, credentials: tuple, share_files: list) -> float:
        download_path = 'C:/Users/dell/Desktop/'
        
        account = Account(credentials)
        
        if not account.is_authenticated:
            account.authenticate(scopes = scopes)

        storage = account.storage()
        my_drive = storage.get_default_drive()
        root = my_drive.get_root_folder()

        encrypted_shares = []
        share_download_time_start = time.time()
        for i in share_files:
            print('--- SEARCHING FOR: {} ---\n'.format(i))
            search = root.search(i, limit = 1)
            if search:
                document = next(search, None)
                print('--- COPYING {} TO LOCAL MACHINE ---\n'.format(i))
                operation = document.download(to_path = download_path)

                with open(i) as file:
                    content = file.read()
                    encrypted_shares.append(content)
            else:
                print('!!! FILE NOT FOUND !!!\n')
                exit()
        share_download_time_finish = time.time()
            
        decrypted_shares = []
        for i in encrypted_shares:
            decrypted_share = unhexlify(i)
            decrypted_shares.append(decrypted_share)
        
        secret_recovery_time_start = time.time()
        reconstructed_contents = tss.reconstruct_secret(decrypted_shares, False)
        output = open('Reconstruct Secret.txt', 'w')
        output = output.write(str(reconstructed_contents.decode('utf_8')))
        secret_recovery_time_finish = time.time()

        print('--- SHARE DECRYPTION COMPLETE ---')
        print('----------------------------------------------------------------------------------------------\n')

        return (share_download_time_finish - share_download_time_start), (secret_recovery_time_finish - secret_recovery_time_start)
        
def main():
    threshold = 3
    shareholders = 5
    remote_file = 'CIS6006 PRES1 Secret.txt'

    latency = []
    overall_time = []
    secret_download_time = []
    share_creation_time = []
    share_upload_time = []
    share_download_time = []
    secret_recovery_time = []

    for i in range(10):
        print('\nITERATION {}\n'.format(i + 1))
        SS_obj = SecretSharing(threshold, shareholders, remote_file)
        latency.append(SS_obj.latency)
        overall_time.append(SS_obj.overall_time)
        secret_download_time.append(SS_obj.secret_download_time)
        share_creation_time.append(SS_obj.share_creation_time)
        share_upload_time.append(SS_obj.share_upload_time)
        share_download_time.append(SS_obj.share_download_time)
        secret_recovery_time.append(SS_obj.secret_recovery_time)

    average_latency = np.mean(latency)
    average_overall_time = np.mean(overall_time)
    average_share_creation_time = np.mean(share_creation_time)
    average_secret_download_time = np.mean(secret_download_time)
    average_share_upload_time = np.mean(share_upload_time)
    average_share_download_time = np.mean(share_download_time)
    average_secret_recovery_time = np.mean(secret_recovery_time)

    print(
    '''TEST: THRESHOLD {}, SHAREHOLDERS {}
      10 ITERATION AVERAGE
      LATENCY: {} (s)
      OVERALL TIME {} (s)
      SECRET DOWNLOAD TIME {} (s)
      SHARE CREATION TIME {} (s)
      SHARE UPLOAD TIME {} (s)
      SHARE DOWNLOAD TIME {} (s)
      SECRET RECOVERY TIME {} (s)
    '''.format(threshold, 
               shareholders, 
               average_latency, 
               average_overall_time, 
               average_secret_download_time, 
               average_share_creation_time, 
               average_share_upload_time, 
               average_share_download_time, 
               average_secret_recovery_time))

if __name__ == '__main__':
    main()