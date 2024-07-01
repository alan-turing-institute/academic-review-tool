from ..utils.basics import Iterator, results_cols
from ..utils.cleaners import strip_list_str
from ..exporters.general_exporters import obj_to_folder
from ..importers.pdf import read_pdf_to_table
from ..importers.jstor import import_jstor_metadata, import_jstor_full
from ..importers.crossref import references_to_df, search_works, lookup_doi, lookup_dois, lookup_journal, lookup_journals, search_journals, get_journal_entries, search_journal_entries, lookup_funder, lookup_funders, search_funders, get_funder_works, search_funder_works
from ..importers.orcid import lookup_orcid
from ..datasets import stopwords
from ..internet.scrapers import scrape_article, scrape_doi, scrape_google_scholar, scrape_google_scholar_search, can_scrape

from ..classes.properties import Properties
from ..classes.results import Results, generate_work_id

import copy
from datetime import datetime
import pickle
from pathlib import Path

import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize # type: ignore








class ActivityLog(pd.DataFrame):

    """
    This is a ActivityLog object. It is a modified Pandas Dataframe object designed to store metadata about an academic review.
    
    Parameters
    ----------
    
    
    Attributes
    ----------
    """

    def __init__(self):
        
        """
        Initialises ActivityLog instance.
        
        Parameters
        ----------
        """


        # Inheriting methods and attributes from Pandas.DataFrame class
        super().__init__(dtype=object, columns = [
                                'activity',
                                'site'
                                ]
                         )
        
        self.replace(np.nan, None)

def generate_author_id(author_data: pd.Series):

        author_id = 'A:'

        given_name = author_data['given_name']
        family_name = author_data['family_name']
        full_name = author_data['full_name']

        if (family_name == None) and (full_name != None):
            
            if full_name == 'no_name_given':
                author_id = author_id + '-' + '000'
            
            else:
            
                full_split = full_name.lower().split(' ')
                first = full_split[0]
                first_shortened = first[0]
                last = full_split[-1]

                author_id = author_id + '-' + first_shortened + '-' + last

        else:

            if given_name != None:
                given_shortened = given_name.lower()[0]
                author_id = author_id + '-' + given_shortened
            
            
            if family_name != None:
                family_clean = family_name.lower().replace(' ', '-')
                author_id = author_id + '-' + family_clean

        uid = author_data['orcid']
        if (uid == None) or (uid == 'None') or (uid == ''):
            uid = author_data['google_scholar']
            if (uid == None) or (uid == 'None') or (uid == ''):
                uid = author_data['scopus']
                if (uid == None) or (uid == 'None') or (uid == ''):
                    uid = author_data['crossref']
                    if (uid == None) or (uid == 'None') or (uid == ''):
                        uid = ''
        
        uid_shortened = uid.replace('https://', '').replace('http://', '').replace('www.', '').replace('orcid.org/','').replace('scholar.google.com/','').replace('citations?','').replace('user=','')[:20]

        author_id = author_id + '-' + uid_shortened
        author_id = author_id.replace('A:-', 'A:').strip('-')

        return author_id


class Author():

    """
    This is an Author object. It is designed to store data about an individual author and their publications.
    
    Parameters
    ----------
    
    
    Attributes
    ----------
    """

    def __init__(self,
                 author_id: str = None, # type: ignore
                 full_name = None, # type: ignore
                 given_name = None, # type: ignore
                 family_name = None, # type: ignore
                 email: str = None, # type: ignore
                 affiliations: str = None, # type: ignore
                 publications: str = None, # type: ignore
                 orcid: str = None, # type: ignore
                 google_scholar: str = None, # type: ignore
                 scopus: str = None, # type: ignore
                 crossref: str = None, # type: ignore
                 other_links: str = None # type: ignore
                 ):
        
        """
        Initialises Author instance.
        
        Parameters
        ----------
        """

        if type(given_name) == str:
            given_name = given_name.strip()

        if type(family_name) == str:
            family_name = family_name.strip()

        if ((type(family_name) == str) and (',' in family_name)) and ((given_name == None) or (given_name == '')):
            split_name = family_name.split(',')
            given_name = split_name[0].strip()
            family_name = split_name[1].strip()

        

        self.details = pd.DataFrame(columns = [
                                'author_id',
                                'full_name',
                                'given_name',
                                'family_name',
                                'email',
                                'affiliations',
                                'publications',
                                'orcid',
                                'google_scholar',
                                'scopus',
                                'crossref',
                                'other_links'
                                ],
                                dtype = object)
        
        
        self.details.loc[0] = pd.Series(dtype=object)
        self.details.loc[0, 'author_id'] = author_id
        self.details.loc[0, 'full_name'] = full_name
        self.details.loc[0, 'given_name'] = given_name
        self.details.loc[0, 'family_name'] = family_name
        self.details.loc[0, 'email'] = email
        self.details.loc[0, 'affiliations'] = affiliations
        self.details.loc[0, 'publications'] = publications
        self.details.loc[0, 'orcid'] = orcid
        self.details.loc[0, 'google_scholar'] = google_scholar
        self.details.loc[0, 'scopus'] = scopus
        self.details.loc[0, 'crossref'] = crossref
        self.details.loc[0, 'other_links'] = other_links

        full_name = self.get_full_name()
        if full_name != self.details.loc[0, 'full_name']:
            self.details.loc[0, 'full_name'] = full_name

        self.publications = Results()

    def generate_id(self):

        author_data = self.details.loc[0]

        author_id = generate_author_id(author_data) # type: ignore
        return author_id

    def update_id(self):

        current_id = self.details.loc[0, 'author_id']

        if (current_id == None) or (current_id == 'None') or (current_id == '') or (current_id == 'A:000'):
            auth_id = self.generate_id()
            self.details.loc[0, 'author_id'] = auth_id
        
    
    def __getitem__(self, key):
        
        """
        Retrieves Author attribute using a key.
        """
        
        if key in self.__dict__.keys():
            return self.__dict__[key]
        
        if key in self.details.columns:
            return self.details.loc[0, key]
        
        if key in self.publications.columns:
            return self.publications[key]

    def __repr__(self) -> str:
        return str(self.details.loc[0, 'full_name'])
    
    def get_full_name(self):

            given = self.details.loc[0, 'given_name']
            family = self.details.loc[0, 'family_name']

            if given == None:
                given = ''
            
            if family == None:
                family = ''

            if ((type(family) == str) and (',' in family)) and ((given == None) or (given == 'None') or (given == '')):
                split_name = family.split(',')
                given = split_name[0].strip()
                self.details.loc[0, 'given_name'] = given

                family = split_name[1].strip()
                self.details.loc[0, 'family_name'] = family

            full = given + ' ' + family
            full = full.strip()

            if (full == '') or (full == ' '):
                full = 'no_name_given'

            full_name = self.details.loc[0, 'full_name']
            if (full_name == None) or (full_name == 'None') or (full_name == '') or (full_name == 'no_name_given'):
                result = full
            else:
                result = full_name

            return result


    def update_full_name(self):

            full_name = self.get_full_name()
            self.details.loc[0, 'full_name'] = full_name

    def name_set(self) -> set:

        given = str(self.details.loc[0, 'given_name'])
        family = str(self.details.loc[0, 'family_name'])

        return set([given, family])

    def has_orcid(self) -> bool:

        orcid = self.details.loc[0, 'orcid']

        if (type(orcid) == str) and (orcid != ''):
            return True
        else:
            return False

    def add_series(self, series: pd.Series):
        self.details.loc[0] = series

    def from_series(series: pd.Series): # type: ignore
        author = Author()
        author.add_series(series)
    
    def add_dataframe(self, dataframe: pd.DataFrame):
        series = dataframe.loc[0]
        self.add_series(series) # type: ignore

    def from_dataframe(dataframe: pd.DataFrame): # type: ignore
        author = Author()
        author.add_dataframe(dataframe)

    def import_crossref(self, crossref_result: dict):

        if 'given' in crossref_result.keys():
            self.details.loc[0, 'given_name'] = crossref_result['given']
        
        if 'family' in crossref_result.keys():
            self.details.loc[0, 'family_name'] = crossref_result['family']
        
        if 'email' in crossref_result.keys():
            self.details.loc[0, 'email'] = crossref_result['email']

        if 'affiliation' in crossref_result.keys():
            if (type(crossref_result['affiliation']) == list) and (len(crossref_result['affiliation']) > 0):
                self.details.at[0, 'affiliations'] = crossref_result['affiliation'][0]

            else:
                if (type(crossref_result['affiliation']) == dict) and (len(crossref_result['affiliation'].keys()) > 0):
                    key = list(crossref_result['affiliation'].keys())[0]
                    self.details.at[0, 'affiliations'] = crossref_result['affiliation'][key]

        if 'ORCID' in crossref_result.keys():
            self.details.loc[0, 'orcid'] = crossref_result['ORCID']
        
        else:
            if 'orcid' in crossref_result.keys():
                self.details.loc[0, 'orcid'] = crossref_result['orcid']

        # self.details.loc[0, 'google_scholar'] = google_scholar
        # self.details.loc[0, 'crossref'] = crossref
        # self.details.loc[0, 'other_links'] = other_links

        self.update_full_name()
    
    def import_orcid(self, orcid_id: str):

        auth_df = lookup_orcid(orcid_id)
        cols = auth_df.columns.to_list()

        if len(auth_df) > 0:

            author_details = auth_df.loc[0]

            if 'name' in cols:
                self.details.loc[0, 'given_name'] = author_details['name']
            
            if 'family name' in cols:
                self.details.loc[0, 'family_name'] = author_details['family name']
            
            if 'emails' in cols:
                self.details.at[0, 'email'] = author_details['emails']
            
            if 'employment' in cols:
                self.details.at[0, 'affiliations'] = author_details['employment']
            
            if 'works' in cols:
                self.details.at[0, 'publications'] = author_details['works']
            
            self.details.loc[0, 'orcid'] = orcid_id

            self.update_full_name()
        
        else:
            self.details.loc[0, 'orcid'] = orcid_id
            self.update_full_name()
        

    def from_crossref(crossref_result: dict): # type: ignore

        author = Author()
        author.import_crossref(crossref_result)
        author.update_full_name()

        return author
    
    def from_orcid(orcid_id: str): # type: ignore

        author = Author()
        author.import_orcid(orcid_id)
        author.update_full_name()

        return author
    
    def update_from_orcid(self):

        orcid = self.details.loc[0, 'orcid']

        if (orcid != None) and (orcid != '') and (orcid != 'None'):
            
            orcid = str(orcid).replace('https://', '').replace('http://', '').replace('orcid.org/', '')

            self.import_orcid(orcid_id = orcid)

        
    





class Authors:

    """
    This is an Authors object. It contains a collection of Authors objects and compiles data about them.
    
    Parameters
    ----------
    
    
    Attributes
    ----------
    """

    def __init__(self, authors_data = None):
        
        """
        Initialises Authors instance.
        
        Parameters
        ----------
        """

        self.all = pd.DataFrame(columns = [
                                'author_id',
                                'full_name',
                                'given_name',
                                'family_name',
                                'email',
                                'affiliations',
                                'publications',
                                'orcid',
                                'google_scholar',
                                'crossref',
                                'other_links'
                                ],
                                dtype = object)
        

        self.details = dict()

        self.data = []
        self.data.append(authors_data)

        if (type(authors_data) == list) and (type(authors_data[0]) == Author):

            for i in authors_data:
                auth = i.details.copy(deep=True)
                self.all = pd.concat([self.all, auth])

            self.all = self.all.reset_index().drop('index',axis=1)

        else:

            if type(authors_data) == dict:
                
                values = list(authors_data.values())

                if type(values[0]) == Author:

                    for a in authors_data.keys():
                        
                        index = len(self.all)
                        auth = a.details.copy(deep=True)
                        self.all = pd.concat([self.all, auth])
                        self.all.loc[index, 'author_id'] = a

                    self.all = self.all.reset_index().drop('index',axis=1)
                


    def __getitem__(self, key):
        
        """
        Retrieves Authors attribute using a key.
        """
        
        if key in self.__dict__.keys():
            return self.__dict__[key]
        
        if key in self.details.keys():
            return self.details[key]

        if key in self.all.columns:
            return self.all[key]
        
        if (type(key) == int) and (key <= len(self.data)):
            return self.data[key]
    
    def __repr__(self) -> str:

        alphabetical = self.all['full_name'].sort_values().to_list().__repr__()
        return alphabetical
    
    def __len__(self) -> int:
        return len(self.details.keys())

    def merge(self, authors):

        left = self.all.copy(deep=True)
        right = authors.all.copy(deep=True)
        
        merged = pd.concat([left, right])

        self.all = merged.drop_duplicates(subset=['author_id', 'family_name', 'orcid'], ignore_index=True)

        for i in authors.details.keys():
            if i not in self.details.keys():
                self.details[i] = authors.details[i]

        left_data = self.data
        right_data = authors.data

        if left_data == None:
                left_data = []
            
        if right_data == None:
                right_data = []

        if (type(left_data) == Author) or (type(left_data) == str):
                left_data = [left_data]
            
        if (type(right_data) == Author) or (type(right_data) == str):
                right_data = [right_data]
            
        if type(left_data) == dict:
                left_data = list(left_data.values())
            
        if type(right_data) == dict:
                right_data = list(right_data.values())

        merged_data = left_data + right_data # type: ignore
        merged_data = pd.Series(merged_data).value_counts().index.to_list()

        self.data = merged_data

        return self

    def add_author(self, author: Author, data = None, update_from_orcid = False):

        if update_from_orcid == True:
            orcid = author.details.loc[0,'orcid']
            if (orcid != None) and (orcid != '') and (orcid != 'None'):
                author.update_from_orcid()

        author.update_id()

        author_id = str(author.details.loc[0, 'author_id'])

        if author_id in self.all['author_id'].to_list():
            id_count = len(self.all[self.all['author_id'].str.contains(author_id)]) # type: ignore
            author_id = author_id + f'#{id_count + 1}'
            author.details.loc[0, 'author_id'] = author_id

        self.all = pd.concat([self.all, author.details])
        self.all = self.all.reset_index().drop('index', axis=1)

        self.details[author_id] = author

        if data == None:
            data = author.details.to_dict(orient='index')
        
        self.data.append(data)


    def add_authors_list(self, authors_list: list):
        
        for i in authors_list:
            if type(i) == Author:
                self.add_author(author = i)

    def sync_all(self):

        for i in self.details.keys():
            author = self.details[i]
            author.update_id()
            series = author.details.loc[0]
            all = self.all.copy(deep=True).astype(str)
            auth_index = all[all['author_id'] == i].index.to_list()[0]
            self.all.loc[auth_index] = series

    def update_from_orcid(self):

        author_ids = self.details.keys()

        for a in author_ids:

            self.details[a].update_from_orcid()
            details = self.details[a].details.loc[0]
            
            df_index = self.all[self.all['author_id'] == a].index.to_list()[0]
            self.all.loc[df_index] = details

            new_id = details['author_id']
            if new_id != a:
                self.details[new_id] = self.details[a]
                del self.details[a]

    def import_orcid_ids(self, orcid_ids: list):

        for i in orcid_ids:

            auth = Author.from_orcid(i) # type: ignore
            self.add_author(author = auth, data = i)

    def from_orcid_ids(orcid_ids: list): # type: ignore

        authors = Authors()
        authors.import_orcid_ids(orcid_ids)

        return authors

    def with_orcid(self):
        return self.all[~self.all['orcid'].isna()]

    def import_crossref(self, crossref_result: list):

        for i in crossref_result:

            auth = Author.from_crossref(i) # type: ignore
            self.add_author(author = auth, data = i)
    
    def from_crossref(crossref_result: list): # type: ignore

        authors = Authors()
        authors.import_crossref(crossref_result)

        return authors

def format_authors(author_data):
        
        result = Authors()

        if (author_data == None) or (author_data == ''):
            result = Authors()

        if type(author_data) == Authors:
            result = author_data

        if (type(author_data) == list) and (len(author_data) > 0) and (type(author_data[0]) == Author):
            result = Authors()
            result.add_authors_list(author_data)

        if (type(author_data) == list) and (len(author_data) > 0) and (type(author_data[0]) == dict):
            result = Authors.from_crossref(author_data) # type: ignore

        if (type(author_data) == dict) and (len(author_data.values()) > 0) and (type(list(author_data.values())[0]) == str):
            author = Author.from_crossref(author_data) # type: ignore
            result = Authors()
            result.add_author(author)
    
    
        return result

class Review:
    
    """
    This is a Review object. It stores the data from academic reviews.
    
    Parameters
    ----------
    review_name : str 
        the Review's name. Defaults to requesting from user input.
    file_location : str
        file location associated with Review.
    file_type : str
        file type associated with Review file(s).
    """

    
    def __init__(self, review_name = 'request_input', file_location = None, file_type = None):
        
        """
        Initialises a Review instance.
        
        Parameters
        ----------
        review_name : str 
            the Review's name. Defaults to requesting from user input.
        file_location : str
            file location associated with Review.
        file_type : str
            file type associated with Review file(s).
        """
        
        if review_name == 'request_input':
            review_name = input('Review name: ')

        self.properties = Properties(review_name = review_name, file_location = file_location, file_type = file_type)
        self.results = Results()
        self.authors = Authors()
        self.activity_log = ActivityLog()
        self.description = ''
        self.update_properties()
    
    def update_properties(self):
        
        """
        Updates Review's properties.
        
        Updates
        -------
            * review_id
            * case_count
            * size
            * last_changed
        """
        
        self.properties.review_id = id(self)
        self.properties.size = str(self.__sizeof__()) + ' bytes'
        self.properties.update_last_changed()
    
    def __repr__(self):
        
        """
        Defines how Reviews are represented in string form.
        """
        
        output = f'\n{"-"*(13+len(self.properties.review_name))}\nReview name: {self.properties.review_name}\n{"-"*(13+len(self.properties.review_name))}\n\nProperties:\n-----------\n{self.properties}\n\nDescription:\n------------\n\n{self.description}\n\nResults:\n--------\n\n{self.results}\n\nAuthors:\n--------\n\n{self.authors.all.head(10)}'
        
        return output
            
    def __iter__(self):
        
        """
        Implements iteration functionality for Review objects.
        """
        
        return Iterator(self)
    
    def __getitem__(self, key):
        
        """
        Retrieves Review contents or results using an index/key.
        """
        
        if key in self.__dict__.keys():
            return self.__dict__[key]

        if key in self.results['work_id'].to_list():
            return self.results.get(key)
        
        if key in self.authors.details.keys():
            return self.authors[key]
        
        if key in self.results.columns.to_list():
            return self.results[key]
        
        if key in self.authors.all.columns.to_list():
            return self.authors.all[key]


    def __setitem__(self, index, data):
        
        """
        Adds entry to results using an index position. Specifying a column position is optional.
        """
        
        self.results.loc[index] = data
        
        self.update_properties()
        
    def __delitem__(self, index):
        
        """
        Deletes entry from results using its index.
        """
        
        self.results = self.results.drop(index)
        self.update_properties()
    
    def contents(self):
        
        """
        Returns the Review's attributes as a list.
        """
        
        return self.__dict__.keys()
    
    def __len__(self):

        return len(self.results)
    
    def count_results(self):
        
        """
        Returns the number of entries in the Results table.
        """
        
        return len(self.results)
        
    def to_list(self):
        
        """
        Returns the Review as a list.
        """
        
        return [i for i in self]
    
    def to_dict(self):
        
        """
        Returns the Review as a dictionary.  Excludes the Review's 'properties' attribute.
        """
        
        output_dict = {}
        for index in self.__dict__.keys():
            output_dict[index] = self.__dict__[index]
        
        return output_dict
    
    def copy(self):
        
        """
        Returns the a copy of the Review.
        """
        
        return copy.deepcopy(self)
    
    def get_result(self, row_position, column_position = None):
        
        """
        Returns a result when given its attribute name.
        """
        
        if column_position == None:
            return self.results.loc[row_position]
        else:
            return self.results.loc[row_position, column_position]
    
    def get_name_str(self):
        
        """
        Returns the Review's variable name as a string. 
        
        Notes
        -----
            * Searches global environment dictionary for objects sharing Review's ID. Returns key if found.
            * If none found, searches local environment dictionary for objects sharing Review's ID. Returns key if found.
        """
        
        for name in globals():
            if id(globals()[name]) == id(self):
                return name
        
        for name in locals():
            if id(locals()[name]) == id(self):
                return name
    
    def add_pdf(self, path = 'request_input'):
        
        self.results.add_pdf(path)
        self.update_properties()

    def varstr(self):
        
        """
        Returns the Review's name as a string. Defaults to using its variable name; falls back to using its name property.
        
        Notes
        -----
            * Searches global environment dictionary for objects sharing Review's ID. Returns key if found.
            * If none found, searches local environment dictionary for objects sharing Review's ID. Returns key if found.
            * If none found, returns Review's name property.
            * If name property is None, 'none', or 'self', returns an empty string.
        """
        
        try:
            string = self.get_name_str()
        except:
            string = None
        
        if (string == None) or (string == 'self'):
            
            try:
                string = self.properties.review_name
            except:
                string = ''
                
        if (string == None) or (string == 'self'):
            string = ''
            
        return string
    
    def to_dataframe(self):
        return self.results.to_dataframe() # type: ignore

    def from_dataframe(dataframe): # type: ignore
        
        review = Review()
        review.results = Results.from_dataframe(dataframe) # type: ignore
        review.format_authors()

        return review

    def format_citations(self):
        self.results.format_citations() # type: ignore

    def format_authors(self):

        self.results.format_authors() # type: ignore

        authors_data = self.results['authors'].to_list()

        for i in authors_data:

            if type(i) == Authors:
                self.authors.merge(i)
            
            if (type(i) == str) and (len(i) > 0):
                i = i.split(',')

            if (type(i) == list) and (len(i) > 0):
                auths = Authors()
                for a in i:
                    auth = Author(full_name=a.strip())
                    auths.add_author(auth)
                self.authors.merge(auths)
    
    def add_citations_to_results(self):
        self.results.add_citations_to_results()
        self.format_authors()


    def update_from_orcid(self):
        self.authors.update_from_orcid()

    def import_excel(self, file_path = 'request_input', sheet_name = None):
        self.update_properties()
        return self.results.import_excel(file_path, sheet_name) # type: ignore
    
    def from_excel(file_path = 'request_input', sheet_name = None): # type: ignore

        review = Review()
        review.results = Results.from_excel(file_path, sheet_name)
        review.format_authors() # type: ignore

        return review

    def import_csv(self, file_path = 'request_input'):
        self.update_properties()
        return self.results.import_csv(file_path) # type: ignore
    
    def from_csv(file_path = 'request_input'):

        review = Review()
        review.results = Results.from_csv(file_path)
        review.format_authors()

        return review

    def import_json(self, file_path = 'request_input'):
        self.update_properties()
        return self.results.import_json(file_path) # type: ignore
    
    def from_json(file_path = 'request_input'):

        review = Review()
        review.results = Results.from_json(file_path)
        review.format_authors() # type: ignore

        return review
    
    def import_file(self, file_path = 'request_input', sheet_name = None):
        self.update_properties()
        return self.results.import_file(file_path, sheet_name)
    
    def from_file(file_path = 'request_input', sheet_name = None):
        
        review = Review()
        review.results = Results.from_file(file_path, sheet_name)
        review.format_authors() # type: ignore

        return review

    def import_jstor_metadata(self, file_path = 'request_input', clean_results = True):
        self.results.import_jstor_metadata(file_path = file_path, clean_results = clean_results)
    
    def import_jstor_full(self, file_path = 'request_input', clean_results = True):
        self.results.import_jstor_full(file_path = file_path, clean_results = clean_results)

    def search_field(self, field = 'request_input', any_kwds = 'request_input', all_kwds = None, not_kwds = None, case_sensitive = False, output = 'Results'):
        return self.results.search_field(field = field, any_kwds = any_kwds, all_kwds = all_kwds, not_kwds = not_kwds, case_sensitive = case_sensitive, output = output)

    def search(self, any_kwds = 'request_input', all_kwds = None, not_kwds = None, fields = 'all', case_sensitive = False, output = 'Results'):
        return self.results.search(fields = fields, any_kwds = any_kwds, all_kwds = all_kwds, not_kwds = not_kwds, case_sensitive = case_sensitive, output = output)

    def export_txt(self, file_name = 'request_input', file_address = 'request_input'):
        
        """
        Exports the Review to a .txt file.
        
        Parameters
        ----------
        file_name : str
            name of file to create. Defaults to using the object's variable name.
        file_address : str
            directory address to create file in. defaults to requesting for user input.
        """
        
        if file_name == 'request_input':
            file_name = input('File name: ')
            
        if file_address == 'request_input':
            file_address = input('File address: ')
            
        file_address = file_address + '/' + file_name

        if file_address.endswith('.Review') == False:
            file_address = file_address + '.Review'

        with open(file_address, 'wb') as f:
            pickle.dump(self, f) 
    
    def export_folder(self, folder_name = 'request_input', folder_address = 'request_input', export_str_as = 'txt', export_dict_as = 'json', export_pandas_as = 'csv', export_network_as = 'graphML'):
        
        """
        Exports Review's contents to a folder.
        
        Parameters
        ----------
        folder_name : str 
            name of folder to create. Defaults to using the object's variable name.
        folder_address : str 
            directory address to create folder in. defaults to requesting for user input.
        export_str_as : str 
            file type for exporting string objects. Defaults to 'txt'.
        export_dict_as : str 
            file type for exporting dictionary objects. Defaults to 'json'.
        export_pandas_as : str 
            file type for exporting Pandas objects. Defaults to 'csv'.
        export_network_as : str 
            file type for exporting network objects. Defaults to 'graphML'.
        """
        
        if folder_name == 'request_input':
            folder_name = input('Folder name: ')
        
        if folder_name.endswith('_Review') == False:
            folder_name = folder_name + '_Review'
        
        obj_to_folder(self, folder_name = folder_name, folder_address = folder_address, export_str_as = export_str_as, export_dict_as = export_dict_as, export_pandas_as = export_pandas_as, export_network_as = export_network_as)

    def scrape_article(self, url = 'request_input'):
        
        if url == 'request_input':
            url = input('URL: ')

        df = scrape_article(url)
        self.results.add_dataframe(df)

    def scrape_doi(self, doi = 'request_input'):
        
        if doi == 'request_input':
            doi = input('DOI or URL: ')

        df = scrape_doi(doi)
        self.results.add_dataframe(df)

    def scrape_google_scholar(self, url = 'request_input'):

        if url == 'request_input':
            url = input('URL: ')

        df = scrape_google_scholar(url)
        self.results.add_dataframe(df)
    
    def scrape_google_scholar_search(self, url = 'request_input'):

        if url == 'request_input':
            url = input('URL: ')

        df = scrape_google_scholar_search(url)
        self.results.add_dataframe(df)
    
    def search_crossref(self,
                bibliographic: str = None,
                title: str = None,
                author: str = None,
                author_affiliation: str = None,
                editor: str = None,
                entry_type: str = None,
                published_date: str = None,
                DOI: str = None,
                ISSN: str = None,
                publisher_name: str = None,
                funder_name = None,
                source: str = None,
                link: str = None,
                filter: dict = None,
                select: list = None,
                sample: int = None,
                limit: int = None,
                rate_limit: float = 0.1,
                timeout = 60,
                add_to_results = False
                ) -> pd.DataFrame:
        
        df = search_works(bibliographic = bibliographic,
                title = title,
                author = author,
                author_affiliation = author_affiliation,
                editor = editor,
                entry_type = entry_type,
                published_date = published_date,
                DOI = DOI,
                ISSN = ISSN,
                publisher_name = publisher_name,
                funder_name = funder_name,
                source = source,
                link = link,
                filter = filter,
                select = select,
                sample = sample,
                limit = limit,
                rate_limit = rate_limit,
                timeout = timeout)
        
        if add_to_results == True:
            self.results.add_dataframe(dataframe=df)
            self.format_authors()
        
        return df

    def lookup_doi(self, doi = 'request_input', timeout = 60):
        return lookup_doi(doi=doi, timeout=timeout)
    
    def add_doi(self, doi = 'request_input', timeout = 60):
        return self.results.add_doi(doi=doi, timeout=timeout)

    def lookup_dois(self, dois_list: list = [], rate_limit: float = 0.1, timeout = 60):
        return lookup_dois(dois_list=dois_list, rate_limit=rate_limit, timeout=timeout)
    
    def add_dois(self, dois_list: list = [], rate_limit: float = 0.1, timeout = 60):
        return self.results.add_dois(dois_list=dois_list, rate_limit=rate_limit, timeout=timeout)
    
    def update_from_dois(self, timeout: int = 60):
        self.results.update_from_dois(timeout=timeout) # type: ignore
        self.format_authors()
        self.format_citations()

    def sync_apis(self, timeout: int = 60):

        self.update_from_dois(timeout=timeout)
        self.update_from_orcid()

    def lookup_journal(self, issn = 'request_input', timeout = 60):
        return lookup_journal(issn = issn, timeout = timeout)
    
    def lookup_journals(self, issns_list: list = [], rate_limit: float = 0.1, timeout: int = 60):
        return lookup_journals(issns_list = issns_list, rate_limit = rate_limit, timeout = timeout)
    
    def search_journals(self, *args, limit: int = None, rate_limit: float = 0.1, timeout = 60):
        return search_journals(*args, limit = limit, rate_limit=rate_limit, timeout = timeout)
    
    def get_journal_entries(self,
                        issn = 'request_input',
                        filter: dict = None,
                        select: list = None,
                        sample: int = None,
                        limit: int = None,
                        rate_limit: float = 0.1,
                        timeout = 60):
        
        return get_journal_entries(issn = issn, filter = filter, select = select, sample = sample, limit = limit, rate_limit = rate_limit, timeout = timeout)
    
    def search_journal_entries(
                        self,
                        issn = 'request_input',
                        bibliographic: str = None,
                        title: str = None,
                        author: str = None,
                        author_affiliation: str = None,
                        editor: str = None,
                        entry_type: str = None,
                        published_date: str = None,
                        DOI: str = None,
                        publisher_name: str = None,
                        funder_name: str = None,
                        source: str = None,
                        link: str = None,
                        filter: dict = None,
                        select: list = None,
                        sample: int = None,
                        limit: int = None,
                        rate_limit: float = 0.1,
                        timeout: int = 60,
                        add_to_results: bool = False) -> pd.DataFrame:
        
            df = search_journal_entries(issn = issn,
                                          bibliographic = bibliographic,
                                          title=title,
                                          author=author,
                                          author_affiliation=author_affiliation,
                                          editor=editor,
                                          entry_type=entry_type,
                                          published_date = published_date,
                                          DOI = DOI,
                                          publisher_name = publisher_name,
                                          funder_name = funder_name,
                                          source = source,
                                          link=link,
                                          filter=filter,
                                          select = select,
                                          sample=sample,
                                          limit=limit,
                                          rate_limit=rate_limit,
                                          timeout=timeout
                                          )
            
            if add_to_results == True:
                self.results.add_dataframe(dataframe=df)
                self.format_authors()
        
            return df
    
    def lookup_funder(self, funder_id = 'request_input', timeout = 60):
        return lookup_funder(funder_id = funder_id, timeout = timeout)
    
    def lookup_funders(self, funder_ids: list = [], rate_limit: float = 0.1, timeout = 60):
        return lookup_funders(funder_ids=funder_ids, rate_limit=rate_limit, timeout = timeout)
    
    def search_funders(self, *args, limit: int = None, rate_limit: float = 0.1, timeout = 60):
        return search_funders(*args, limit=limit, rate_limit=rate_limit, timeout=timeout)
    
    def get_funder_works(self,
                        funder_id = 'request_input',
                        filter: dict = None,
                        select: list = None,
                        sample: int = None,
                        limit: int = None,
                        rate_limit: float = 0.1,
                        timeout: int = 60,
                        add_to_results: bool = False):
        
        df = get_funder_works(funder_id=funder_id, filter=filter, select=select, sample=sample, limit=limit, rate_limit=rate_limit, timeout=timeout)

        if add_to_results == True:
                self.results.add_dataframe(dataframe=df)
                self.format_authors()
        
        return df
    
    def search_funder_works(self,
                        funder_id = 'request_input',
                        bibliographic: str = None,
                        title: str = None,
                        author: str = None,
                        author_affiliation: str = None,
                        editor: str = None,
                        entry_type: str = None,
                        published_date: str = None,
                        DOI: str = None,
                        publisher_name: str = None,
                        funder_name = None,
                        source: str = None,
                        link: str = None,
                        filter: dict = None,
                        select: list = None,
                        sample: int = None,
                        limit: int = None,
                        rate_limit: float = 0.1,
                        timeout: int = 60,
                        add_to_results: bool = False):
    
        df = search_funder_works(
                                funder_id=funder_id,
                                bibliographic=bibliographic,
                                title=title,
                                author=author,
                                author_affiliation=author_affiliation,
                                editor=editor,
                                entry_type=entry_type,
                                published_date=published_date,
                                DOI=DOI,
                                publisher_name=publisher_name,
                                funder_name=funder_name,
                                source=source,
                                link=link,
                                filter=filter,
                                select=select,
                                sample=sample,
                                limit=limit,
                                rate_limit=rate_limit,
                                timeout=timeout)
            
        if add_to_results == True:
                self.results.add_dataframe(dataframe=df) # type: ignore
                self.format_authors()
        
        return df


    def crawl_stored_citations(self, max_depth=3, processing_limit=1000, format_authors = True, update_from_doi = False):

        self.results.crawl_stored_citations(max_depth=max_depth, processing_limit=processing_limit, format_authors = format_authors, update_from_doi = update_from_doi) # type: ignore

        if format_authors == True:
            self.format_authors()

    def crawl_citations(
                    self,
                    use_api: bool = True,
                    crawl_limit: int = 5, 
                    depth_limit: int = 2,
                    be_polite: bool = True,
                    rate_limit: float = 0.05,
                    timeout: int = 60,
                    add_to_results = True
                    ):
    
        """
        Crawls a Result's object's entries, their citations, and so on.
        
        The crawler iterates through queue of works; extracts their citations; runs checks to validate each reference;
        based on these, selects a source to retrieve data from: 
            (a) if has a valid DOI: Crossref API.
            (b) if no valid DOI: bespoke web scraping for specific academic websites.
            (c) else if a link is present: general web scraping.
        
        Retrieves data and adds the entries to the dataframe. 

        Iterates through each set of added entries.
        
        Parameters
        ---------- 
        
        
        
        Returns
        -------
        result : object 
            an object containing the results of a crawl.
        """

        result = self.results.crawl_citations(
                                            use_api = use_api,
                                            crawl_limit = crawl_limit, 
                                            depth_limit = depth_limit,
                                            be_polite = be_polite,
                                            rate_limit = rate_limit,
                                            timeout = timeout,
                                            add_to_results = add_to_results
                                            ) # type: ignore
        
        if add_to_results == True:

            self.format_citations()
            self.format_authors()
        
        return result


    ## Legacy code for saving reviews, taken from Projects class in IDEA. Requires overhaul.

    # def save_as(self, file_name = 'request_input', file_address = 'request_input', file_type = 'request_input'):
        
    #     """
    #     Saves the Review to a file or folder.
        
    #     Parameters
    #     ----------
    #     file_name : str
    #         name of file to create. Defaults to using the object's variable name.
    #     file_address : str
    #         directory address to create file in. defaults to requesting for user input.
    #     file_type : str
    #         type of file to save.
        
    #     Notes
    #     -----
    #     Options for file_type:
    #         * 'Review': saves to a .Review file. This is a specially labelled pickled .txt file.
    #         * 'text' or 'txt': saves to a pickled .txt file.
    #         * 'pickle': saves to pickled .txt file.
    #         * 'Excel': saves to a folder of .xlsx files.
    #         * 'xlsx': saves to a folder of .xlsx files.
    #         * 'csv': saves to a folder of folders of .csv files.
    #         * 'folder': saves to a folder.
    #     """
        
    #     if file_name == 'request_input':
    #         file_name = input('File name: ')

    #     if file_type == 'request_input':
    #         file_type = input('File type: ')
        
    #     if file_address == 'request_input':
    #         file_address = input('File address: ')
        
    #     file_type = file_type.strip().strip('.').strip().lower()
        
        
    #     if (file_type == None) or (file_type.lower().strip('.').strip() == '') or (file_type.lower().strip('.').strip() == '.Review') or (file_type.lower().strip('.').strip() == 'Review') or (file_type.lower().strip('.').strip() == 'text') or (file_type.lower().strip('.').strip() == 'txt') or (file_type.lower().strip('.').strip() == 'pickle'):
            
    #         self.export_txt(file_name = file_name, file_address = file_address)
        
        
    #     if (file_type.lower().strip('.').strip() == 'excel') or (file_type.lower().strip('.').strip() == 'xlsx'):

    #         file_address = file_address + '/' + file_name
    #         os.mkdir(file_address)
    #         cases = self.cases()
    #         for i in cases:
    #             self.get_case(i).export_excel(new_file = True, file_name = i, file_address = file_address)
        
        
    #     if (file_type.lower().strip('.').strip() == 'csv') or (file_type.lower().strip('.').strip() == 'csvs'):
            
    #         file_address = file_address + '/' + file_name
    #         os.mkdir(file_address)
    #         cases = self.cases()
    #         for i in cases:
    #             self.get_case(i).export_csv_folder(folder_address = file_address, folder_name = file_name)
    
    
    # def save(self, save_as = None, file_type = None, save_to = None):
        
    #     """
    #     Saves the Review to its source file. If no source given, saves to a new file.
        
    #     Parameters
    #     ----------
    #     save_as : str
    #         name of file to create. Defaults to using the object's variable name.
    #     save_to : str
    #         directory address to save file in. Defaults to requesting for user input.
    #     file_type : str
    #         type of file to save.
        
    #     Notes
    #     -----
    #     Options for file_type:
    #         * 'review': saves to a .Review file. This is a specially labelled pickled .txt file.
    #         * 'text' or 'txt': saves to a pickled .txt file.
    #         * 'pickle': saves to pickled .txt file.
    #         * 'Excel': saves to a folder of .xlsx files.
    #         * 'xlsx': saves to a folder of .xlsx files.
    #         * 'csv': saves to a folder of folders of .csv files.
    #         * 'folder': saves to a folder.
    #     """
        
    #     if save_as == None:
            
    #         try:
    #             save_as = self.properties.file_location.split('/')[-1].split('.')[0]
    #         except:
    #             save_as = self.case_name
        
    #     if file_type == None:
    #         file_type = self.file_type
        
    #     if save_to == None:
    #         save_to = self.file_location
        
    #     save_as = save_as.lower().strip('.').strip() 
        
    #     try:
    #         self.save_as(file_name = save_as, file_address = save_to, file_type = file_type)
    #     except:
    #         print('Save failed') 