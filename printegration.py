import cups
from collections import namedtuple
from mako.template import Template
import io
import os
import toml
import regfox
import badges
from GenericBadge import GenericBadgeTemplate

class Printegration:
    PrinterDef = namedtuple("PrinterDef", ('name', 'info', 'model'))
    def __init__(self, config):
        self._config = config
        self._cups_connection = cups.Connection()

    def printer_list(self):
        cups_printer_list = self._cups_connection.getPrinters()
        printer_list = []
        for printer_name, printer_dict in cups_printer_list.items():
            printer_list.append({
                'printerName': printer_name,
                'printerInfo': printer_dict['printer-info'],
                'printerModel': printer_dict['printer-make-and-model'],
            })
        return printer_list

    def _print_png(self, printer, data, job_name='badge', media=None):
        cups_options = {}
        if media is not None:
            cups_options['media'] = media

        job_id = self._cups_connection.createJob(printer, job_name, cups_options)
        self._cups_connection.startDocument(printer, job_id, job_name, cups.CUPS_FORMAT_AUTO, 1)
        self._cups_connection.writeRequestData(data, len(data))
        self._cups_connection.finishDocument(printer)

    def print_badge(self, template_data):
        badge_template = GenericBadgeTemplate(default_font=self._config['default_font'])
        png_data = io.BytesIO()
        badge_template.render(template_data, png_data, 'png')
        self._print_png(
            self._config['printer_name'],
            png_data.getvalue(),
            'badge-{}'.format(template_data['registrantId']),
            badge_template.cups_media
        )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--configuration', '-c', type=os.path.realpath, required=True, help='Configuration File')
    parser.add_argument('--template-data-file', '-t', type=os.path.realpath, required=False, default=None, help='TOML file containing values for the tempalte.')
    parser.add_argument('--list-printers', '-l', action='store_true', help='Show all available printers.')
    args = parser.parse_args()

    config = toml.load(config_file)
    printer = Printegration(config['printer'])

    if args.list_printers:
        printer.printer_list()

    elif args.template_data_file is not None:
        template_data = toml.load(args.template_data_file)
        printer.print_badge(template_data)
