import datetime
import logging
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, Union, List, Any
from xhtml2pdf import pisa
import pandas as pd

import psycopg2
import psycopg2.extras
from jinja2 import FileSystemLoader, Environment
from pandas import DataFrame

from InvoiceGenerator.exceptions import ConfigurationIncompleteException
from InvoiceGenerator.test_configs import csv_sample_config


class InvoiceCreator(ABC):
    AGG_ACTIVE_FUNCTIONS = []

    USER_KEY = 'user_id'

    def __init__(self, html_template: str, css_template: str, file_name_format: str, datasource_type: str,
                 datasource_configuration: Dict[str, Union[Any]], *args, **kwargs):
        self.days_of_delay = 45
        self.html_template = html_template
        self.css_template = css_template
        self.file_name_format = file_name_format
        self.datasource_type = datasource_type
        self.configuration = datasource_configuration

    def execute(self):

        fetched_data = self._fetch_data()

        grouped_data = self.group_data_by_user(fetched_data)

        for each_grouped_data in grouped_data.values():
            agg_results = self._aggregate_calculations(each_grouped_data)
            self._generate_pdf(each_grouped_data, agg_results)

    def _generate_pdf(self, user_data, aggregate_results):
        html_rendered_template = self._render_html_template(user_data, aggregate_results)
        self.html_to_pdf(html_rendered_template, user_data)

    def _aggregate_calculations(self, data):
        calculation_matrix = dict()
        for function in self.AGG_ACTIVE_FUNCTIONS:
            calculation_matrix.update(function(data))
        return calculation_matrix

    @abstractmethod
    def _fetch_data(self) -> List[Dict[str, Any]]:
        """fetch data from datasource and return as python list of dict"""
        pass

    def group_data_by_user(self, data_list: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        group data by user id for individual execution
        :param data_list: data retrieved from data sources
        :return: data grouped by user
        """
        grouped_data = defaultdict(list)
        for data_row in data_list:
            grouped_data[data_row[self.USER_KEY]].append(data_row)

        return grouped_data

    def _render_html_template(self, user_data, aggregate_results):
        """

        :param user_data: financial data of a particular user
        :param aggregate_results: aggregate calculations (future scope)
        :return: rendered html using jinja2 template renderer
        """
        environment = Environment(loader=FileSystemLoader(""))
        template = environment.get_template(self.html_template)
        metadata = self._generate_metadata()
        col_names = dict(col_names=user_data[0].keys())

        # manual css_load (needed only for xwkhtmlpdf package)
        with open(self.css_template) as css_file:
            css_dict = {'css_data': css_file.read()}

        return template.render(user_data=user_data, **css_dict, **col_names, **aggregate_results, **metadata)

    def _generate_metadata(self):
        """

        :return: generate metadata
        """
        metadata = {
            'current_date': datetime.datetime.now().strftime('%d/%m/%y'),
            'due_date': (datetime.datetime.now() + datetime.timedelta(days=self.days_of_delay)).strftime('%d/%m/%y'),
        }
        return metadata

    def html_to_pdf(self, html_rendered_template, user_data):

        output_filename = self.file_name_format.format(user_name=user_data[0]['user_name'])
        with open(output_filename, "w+b") as result_file:
            pisa.CreatePDF(src=html_rendered_template, dest=result_file)

        logging.info(f'Invoice File :{output_filename} is created')


class FileInvoiceCreator(InvoiceCreator, ABC):
    def _fetch_data(self) -> List[Dict[str, Any]]:

        file_output_as_df = self._get_file_output()
        return file_output_as_df.to_dict('records')

    @abstractmethod
    def _get_file_output(self) -> DataFrame:
        """data in df from datasource"""
        pass


class ExcelInvoiceCreator(FileInvoiceCreator):
    """
    Invoice with Excel as data source
    """
    def _get_file_output(self) -> DataFrame:
        """

        :return: get file output for excel
        """
        return pd.read_excel(self.configuration['file_name'], sheet_name=self.configuration['sheet_name'], index_col=0)


class CSVInvoiceCreator(FileInvoiceCreator):
    def _get_file_output(self) -> DataFrame:
        """
        :return: get file output for csv
        """
        return pd.read_csv(self.configuration['file_name'], sep=self.configuration['separator'])


class DatabaseInvoiceCreator(InvoiceCreator, ABC):

    def _fetch_data(self) -> List[Dict[str, Any]]:
        """

        :return: fetch data from database as datasource
        """
        conn = self._connect_to_db()
        cursor = self._get_cursor(conn)
        retrieve_query_result = self._execute_retrieve_query(cursor)
        self.destroy_connection(conn)
        return retrieve_query_result

    @abstractmethod
    def _get_cursor(self, conn):
        pass

    def _execute_retrieve_query(self, cursor):
        query = self.configuration.get('retrieve_query', None)
        if query is None:
            table_name = self.configuration.get('table_name', None)
            if table_name is None:
                raise ConfigurationIncompleteException('No query or table name found')
            query = self.get_default_query()
        return cursor.execute(query)

    @abstractmethod
    def get_default_query(self):
        pass

    @abstractmethod
    def _connect_to_db(self):
        pass

    @staticmethod
    def destroy_connection(conn):
        conn.commit()
        conn.close()


class PostgresInvoiceCreator(DatabaseInvoiceCreator):
    """
    using postgres as db
    """
    def _connect_to_db(self):
        config = self.configuration['db_connection_config']
        conn = psycopg2.connect(**config)
        return conn

    def _get_cursor(self, conn):
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return cursor

    def get_default_query(self):
        pass


Datasource_map = {
    'csv': CSVInvoiceCreator

}


def generate_pdfs(config):
    pdf_creator_object = Datasource_map[config['datasource_type']](**config)
    pdf_creator_object.execute()


if __name__ == '__main__':
    generate_pdfs(csv_sample_config)
