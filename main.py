import json

import multiprocessing
import requests
import time
from bs4 import BeautifulSoup
from multiprocessing import Queue


def fetch_detail_url(url):
    html = None
    print('Processing detail..{}'.format(url))
    try:
        r = requests.get(url)
        if r.status_code == 200:
            html = r.text
    except Exception as ex:
        print('Exception while accessing raw html')
        print(str(ex))
    finally:
        return html

def create_data(promos, main_url):
    img_list = []
    for promo in promos:
        link_detail = promo['href']
        if "promo_detail" in link_detail:
            # Just to make sure grab detail from BANK MEGA WEBSITE
            detail_url = "{}{}".format(main_url,
                                       promo['href'])
            detail_html = fetch_detail_url(detail_url)
            soup = BeautifulSoup(detail_html, 'lxml')
            area = soup.select(".area")
            img_banner = soup.select(".keteranganinside")
            periode = soup.select(".periode")
            img_list.append({
                "title": promo.img['title'],
                "imageurl": img_banner[0].img['src'],
                "area": area[0].text.strip(),
                "periode": periode[0].text.strip(),
            })
        else:
            # Else, just grab detail info from thumbnail
            img_list.append({
                "title": promo.img['title'],
                "imageurl": promo.img['src'],
                "area": "",
                "periode": ""
            })
    return img_list

def promo_processing():
    main_url = "https://www.bankmega.com/"
    url = '{}promolainnya.php'.format(main_url)
    lists = []
    try:
        r = requests.get(url)
        if r.status_code == 200:
            html = r.text
            soup = BeautifulSoup(html, 'lxml')
            divs = soup.select('#subcatpromo div')
            idx = 1
            for link in divs:
                obj = {link.img['title']: []}
                lists.append(obj)
                req_url = "{}?product=0&subcat={}".format(url, idx)
                r = requests.get(
                    req_url
                )
                if r.status_code == 200:
                    html = r.text
                    soup = BeautifulSoup(html, 'lxml')

                    #Find how many paging inside html
                    table = soup.find("table", {"class": "tablepaging"})
                    column_paging_in_html = [column for column in table.findAll("td")]
                    count_column_paging_in_html = len(column_paging_in_html)
                    count_column_paging_in_html -= 2 #Exclude Prev and Next

                    mergedlist = []
                    for num in range(count_column_paging_in_html):
                        num += 1
                        r = requests.get(
                            "{}&page={}".format(req_url, num)
                        )
                        if r.status_code == 200:
                            html = r.text
                            soup = BeautifulSoup(html, 'lxml')
                            promos = soup.select('ul#promolain a')
                            mergedlist += create_data(promos, main_url)

                    obj[link.img['title']] = mergedlist
                idx += 1
                # if idx > 1:
                #     break
    except Exception as ex:
        print('Exception')
        print(str(ex))
    finally:
        return lists



#===================MULTIPROCESSING=====================
def worker_process(link, main_url, url, idx, lists, queue):
    obj = {link.img['title']: []}
    lists.append(obj)
    req_url = "{}?product=0&subcat={}".format(url, idx)
    r = requests.get(
        req_url
    )
    print(req_url)
    if r.status_code == 200:
        html = r.text
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find("table", {"class": "tablepaging"})
        column_paging_in_html = [
            column
            for column in table.findAll("td")
        ]
        count_column_paging_in_html = len(
            column_paging_in_html)
        count_column_paging_in_html -= 2  # Exclude Prev and Next

        mergedlist = []
        for num in range(count_column_paging_in_html):
            num += 1
            r = requests.get(
                "{}&page={}".format(req_url, num)
            )
            if r.status_code == 200:
                html = r.text
                soup = BeautifulSoup(html, 'lxml')
                promos = soup.select('ul#promolain a')
                mergedlist += create_data(promos, main_url)

        obj[link.img['title']] = mergedlist
        queue.put(obj)

def promo_multiprocessing():
    main_url = "https://www.bankmega.com/"
    url = '{}promolainnya.php'.format(main_url)
    lists = []
    try:
        r = requests.get(url)
        if r.status_code == 200:
            html = r.text
            soup = BeautifulSoup(html, 'lxml')
            divs = soup.select('#subcatpromo div')
            idx = 1
            queue = Queue()
            jobs = []
            for link in divs:
                p = multiprocessing.Process(target=worker_process,
                                            args=(link, main_url, url, idx,
                                                  lists, queue)
                                            )
                jobs.append(p)
                p.start()
                idx += 1
                # if idx > 2:
                #     break

            for p in jobs:
                lists.append(queue.get())

            for p in jobs:
                p.join()


    except Exception as ex:
        print('Exception')
        print(str(ex))
    finally:
        return lists


if __name__ == '__main__':
    start_time = time.time()

    # Use this if you want to use multiprocessing
    print(json.dumps(promo_multiprocessing()))

    # Use this if don't want multiprocessing
    #print(json.dumps(promo_processing()))

    total_execute = time.time() - start_time
    print("------End Execution time {} seconds -----".format(total_execute))
