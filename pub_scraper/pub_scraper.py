#!/usr/bin/env python

"""
Scrape NCBI pubmed for papers of interest

Inputs:
   

Outputs:
   

Ben Ober-Reynolds
20170331
"""

import os
import sys
import argparse
import entrezUtils
import smtplib
from pubmed_lookup import PubMedLookup, Publication
from collections import OrderedDict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from Bio import Entrez



def main():  
    # set up command line argument parser
    parser = argparse.ArgumentParser(description='Pubmed scraper')
    group = parser.add_argument_group('required arguments:')
    group.add_argument('-sf', '--search_file', required=True,
        help='File containing settings and search terms')
    group = parser.add_argument_group('optional arguments')

    # print help if no arguments provided
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit()

    # parse command line arguments
    args = parser.parse_args()

    # Settings and variables:
    date_format = "%Y/%m/%d"
    database = 'pubmed'
    sort_type = 'Most Recent'
    email_server = 'smtp.gmail.com'
    smtp_port = 465
    message_subject = 'pub scraper report - {}'.format(
        date.today().strftime(date_format))

    # Parse settings file and initialize variables
    settings_dict = parse_search_file(args.search_file)
    
    entrez_email = settings_dict['entrez_email_address'][0]
    send_to_emails = settings_dict['send_to_email_address']
    search_keywords = settings_dict['search_keywords']
    search_authors = settings_dict['search_authors']
    journal_topic_list = settings_dict['journal_and_topics']
    pub_days_ago = int(settings_dict['pub_days_ago'][0])
    sender_email = settings_dict['sender_email'][0]
    sender_pswd = settings_dict['sender_pswd'][0]

    # Parse journal_topic_list:
    journal_topic_dict = parse_journal_topics(journal_topic_list)

    # Set entrez email:
    Entrez.email = entrez_email

    # Search by keywords:
    keyword_results = entrezUtils.search_by_keywords(search_keywords, 
        reldate=pub_days_ago, database=database, sort_type=sort_type)

    # Search by authors:
    author_results = entrezUtils.search_by_authors(search_authors, 
        reldate=pub_days_ago, database=database, sort_type=sort_type)

    # Search by journal plus topics:
    journal_topic_results = entrezUtils.search_by_journal_and_topic(
        journal_topic_dict, reldate=pub_days_ago, database=database, 
        sort_type=sort_type)
    
    # Fetch data records for identified UIDs
    keyword_publications = build_result_dict(keyword_results, database)
    author_publications = build_result_dict(author_results, database)
    journal_topic_publications = build_result_dict(journal_topic_results, 
        database)
    
    # All results:
    all_results_dict = OrderedDict([
        ('Keyword Searches', keyword_publications),
        ('Author Searches', author_publications),
        ('Journal and Topic Searches', journal_topic_publications)
    ])

    # Get the total number of hits:
    total_hits = 0
    for group, result_dict in all_results_dict.items():
        for term, pub_list in result_dict.items():
            total_hits += len(pub_list)

    # Now send information by email:
    message = MIMEMultipart('alternative')
    message['subject'] = message_subject + " ({} hits)".format(total_hits)
    message['To'] = ','.join(send_to_emails)
    message['From'] = sender_email

    # Construct the body of the report
    message_body = construct_email_body(all_results_dict, pub_days_ago)
    html_body = MIMEText(message_body, 'html')
    message.attach(html_body)

    # Actually send the email:
    try:
        server = smtplib.SMTP_SSL(email_server, smtp_port)
        server.ehlo()
        server.login(sender_email, sender_pswd)
        server.sendmail(sender_email, send_to_emails, message.as_string())
        server.quit()
    except:
        print("email failed to send")



def parse_search_file(search_file):
    """
    Read in settings from a provided search_file. Relevant settings will
    be added to a settings_dict for further parsing in the main function.
    Inputs:
        search_file (str) - filename for the search file
    Outputs:
        settings_dict (dict) - Dictionary of settings extracted from 
            the setting_file
    """
    settings_dict = {}

    with open(search_file, 'r') as f:
        for line in f:
            # The '#' character denotes a line that should be ignored in the 
            # settings file
            if line[0] == '#':
                continue
            # The '$' character denotes a setting header line-- every line
            # following the header line is added to that header's list in the
            # settings_dict
            if line[0] == '$':
                key = line.strip().split()[1]
                settings_dict[key] = []
                while True:
                    try:
                        line = f.readline().strip()
                        if line[0] == '#':
                            continue
                        if line == '':
                            break
                        settings_dict[key].append(line)
                    except EOFError:
                        break

    return settings_dict


def parse_journal_topics(journal_topic_list):
    """
    Parses a journal topic list from the search file
    Inputs:
        journal_topic_list (list) - list of formatted journal and topics
    Outputs:
        journal_topic_dict (dict) - dictionary of topics keyed by journal
    """
    journal_topic_dict = OrderedDict()
    for jt_list in journal_topic_list:
        journal, topic_list = jt_list.split('=')
        journal_topic_dict[journal] = topic_list.strip()[1:-1].split(',')
    return journal_topic_dict


def build_result_dict(search_dict, entrez_email):
    """
    Build a dictionary of data records based on previously identified UIDs
    Inputs:
        search_dict (dict) - dictionary of previously identified UIDs keyed by 
            search term
        entrez_email (str) - the current entrez email
    Output:
        data_dict (dict) - dictionary of publications corresponding to the 
            previously identified UIDs
    """
    data_dict = OrderedDict()
    for key, UID_list in search_dict.items():
        data_dict[key] = entrezUtils.fetch_pubs_from_ID_list(UID_list, 
            entrez_email)
    return data_dict


def construct_email_body(all_results_dict, pub_days_ago):
    """
    Construct an html-formatted email with the results found
    Inputs:
        all_results_dict (dict) - dict of dictionaries containing the found
            publications
        pub_days_ago (int) - day range for checking on new pubs
    Output:
        html_body (str) - an html-formatted string containing the results
            to be sent
    """
    # Define the header
    html_header = """\
    <html>
    <body>
    <h1><b>Pub Scraper Report</b></h1>
    <br/>
    """
    # Fill in html body:
    report_sections = []
    for section, result_dict in all_results_dict.items():
        report_subsection = ['<h2 style="color:red;">{}</h2>\n'.format(section)]
        for term, pub_list in result_dict.items():
            report_subsection.append("<h4>{}</h4>\n".format(term))
            if len(pub_list) < 1:
                report_subsection.append(
                    "<p>No results for '{}' in the last {} days</p>\n".format(
                        term, pub_days_ago))
                continue
            for pub in pub_list:
                # Format for html
                report_subsection.append(
                    '<p><a href="{}"> <b>{}</b> </a></p>\n'.format(
                        pub.url, pub.title))
                report_subsection.append("<p><i>{}</i></p>\n".format(
                    pub.journal))
                report_subsection.append("<p>{}</p>\n".format(
                    pub.authors))
        report_sections.append(''.join(report_subsection))
    html_body = '<br/>'.join(report_sections)
    # Define the tail:
    html_tail = """\
    </body>
    </html>
    """
    return '\n'.join([html_header, html_body, html_tail])


if __name__ == '__main__':
    main()
