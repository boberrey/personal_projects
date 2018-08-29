#!/usr/bin/env python

"""
Utility functions for biopython's NCBI Entrez utilities

Ben Ober-Reynolds
20170331
"""

from Bio import Entrez
from pubmed_lookup import PubMedLookup, Publication
from collections import OrderedDict

###################################
####### Searching functions #######
###################################

def entrezSearch(term, reldate, db='pubmed', sort='Most Recent', 
    retmode='xml', retmax=20, datetype='edat'):
    """
    Perform entrez esearch using provided term and settings
    Inputs:
        term (str) - formatted search term
        reldate (int) - the number of days previously that define the max 
            date range
        db (str) - the database to query
        sort (str) - the way to sort the results
        retmode (str) - the retrieval mode
        retmax (int) - the maximum number of search results
        datetype (str) - the date type (e.g. publish date) relevant to the 
            search
    Outputs: 
        A list of found UIDs
    """
    handle = Entrez.esearch(db=db, sort=sort, retmode=retmode, 
            retmax=retmax, term=term, reldate=reldate, 
            datetype=datetype)
    return Entrez.read(handle)['IdList']


def search_by_keywords(keywords, reldate, database='pubmed', 
    sort_type='Most Recent', retmax=20, datetype='edat'):
    """
    Query the Entrez pubmed database by a list of provided keywords. Uses the
    [Title/Abstract] search classifier
    Inputs:
        keywords (list) - list of key words to search
        reldate (int) - the number of days previously that define the max 
            date range
        database (str) - the database to query
        sort_type (str) - the way to sort the results
        retmax (int) - the maximum number of search results
        datetype (str) - the date type (e.g. entrez date) relevant to the 
            search
    Outputs:
        results_by_term (dict) - dictionary of UID lists keyed by search term
    """
    results_by_term = OrderedDict()
    for term in keywords:
        formatted_term = '+'.join(term.split()) + "[Title/Abstract]"
        results_by_term[term] = entrezSearch(db=database, sort=sort_type, 
            retmode='xml', retmax=retmax, term=formatted_term, reldate=reldate, 
            datetype=datetype)
    return results_by_term


def search_by_authors(authors, reldate, database='pubmed', 
    sort_type='Most Recent', retmax=20, datetype='edat'):
    """
    Query the Entrez pubmed database by a list of provided authors.
    Inputs:
        authors (list) - list of authors to search
        reldate (int) - the number of days previously that define the max 
            date range
        database (str) - the database to query
        sort_type (str) - the way to sort the results
        retmax (int) - the maximum number of search results
    Outputs:
        results_by_term (dict) - dictionary of UID lists keyed by search term
    """
    results_by_term = OrderedDict()
    for term in authors:
        formatted_term = term + '[Author]'
        results_by_term[term] = entrezSearch(db=database, sort=sort_type, 
            retmode='xml', retmax=retmax, term=formatted_term, reldate=reldate, 
            datetype=datetype)
    return results_by_term


def search_by_journal_and_topic(journal_topic_dict, reldate, database='pubmed', 
    sort_type='Most Recent', retmax=20, datetype='edat'):
    """
    Query the Entrez pubmed database by topics from a specific journal
        journal_topic_dict (dict) - dictionary of topics keyed by journal
        reldate (int) - the number of days previously that define the max 
            date range
        database (str) - the database to query
        sort_type (str) - the way to sort the results
        retmax (int) - the maximum number of search results
    Outputs:
        results_by_term (dict) - dictionary of UID lists keyed by search term
    """
    results_by_term = OrderedDict()
    for journal, topic_list in journal_topic_dict.items():
        formatted_term = journal + '[Journal] AND ({})'.format(' OR '.join(topic_list))
        results_by_term[formatted_term] = entrezSearch(db=database, sort=sort_type, 
            retmode='xml', retmax=retmax, term=formatted_term, reldate=reldate, 
            datetype=datetype)
    return results_by_term

##################################
####### Fetching functions #######
##################################

def fetch_data_for_ID_list(ID_list, database='pubmed', retmode='xml', 
    rettype='xml', retmax=20):
    """
    Fetch data for a list of UIDs
    Inputs:
        ID_list (list) - a list of UIDs to search
        db (str) - the database to query
        retmode (str) - the retrieval mode
        rettype (str) - the retrieval type
        retmax (int) - the maximum number of search results
    Outputs:
        result_list (list) - list of 'Bio.Entrez.Parser.StructureElement'
            objects
    """
    result_list = []
    for ID in ID_list:
        result_list.append(entrezFetch(ID, db=database, retmode=retmode, 
            rettype=rettype, retmax=retmax))
    return result_list


def entrezFetch(ID, db='pubmed', retmode='xml', rettype='xml', retmax=20):
    """
    Perform entrez efetch using provided ID and settings
    Inputs:
        ID (str) - the ID to search for
        db (str) - the database to query
        retmode (str) - the retrieval mode
        rettype (str) - the retrieval type
        retmax (int) - the maximum number of search results
    Outputs:
        A 'Bio.Entrez.Parser.StructureElement' object
    """
    handle = Entrez.efetch(id=ID, db=db, retmode=retmode, rettype=rettype, 
        retmax=retmax)
    return Entrez.read(handle)


# or use the pubmed_lookup module I found after the fact...
def fetch_pubs_from_ID_list(ID_list, entrez_email):
    """
    Fetch Publication objects for a list of UIDs
    Inputs:
        ID_list (list) - a list of UIDs to search
        entrez_email (str) - the current entrez email
    Outputs:
        result_list (list) - list of Publication
            objects
    """
    result_list = []
    for ID in ID_list:
        lookup = PubMedLookup(ID, entrez_email)
        # 20171011: It seems like there are some bad lookup results
        # Adding this try/catch gets things working normally apparently...
        try:
            result_list.append(Publication(lookup))
        except:
            pass
    return result_list



###################################
####### Information Getters #######
###################################

# No longer necessary with pubmed_lookup module...

def get_title(data_record):
    # Get the article title from a pubmed article
    return data_record['PubmedArticle'][0]['MedlineCitation']['Article']['ArticleTitle']


def get_journal(data_record):
    # Get the journal title from a pubmed article
    return data_record['PubmedArticle'][0]['MedlineCitation']['Article']['Journal']['Title']


def get_authors(data_record):
    # Get an author list from a pubmed article
    author_list = []
    # The data record contains lots of information about each author
    for author in data_record['PubmedArticle'][0]['MedlineCitation']['Article']['AuthorList']:
        author_list.append(author['LastName'] + ' ' + author['Initials'])
    return author_list


def get_url(data_record):
    # Get the article url from a pubmed article
    url_tail = ''
    for elocation in data_record['PubmedArticle'][0]['MedlineCitation']['Article']['ELocationID']:
        # Only elocations that are 'doi' format can be easily linked to currently
        if elocation.attributes['EIdType'] == 'doi':
            url_tail = str(elocation)
    return 'dx.doi.org/' + url_tail

def get_abstract(data_record):
    # Get the abstract from a pubmed article
    return data_record['PubmedArticle'][0]['MedlineCitation']['Article']['Abstract']['AbstractText'][0]
