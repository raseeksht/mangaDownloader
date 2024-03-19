import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
from PIL import Image
import time
import threading
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

tempImageDir = "temp_img"

url = "https://mangaclash.com/?post_type=wp-manga&s="


def getLastPartFromUrl(link):
    if link.endswith("/"):
        link = link[:-1]
    return link.split("/")[-1]

def getChapterNumber(link):
    chapter = getLastPartFromUrl(link) #Example : gets "chapter-12-5"
    chapter = chapter.split("chapter-")[-1]  # Removes "chapter-" -> Remaining "12-5"
    if "-" in chapter: #means chapter value is in float
        chapter = float(chapter.replace("-","."))
    else:
        chapter = int(chapter)
    return chapter


def askForNumber(maxNum,allowFloat=False):
    if maxNum == 1:
        print("only 1 choice is available.Choosing 1 by default..")
        time.sleep(2)
        return 1
    while True:
        try:
            userChoice = input(f"choose 1 ... {maxNum} : ")
            try:
                userChoice = int(userChoice)
            except Exception as e:
                if allowFloat:
                    userChoice = float(userChoice)
                
            # print(isinstance(userChoice,float))

            if (userChoice > maxNum):
                print('Unavailable Choice: ',userChoice)
                continue
            else:
                return userChoice
        except Exception as e:
            print("alphabets and special symbol are not accepted...")

def mangaclash():
    searchTerm = input("Enter Manga to download: ")

    searchUrl = url+urllib.parse.quote(searchTerm)

    res = requests.get(searchUrl)

    soup = BeautifulSoup(res.content,"html.parser")

    noOfResult = soup.find('div',class_="tab-wrap").div.h1.text

    print(noOfResult.strip())

    # row c-tabs-item__content
    mangasContainer = soup.find_all("div",{"class":"c-tabs-item__content"})
    links = []
    for index,manga in enumerate(mangasContainer):
        mangaLink = manga.find("div",{"class":"post-title"}).h3.a
        print(f"{index+1}. {mangaLink.text}")
        links.append(mangaLink['href'])

    # usrCh = int(input("Choose any: "))
    print(noOfResult)
    usrCh = askForNumber(len(mangasContainer))
    return links[usrCh-1]


def mangaClashSingleChapter(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.content,"html.parser")
    folderName = soup.find("h1",{"id":"chapter-heading"}).text
    if not os.path.exists(tempImageDir):
        os.mkdir(tempImageDir)
    else:
        os.chdir(tempImageDir)
        os.system("rm *.*")
        os.chdir("..")
    if not os.path.exists("downloads"):
        os.mkdir("downloads")
    imgContainer = soup.find_all("div",{"class":"page-break"})
    imgListForPdf = []
    images = []
    imgThreads = []
    for imgDiv in imgContainer:
        img = imgDiv.img
        imgUrl = img['data-src'].strip()
        imageName = imgUrl.split("/")[-1]
        
        cmd = f"wget '{imgUrl}' -c -O '{tempImageDir}/{imageName}'"
        thread = threading.Thread(target=downloadMedia,args=(cmd,))
        imgThreads.append((thread,imageName))

    
    for thread in imgThreads:
        thread[0].start()
    
    for thread in imgThreads:
        thread[0].join()
    
    for thread in imgThreads:
        im = Image.open(f"{tempImageDir}/{thread[1]}")
        im.convert('RGB')
        imgListForPdf.append(im)
    
    try:
        imgListForPdf[0].save(f"./downloads/{folderName}.pdf",save_all=True,append_images=imgListForPdf[1:])
    except Exception as e:
        print(e)

        print(f'cannot save {folderName}')
        from altpdfgen import generatePdf
        obj = generatePdf(tempImageDir,f"./downloads/{folderName}.pdf")
        obj.convert_to_pdf()

        # exit()
    os.system(f"rm {tempImageDir} -rf")
    print("deleted temp image folder")

def downloadMedia(cmd):
    os.system(cmd)

def convert_to_pdf(image_paths, output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    for image_path in image_paths:
        img = Image.open(image_path)
        # img = image_path
        img_width, img_height = img.size
        aspect_ratio = img_width / img_height

        # Calculate the scaling factor to fit the image within the PDF page
        if img_width > img_height:
            img_width = width
            img_height = img_width / aspect_ratio
        else:
            img_height = height
            img_width = img_height * aspect_ratio

        c.setPageSize((img_width, img_height))
        c.drawImage(image_path, 0, 0, width=img_width, height=img_height)

        c.showPage()

    c.save()

def mangaClashDownload(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.content,"html.parser")
    ul = soup.find('ul',{"class":"version-chap"})
    li = ul.find_all("li")[::-1]
    liChapters = [getChapterNumber(li_elem.a['href']) for li_elem in li]
    liChaptersUrls = [li_elem.a['href'] for li_elem in li]
    liChaptersFloats = list(map(str,(filter(lambda x:isinstance(x,float),liChapters)))) #stores float chapters in list and converts float to str
    print(f"{len(li)} Chapters available including chapters ({', '.join(liChaptersFloats)})")

    print(f"\nLatest Chapter: {li[-1].a.text.strip()}\n")
    
    print("1. Download All")
    print("2. Select a single Chapter")
    print("3. from x to y")
    usrCh = askForNumber(3)
    if usrCh == 1:
        for each in li:
            a = each.a
            chUrl = a['href']
            print(f"Downloading {a.text}")
            mangaClashSingleChapter(chUrl)
    
    elif usrCh == 2:
        chapterChoice = askForNumber(getChapterNumber(li[-1].a['href']),allowFloat=True)
        try:
            chapterUrl = liChaptersUrls[liChapters.index(chapterChoice)]
            mangaClashSingleChapter(chapterUrl)
        except Exception as e:
            print(e)
            print(f"Chapter {chapterChoice} is unavailable")
            print("list of available chapters\n",liChapters)
        
    else:
        while True:
            print("from: ",end="")
            frm = askForNumber(getChapterNumber(li[-1].a['href']),allowFloat=True)
            print("to: ",end="")
            to = askForNumber(getChapterNumber(li[-1].a['href']),allowFloat=True)
            try:
                indexOffrm = liChapters.index(frm)
                indexOfto = liChapters.index(to)
                break                
            except Exception:
                print(f"Chapter {frm} or {to} is unavailable")
                print("list of available chapters\n",liChapters)
                continue

        # if user chooses frm = 5, to = 8 then let liChapters = [1,2,3,4,5,6,7.5,8,9,10]
        # then index of 5 is 4 and index of 8 is 7
        # now create new list liChapters[indexof(frm->5):indexof(to->8)+1]
        # also create corresponding liChaptersUrls[(frm->5):indexof(to->8)+1]
        # newChapters = liChapters[indexOffrm:indexOfto+1]
        newChaptersUrls = liChaptersUrls[indexOffrm:indexOfto+1]

        if frm > to:
            print("Invalid Choice:")
            print(f"From : {frm} ")
            print(f"To   : {to}")
            sys.exit()
        elif frm == to: #download single chapter in this case
            chapterUrl = liChaptersUrls[liChapters.index(chapterChoice)]
            mangaClashSingleChapter(chapterUrl)
        else:
            for chapter in newChaptersUrls:
                mangaClashSingleChapter(chapter)



link = mangaclash()
mangaClashDownload(link)

# print(link)

# print(a)


# print(len(mangasContainer))