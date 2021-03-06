import cups
from collections import namedtuple
import importlib.util
import io
import json
import os
import sys
import toml
import regfox
import badges
from TestBadge import TestBadgeTemplate

def import_module_file(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module

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

    def _verify_printer_name(self, printer_name):
        if printer_name is None:
            printer_name = self._config['printer_name']
        if printer_name not in self._cups_connection.getPrinters():
            raise FileNotFoundError("Printer {!r} was not found.".format(printer_name))
        return printer_name

    def print_badge(self, template_data, printer_name=None):
        printer_name = self._verify_printer_name(printer_name)
        template_module = import_module_file(self._config['badge_template'])
        template_class_name = os.path.splitext(os.path.basename(self._config['badge_template']))[0] + "Template"
        template_class = getattr(template_module, template_class_name)
        badge_template = template_class(default_font=self._config['default_font'])
        png_data = io.BytesIO()
        badge_template.render(template_data, png_data, 'png')
        self._print_png(
            printer_name,
            png_data.getvalue(),
            'badge-{}'.format(template_data['registrantId']),
            badge_template.cups_media
        )

    def print_test(self, printer_name, printer_slot):
        printer_name = self._verify_printer_name(printer_name)
        print("Printer: {!r}".format(printer_name))
        badge_template = TestBadgeTemplate(default_font=self._config['default_font'])
        png_data = io.BytesIO()
        badge_template.render({'printerSlot': printer_slot, 'printerName': printer_name}, png_data, 'png')
        self._print_png(
            printer_name,
            png_data.getvalue(),
            'testBadge-{}'.format(printer_slot),
            badge_template.cups_media
        )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--configuration', '-c', type=os.path.realpath, required=True, help='Configuration File')
    parser.add_argument('--template-data-file', '-t', type=os.path.realpath, required=False, default=None, help='TOML file containing values for the tempalte.')
    parser.add_argument('--list-printers', '-l', action='store_true', help='Show all available printers.')
    args = parser.parse_args()

    config = toml.load(args.configuration)
    printer = Printegration(config['printer'])

    if args.list_printers:
        printer.printer_list()

    elif args.template_data_file is not None:
        with open(args.template_data_file, 'rb') as td_file:
            template_data = json.load(td_file)
        printer.print_badge(template_data)
