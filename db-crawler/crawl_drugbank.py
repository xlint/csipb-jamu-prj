# crawl_drugbank.py

import time
import pickle
import json
import MySQLdb
import urllib2 as urllib
from collections import defaultdict
import dbcrawler_util as util
from datetime import datetime
from bs4 import BeautifulSoup as bs

outDir = '/home/tor/robotics/prj/csipb-jamu-prj/dataset/drugbank/drugbank_20161002'
db = MySQLdb.connect("localhost","root","123","ijah" )
cursor = db.cursor()

def main():
    drugProteinDict = parseUniprotlinkFile() # contain drug-protein binding info

    drugbankIdList = drugProteinDict.keys()
    # drugbankIdList = ['DB05107','DB08423','DB05127']
    drugData = parseDrugWebpage(drugbankIdList)

    # insertDrug(drugProteinDict)
    # insertCompoundVsProtein(drugProteinDict)

    #
    db.close()

def insertCompoundVsProtein(drugProteinDict):
    idx = 0
    for i,v in drugProteinDict.iteritems():
        idx += 1
        print 'inserting i=', str(idx), 'of', str(len(drugProteinDict))

        qf = 'SELECT com_id FROM compound WHERE com_drugbank_id ='
        qm = '"' + i + '"'
        qr = ''
        sql = qf+qm+qr

        try:
            cursor.execute(sql)
            db.commit()
        except:
            assert False, 'dbErr'
            db.rollback()
        comId = cursor.fetchone()[0]
        comId = '"'+comId+'"'

        for p in v['targetProtein']:
            qf = 'SELECT pro_id FROM protein WHERE pro_uniprot_id ='
            qm = '"' + p + '"'
            qr = ''
            sql = qf+qm+qr
            # print sql

            try:
                cursor.execute(sql)
                db.commit()
            except:
                assert False, 'dbErr'
                db.rollback()

            resp = cursor.fetchone()
            if resp!=None:
                proId = resp[0]
                proId = '"'+proId+'"'

                weight = str(1.0)
                weight = '"'+weight+'"'

                factOrPred = 'fact'
                factOrPred = '"'+factOrPred+'"'                

                #
                qf = 'INSERT INTO compound_vs_protein (com_id,pro_id,weight,type) VALUES ('
                qm = comId+','+proId+','+weight+','+factOrPred
                qr = ')'
                sql = qf+qm+qr

                try:
                    cursor.execute(sql)
                    db.commit()
                except:
                    assert False, 'dbErr'
                    db.rollback()

def insertDrug(drugProteinDict):
    idx = 0
    for i,v in drugProteinDict.iteritems():
        if len(v['targetProtein'])!=0:
            idx += 1
            print 'inserting idx=',str(idx),'of at most', str(len(drugProteinDict))
            
            comId = str(idx)
            comId = comId.zfill(8)
            comId = '"'+'COM'+comId+'"'
            comName = '"'+v['name']+'"'
            comDrugbankId = '"'+i+'"'
            qf = 'INSERT INTO compound (com_id,com_drugbank_id,com_name) VALUES ('
            qm = comId+','+comDrugbankId+','+comName
            qr = ')'
            sql = qf+qm+qr
            # print sql

            util.mysqlCommit(db, cursor, sql)

def parseUniprotlinkFile():
    dpFpath = '/home/tor/robotics/prj/csipb-jamu-prj/dataset/drugbank/drugbank_20161002/uniprot_links.csv'

    now = datetime.now()
    drugProteinDict = dict()
    idx = 0
    with open(dpFpath) as infile:        
        first = True
        hot = ''
        for line in infile:
            if not(first):
                idx += 1
                print 'parsing idx=', idx
                
                line = line.strip();
                quoteIdx = [i for i,c in enumerate(line) if c=='"']; assert(len(quoteIdx)%2==0)
                quoteIdx = [j for i,j in enumerate(quoteIdx) if i%2==0] # take only odd-indexed idx
                
                words = line.split('"')
                words2 = []
                for w in words:
                    i = line.find(w) # just after an opening quote
                    w2 = w
                    if (i-1) in quoteIdx:
                        w2 = w.replace(',','$')
                    if len(w2)!=0:
                        words2.append(w2)
                line = ' '.join(words2)

                words = line.split(','); 
                words = words[0:4]
                words = [w.strip() for w in words]
                words = [w.replace('$',',') for w in words]
                
                drugbankId = words[0]
                name = words[1]
                uniprotId = words[3]

                if hot != drugbankId:
                    hot = drugbankId
                    drugProteinDict[hot] = defaultdict(list)

                if len(drugProteinDict[hot]['name'])==0:
                    drugProteinDict[hot]['name'] = name

                drugProteinDict[hot]['targetProtein'].append(uniprotId)
            first = False
    
    jsonFpath = outDir+'/drugbank_drug_vs_protein_'+str(now.date())+'_'+str(now.time())+'.json'
    with open(jsonFpath, 'w') as f:
        json.dump(drugProteinDict, f, indent=2, sort_keys=True)

    pklFpath = outDir+'/drugbank_drug_vs_protein_'+str(now.date())+'_'+str(now.time())+'.pkl'
    with open(pklFpath, 'wb') as f:
        pickle.dump(drugProteinDict, f)

    return drugProteinDict

def parseDrugWebpage(drugbankIdList): # e.g. http://www.drugbank.ca/drugs/DB05107
    html = None
    comData = dict()
    now = datetime.now()

    nDbId = len(drugbankIdList)
    for idx, dbId in enumerate(drugbankIdList):
        print 'parsing idx=', str(idx+1), 'of', str(nDbId)

        baseURL = 'http://www.drugbank.ca/drugs/'
        url = baseURL+dbId
        html = urllib.urlopen(url)
        # baseFpath = '/home/tor/robotics/prj/csipb-jamu-prj/dataset/drugbank/drugbank_20161002/' 
        # fpath = baseFpath+dbId+ '.html'
        # with open(fpath, 'r') as content_file:
        #     html = content_file.read()

        #
        soup = bs(html, 'html.parser')

        #
        datum = defaultdict(list)

        rowData = []
        trList = soup.find_all('tr')
        for tr in trList:
            trStr = str(tr)
            if 'InChI Key' in trStr or 'CAS' in trStr or 'Chemical Formula' in trStr or 'SMILES' in trStr:
                rowData.append(trStr)

        if len(rowData)>4:
            rowData = rowData[1:5]
        rowData = [d.split('<td>')[1].replace('</td></tr>','') for d in rowData]
        rowData = [d.replace('<div class="wrap">','').replace('</div>','') for d in rowData]
        rowData = [d.replace('InChIKey=','').replace('</div>','') for d in rowData]
        rowData = [d.replace('<sub>','').replace('</sub>','') for d in rowData]
        rowData = ['not-available' if ('wishart-not-available' in d) else d for d in rowData]

        assert len(rowData)==4
        datum['name'] = str(soup.title.string).split()[1]
        datum['CAS'] = rowData[0]
        datum['formula'] = rowData[1]
        datum['InChIKey'] = rowData[2]
        datum['SMILES'] = rowData[3]

        aList = soup.find_all('a')
        cidBaseUrl = 'http://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid='
        sidBaseUrl = 'http://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?sid='
        chemspiderBaseUrl = 'http://www.chemspider.com/Chemical-Structure.'
        uniprotBaseUrl = 'http://www.uniprot.org/uniprot/'
        for a in aList:
            href = str(a.get('href'))
            if cidBaseUrl in href:
                datum['pubchemCid']= str(a.get('href').strip(cidBaseUrl))
            elif sidBaseUrl in href:
                datum['pubchemSid']= str(a.get('href').strip(sidBaseUrl))
            elif chemspiderBaseUrl in href:
                datum['chemspiderId'] = str(a.get('href').strip(chemspiderBaseUrl).strip('.html'))
            elif uniprotBaseUrl in href:
                datum['uniprotTargets'].append( str(a.get('href').strip(uniprotBaseUrl)) )

        comData[dbId] = datum

        if (idx%100)==0 or idx==(nDbId-1):
            jsonFpath = outDir+'/drugbank_drug_data_'+str(now.date())+'_'+str(now.time())+'.json'
            with open(jsonFpath, 'w') as f:
                json.dump(comData, f, indent=2, sort_keys=True)

            pklFpath = outDir+'/drugbank_drug_data_'+str(now.date())+'_'+str(now.time())+'.pkl'
            with open(pklFpath, 'wb') as f:
                pickle.dump(comData, f)

    return comData

# def parseDrugbankVocab():
#     fpath = '/home/tor/robotics/prj/csipb-jamu-prj/dataset/drugbank/drugbank_20161002/drugbank_vocabulary.csv'

#     with open(fpath) as infile:      
#         first = True
#         idx = 0
#         for line in infile:
#             if not(first):
#                 idx += 1
#                 print 'updating idx=', idx

#                 line = line.strip()
#                 words = line.split(',')
#                 words = words[0:4]

#                 drugbankId = words[0]
#                 cas = words[3]
#                 cas = cas.replace('"','')

#                 if len(cas)!=0 and len(drugbankId)!=0:
#                     drugbankId = '"'+drugbankId+'"'
#                     cas = '"'+cas+'"'

#                     qf = 'UPDATE compound SET '
#                     qm = 'com_cas_id='+cas
#                     qr = ' WHERE com_drugbank_id='+drugbankId
#                     q = qf+qm+qr
#                     # print q

#                     util.mysqlCommit(db, cursor, q)

#             first = False

if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
