#!python3

import sys
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import *
import time

from datetime import date
import mailbox
from email.header import decode_header
import email

import datetime
import getpass
import imaplib

interesting_senders = [
    '楽天特典付きキャンペーンニュース <incentive@emagazine.rakuten.co.jp>',
    '楽天スーパーポイントギャラリーニュース <point-g@emagazine.rakuten.co.jp>',
    '楽天カレンダーお得なニュース <calendar-info@emagazine.rakuten.co.jp>',
    'ポイント10倍ニュース <pointo10henbai@emagazine.rakuten.co.jp>',
    'メールdeポイント <info@pointmail.rakuten.co.jp>',
    '楽天ダイヤモンド・プラチナ優待ニュース <platinum-news@emagazine.rakuten.co.jp>',
]
#not interesting:
#Infoseek メールdeポイント事務局 <info@pointmail.rakuten.co.jp>

# dont include http or https as both will be checked
banner_urls = [
    "://point-g.rakuten.co.jp/mailmag/common/pg_click_banner_btn.png",
    "://point-g.rakuten.co.jp/mailmag/common/pg_click_banner_btn_2.png",
    "://point-g.rakuten.co.jp/mailmag/common/pg_click_banner_btn_3.png",
    "://image.infoseek.rakuten.co.jp/content/tmail/htmlmail/maildepoint_btn2.gif",
]

class MyEmail:
    def __init__(self, msgstr):
        self.body = None

        #print(msgstr)
        self.msg = email.message_from_string(msgstr)

        # extract subject and from
        self.subject, charset = email.header.decode_header(self.msg['Subject'])[0]
        if type(self.subject) != str:
            charset = 'utf-8' if not charset else charset
            self.subject = self.subject.decode(charset)

        #print(self.msg['From'])
        header_from = email.header.decode_header(self.msg['From'])

        # set FROM from header
        self.fr, charset = header_from[0]
        if type(self.fr) != str:
            charset = 'utf-8' if not charset else charset
            self.fr = self.fr.decode(charset)

        # set SENDER from header
        if len(header_from) > 1:
            sender, charset = header_from[1]
            charset = 'utf-8' if not charset else charset
            sender = sender.decode(charset)
            self.sender = sender
        else:
            self.sender = "<{}>".format(self.msg['Sender'])

        #print('Raw Date:', msg['Date'])
        # convert to local date-time
        date_tuple = email.utils.parsedate_tz(self.msg['Date'])
        if date_tuple:
            self.local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            #print("Local Date:", local_date.strftime("%a, %d %b %Y %H:%M:%S"))
        # ['Date', 'Received', 'Content-Type', 'From', 'To', 'Subject', 'Message-ID', 'Sender']
    
    def checkSenderSubject(self):
        senderchk = False
        subjectchk = False

        # check sender
        fullsender = "{} {}".format(self.fr, self.sender)
        senderchk = fullsender in interesting_senders
        #print("{}".format(fullsender))

        subjectchk = (
            ("【クリック" in self.subject and "ポイント" in self.subject)
            or ("メールdeポイント" in self.subject and self.subject.count("ポイント") >= 2)
            or "【1ポイントゲット！】" in self.subject
            or "クリックして1ポイント" in self.subject
        )
        
        return senderchk, subjectchk

    def tryAnyShop(self):
        if not "text/html" in self.msg['Content-Type']:
            return None
        self.retrieveBody()
        if not "掲載店舗の商品いずれかをクリックしていただいた方" in self.body:
            return None

        for line in self.body.splitlines():
            if '<tr><td><img' in line and 'href' in line:
                for u in line.split('"'):
                    if "http" in u and not (".png" in u or ".gif" in u or ".jpg" in u):
                        return u
                break
        return None

    def tryTextualURL(self):
        # text/html can contain this as well!!!
        #if not "text/plain" in self.msg['Content-Type']:
        #    return None
        self.retrieveBody()
        nexturl = False
        for line in self.body.splitlines():
            if '↓ クリックでもれなく1ポイントGet!! ↓' in line or '▼楽天ポイント獲得はこちら▼' in line:
                nexturl = True
            elif nexturl and "http" in line:
                if 'href="' in line: # text/html can contain this as well!!!
                    line = line.split('"')[1]
                return line
            else:
                nexturl = False
        return None

    def tryBannerURL(self):
        if not "text/html" in self.msg['Content-Type']:
            return None
        self.retrieveBody()
        banner_url = None
        for banner_url in banner_urls:
            if banner_url in self.body:
                break
        if not banner_url:
            return None
        for line in self.body.splitlines():
            if banner_url in line:
                for u in line.split('"'):
                    if "http" in u and not (".png" in u or ".gif" in u or ".jpg" in u):
                        return u
                break
        return None
    
    def retrieveBody(self):
        if self.body:
            return
        charset = "utf-8"
        # Content-Type: text/plain; charset="utf-8"
        for pref in self.msg['Content-Type'].split():
            if "charset=" in pref:
                charset = pref.split('=')[1]
                break
        self.body = self.bodyFromMsg(self.msg).decode(charset)

    def bodyFromMsg(self, b):
        body = ""
        if b.is_multipart():
            for part in b.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True)  # decode
                    break
        # not multipart - i.e. plain text, no attachments, keeping fingers crossed
        else:
            body = b.get_payload(decode=True)
        return body

    def __repr__(self):
        r = ''
        if '様' in self.subject:
            r += 'Subject: {}\n'.format('<hidden for privacy>')
        else:
            r += 'Subject: {}\n'.format(self.subject)
        r += '   From: {} {}\n'.format(self.fr, self.sender)
        r += '   Date: {}'.format(self.local_date.strftime("%Y-%m-%d %H:%M"))
        return r

class MyMailbox:
    def __init__(self, server):
        self.conn = imaplib.IMAP4_SSL(server)
    def connect(self, us, pw, folder):
        self.conn.login(us, pw)
        #l = self.conn.list()
        #print(l)
        readonly = False
        ret = self.conn.select(folder, readonly)
    def close(self):
        self.conn.close()
        self.conn.logout()

    def filter(self):
        #date = (datetime.date.today() - datetime.timedelta(2)).strftime("%d-%b-%Y")
        #(res, data) = conn.search(None, ('UNSEEN'), '(SENTSINCE {0})'.format(date), '(FROM {0})'.format("calendar-info@emagazine.rakuten.co.jp".strip()))
        #(res, data) = conn.search(None, ('UNSEEN'), '(SENTSINCE {0})'.format(date))
        res, data = self.conn.search(None, ('UNSEEN'))
        if res != 'OK':
            print(res, data)
            return None
        ids = data[0].split()
        return ids

    def parseMails(self, ids, markS=False):
        interesting_count, sender_count, subject_count  = (0, 0, 0)
        fids = []
        urls = []
        for id in ids:
            rv, data = self.conn.fetch(id, '(RFC822)')
            if rv != 'OK':
                print("ERROR getting message", id)
                return -1
            # fetch seems to add \Seen flag. Undo.
            self.markUnseen(id)

            msgstr = data[0][1].decode('utf-8')
            memail = MyEmail(msgstr)

            print()
            print(memail)
            senderchk, subjectchk = memail.checkSenderSubject()
            if not senderchk and not subjectchk:
                print("  Uninteresting. SKIP.")
                continue

            interesting_count += 1
            if subjectchk:
                subject_count += 1
            if senderchk:
                sender_count += 1

            url = memail.tryBannerURL()
            if not url:
                url = memail.tryTextualURL()
                if not url:
                    url = memail.tryAnyShop()
                    if not url:
                        #print(memail.body)
                        print("  no idea. check by yourself!")
                        if markS:
                            print("  Mark email as read.")
                            self.markSeen(id)
                        continue

            print("  FOUND URL.")
            urls.append(url)
            fids.append(id)

        return fids, urls, interesting_count, sender_count, subject_count

    def markUnseen(self, id):
        self.conn.store(id,'-FLAGS','\Seen')
    def markSeen(self, id):
        self.conn.store(id,'+FLAGS','\Seen')


class MyChrome:
    def __init__(self):
        pass
    def prepare(self, profilepath="./chrome-profile", headless=False):
        # Chrome立ち上げ
        options = Options()
        if headless:
            options.add_argument('--headless=new')
            #options.add_argument("--no-sandbox")
            #options.add_argument('--lang=en_US')
            #options.add_argument('--window-size=1920x1080');
        options.add_argument('--user-data-dir={}'.format(profilepath))
        if os.name == "posix":
            self.chrome = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=options)
            #self.chrome = webdriver.Chrome(executable_path="./chromedriver", options=options)
        else:
            self.chrome = webdriver.Chrome(executable_path="./chromedriver.exe", options=options)

    def get(self, url):
        self.chrome.get(url)

    def shutdown(self):
        try:
            self.chrome.quit()
        except:
            pass


def run(server, user, pw, folder, profile, rakutenPw, markS):
    mail = MyMailbox(server)
    mail.connect(user, pw, folder)
    ids = mail.filter()
    if len(ids) > 0:
        print("Checking {} unseen emails...".format(len(ids)))
        fids, urls, interesting, sender, subject = mail.parseMails(ids, markS)

        #headless = True if len(fids) == interesting and len(fids) == sender and len(fids) == subject else False
        #headless = True if len(fids) == interesting else False
        headless = True

        print()
        print("Stats:")
        print("Total unseen emails: {}".format(len(ids)))
        print("Interesting: {} (sender: {}, subject: {})".format(interesting, sender, subject))
        print("# URLs: {}".format(len(urls)))

        if len(fids) > 0:
            if headless:
                print()
                print("RUN IN HEADLESS MODE.")
                #headless = False
            print()
            chrome = MyChrome()
            chrome.prepare(profile, headless)
            for fid, url in zip(fids, urls):
                print("Opening url...")
                print(url)
                chrome.get(url)
                # check if there is a password input field
                pwsite = chrome.chrome.find_elements_by_xpath("//input[@type=\"password\"]")
                if len(pwsite) > 0:
                    print("password field FOUND. try logging in...")
                    try:
                        uname = chrome.chrome.find_element_by_id("loginInner_u")
                        upass = chrome.chrome.find_element_by_id ("loginInner_p")
                    except NoSuchElementException:
                        try:
                            uname = chrome.chrome.find_element_by_id("u")
                            upass = chrome.chrome.find_element_by_id ("p")
                        except NoSuchElementException:
                            print('could not find element ids!')
                            return 1
                        
                    ulogin = chrome.chrome.find_element_by_class_name("loginButton")
                    if uname and upass and ulogin:
                        uname.send_keys(user)
                        upass.send_keys(rakutenPw)
                        ulogin.click()
                    else:
                        print("LOGIN FAILED. quit.")
                        return 2

                # new site:
                pwsite = chrome.chrome.find_elements_by_xpath("//input[@id=\"user_id\"]")
                if len(pwsite) > 0:
                    print("INPUT field FOUND. try logging in...")
                    time.sleep(2)
                    try:
                        uname = chrome.chrome.find_element_by_id("user_id")
                        unext = chrome.chrome.find_element_by_id("cta001")
                    except NoSuchElementException:
                        print('could not find element user_id or cta')
                        return 1
                    uname.send_keys(user)
                    unext.click()
                    time.sleep(2)
                    try:
                        upass = chrome.chrome.find_element_by_id("password_current")
                        ulogin = chrome.chrome.find_element_by_id("cta011")
                        #ulogin = chrome.chrome.find_elements_by_xpath("//div[@id=\"cta\"]")[1]
                    except NoSuchElementException:
                        print('could not find element user_id or cta2')
                        return 1
                    upass.send_keys(rakutenPw)
                    ulogin.click()
                    time.sleep(2)

                print("Mark email as read...")
                mail.markSeen(fid)
                # wait for opening web pages to complete loading
                #webdriver.support.ui.WebDriverWait(self.chrome, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
            chrome.shutdown()
            print("DONE.")
    else:
        print("No unseen mails.")

    mail.close()
    return 0

def main(args):

    profile = './chrome-profile'
    server = "imap.gmx.net"
    folder = "INBOX"
    user = "email@gmail.com"
    pw = "password"
    markS = False

    if len(args) >= 6:
        profile = args[1]
        server = args[2]
        folder = args[3]
        user = args[4]
        pw = args[5]
        rakutenPw = args[6]
    if len(args) >= 8:
        markS = args[7] == "true" or args[7] == "True"

    # print("{} on {}".format(user, server))
    return run(server, user, pw, folder, profile, rakutenPw, markS)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
