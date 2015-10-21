# (C) 2015 Elke Schaper

"""
    :synopsis: The Run Class.

    .. moduleauthor:: Elke Schaper <elke.schaper@isb-sib.ch>
"""

import ast
import collections
import configobj
import logging
import os
import pickle
import re

from hts.analysis import analysis
from hts.qc import qc_knitr, qc_matplotlib
from hts.run import run_io
from hts.plate import plate
from hts.plate_data import plate_layout
from hts.protocol import protocol


LOG = logging.getLogger(__name__)

KNOWN_DATA_TYPES = plate.KNOWN_DATA_TYPES

class Run:

    """ ``Run`` describes all information connected to one run of a high
        throughput screening experiment

    Attributes:
        name (str): Name of the run
        plates (collections.OrderedDict of ``Plate``): collections.OrderedDict of ``Plate`` instances
        width (int): Width of the plates
        height (int): Height of the plates
        _protocol (``Protocol``): ``Protocol`` instance
        _platelayout (``PlateLayout``): ``PlateLayout`` instance
        _qc (dict of dict of ``QualityControl`` instance): A collection of ``QualityControl`` instance
        raw_qc (``QualityControl``): ``QualityControl`` instance - NEEDED?
        net_qc (``QualityControl``): ``QualityControl`` instance - NEEDED?
        experimenter (str): Name of the experimenter
        experimenter (str): Mail adress of the experimenter


    ..todo:: Implement me :)
    """

    def __str__(self):
        """
            Create string for Run instance.
        """
        try:
            run = ("<Run instance>\nPath to run config file: {}\n"
                "Number of plates: {}\nwidth: {}\nheight: {}"
                "".format(self.path, len(self.plates), self.width, self.height))
        except:
            run = "<Run instance>"
            LOG.warning("Could not create string of Run instance.")

        return run


    def __init__(self, plates, path = None, **kwargs):

        self.path = path
        self.plates = collections.OrderedDict((plate.name, plate) for plate in plates)
        #Plates as list: self.plates = plates
        # Later: Check if all plates are of the same height and length
        try:
            self.width = plates[0].width
            self.height = plates[0].height
        except:
            LOG.info("Could not discern plate width/height from first plate.")

        if "protocol" in kwargs:
            param = kwargs.pop('protocol')
            if not type(param) == configobj.Section:
                raise Exception("param for protocol is not of type "
                    "configobj.Section: {}, {}".format(param, type(param)))
            self.protocol(path = param['path'], format = param['format'])

        # Save all other kwargs simply as attributes.
        #for key, value in kwargs.items():
        #    if not hasattr(self, key):
        #        setattr(self, key, value)
        self.meta_data = kwargs

        # Extract plate numbering for multiple plates and set index for each plate.
        self.plate_tag_numbers = [re.findall("(\d+)", i) for i in self.plates.keys()]

        plate_tag_numbers_t = [list(i) for i in zip(*self.plate_tag_numbers)]
        for i in plate_tag_numbers_t:
            if len(set(i)) == len(self.plates):
                plate_indices = i
                break
        else:
            raise Exception("No plate numbering is informative: {}. {}. Please check if the files have useful names"
                            "from which a numbering could be derived. Otherwise, change the implementation ;) "
                            "".format(list(self.plates.keys()), plate_tag_numbers_t))

        # Set index for each plate.
        for i_plate, plate_index in zip(list(self.plates.keys()), plate_indices):
            self.plates[i_plate].index = plate_index
        self.plates = collections.OrderedDict((plate.index, plate) for plate in self.plates.values())

        if self.protocol():
            self.preprocess()


    def create(origin, path, format = None, dir = False):
        """ Create ``Run`` instance.

        Create ``Run`` instance.

        Args:
            origin (str):  At current only "config" or "plates"
            format (str):  Format of the origin, at current not specified
            path (str): Path to input file or directory

            dir (Bool): True if all files in directory shall be read, else false.

        .. todo:: Write checks for ``format`` and ``path``.
        """

        if dir == True:
            if os.path.isdir(path):
                file = os.listdir(path)
            else:
                raise ValueError("Run create directory {} does not exist.".format(path))
        else:
            if os.path.isfile(path):
                path, file = os.path.split(path)
            else:
                raise ValueError("Run create file {} does not exist.".format(path))


        if origin == 'config':
            return Run.create_from_config(path, file)
        if origin == 'envision':
            return Run.create_from_envision(path, file)
        elif origin == 'pickle':
            with open(file, 'rb') as fh:
                return pickle.load(fh)
        else:
            raise ValueError("The combination of origin: {} and format: {} is "
                            "not implemented in "
                            "Run.create()".format(origin, format))


    def create_from_config(path, file):
        """ Read config and use data to create `Run` instance.

        Read config and use data to create `Run` instance.

        Args:
            path (str): Path to input configobj file
            file (str): Filename of configobj file

        .. todo:: Write checks if path and file exists when necessary.
        """

        config = configobj.ConfigObj(os.path.join(path, file), stringify=True)


        defined_data_types = [data_type for data_type in KNOWN_DATA_TYPES if data_type in config]
        LOG.info(defined_data_types)
        data_types_plate_wise = [data_type for data_type in defined_data_types if eval(config[data_type].pop("is_defined_plate_wise")) == True]
        data_types_not_plate_wise = [data_type for data_type in defined_data_types if data_type not in data_types_plate_wise]

        ## 1. Create `Plate` instances from plate_wise information.

        if len(data_types_plate_wise) == 0:
            raise Exception("No plate wise information was defined in Run config.")

        config_type_wise = {}
        n_files = {}
        for data_type in data_types_plate_wise:
            # Plate data is located in multiple files.
            config_local = config[data_type]
            # Either, a filename template and filenumbers (indices) are supplied, or the filenames are supplied directly:
            config_file = {i: config_local.pop(i) for i in ["filenames", "path", "filename", "filenumber"] if i in config_local}
            if all(i in config_file for i in ["path", "filenames"]): #"filenames" predominates "filename", "filenumber"
                l_files = [os.path.join(config_file["path"], i_file) for i_file in config_file['filenames']]
            elif all(i in config_file for i in ["path", "filename", "filenumber"]):
                l_files = [os.path.join(config_file["path"], config_file["filename"].format(i_index)) for i_index in config_file['filenumber']]
            config_type_wise[data_type] = {"files": l_files, "config": config_local}
            n_files[data_type] = len(l_files)

        # Check if the number of files is equal for all data_types_plate_wise:
        if len(set(n_files.values())) != 1:
            raise Exception("The run configuration defines different numbers of plates for different datatypes: {}"
                            "".format(n_files))
        else:
            n_files = next(iter(n_files.values()))

        # Transform config_type_wise to per config_plate_wise:
        config_plate_wise = {}
        for i in range(n_files):
            config_plate_wise[i] = {data_type: {"path": info["files"][i], "config": info["config"]} for data_type, info in config_type_wise.items()}

        plates = [plate.Plate.create(format="config", **config) for i_plate, config in config_plate_wise.items()]

        ## 2. If available, add general = not_plate_wise information to each plate
        data_run_wise = {}
        for data_type in data_types_not_plate_wise:
            print("HELP! Needs implementation")
            if data_type == "plate_layout":
                data = plate_layout.PlateLayout.create(**config[data_type])
            else:
                raise Exception("Reading in general info for data_type {} is not yet implemented."
                                "".format(data_type))

            for i_plate in plates:
                i_plate.set_data(data_type, data)

        return Run(path=os.path.join(path, file), plates=plates, **config)


    def create_from_envision(path, file):
        """ Read envision data and create `Run` instance.

        Read envision data and create `Run` instance.

        Args:
            path (str): Path to input configobj file
            file (str): Filename of configobj file

        .. todo:: Write checks if path and file exists when necessary.
        """

        if type(file) != list:
            file = [file]

        plates = []
        for i_file in file:
            config = {"readout": {"path": os.path.join(path, i_file), "config": {"format": "envision_csv"}}}
            plates.append(plate.Plate.create(format="config", **config))

        return Run(path=path, plates=plates)


    def create_qc_report(self, path):
        """ Create quality control report (.pdf) in path.

        Create quality control report (.pdf) in path.

        Args:
            path (str): Path to result quality control report file

        .. todo:: Write checks if the path exists.
        """

        self.run_qc()
        # Create pdf


    def filter(self, type, tag, subset=None):
        """ Filter run data according to type and tag.

        Filter run data according to type and tag.

        Args:
            type (str): Either per "run_wise" or per "plate_wise".
            tags (str): Defines either the plate (within the plate),
                or the plate (within the run).
            subset (list of str): Defines which plates/plate_readouts shall be included.

        Returns:
            Readout or Plate (for multiple Readouts)
        """
        #import pdb; pdb.set_trace()
        #if subset:
        #    subset = ast.literal_eval(subset)

        if type == 'run_wise':
            # Return plates across a run.
            if tag != '':
                if not subset:
                    return {index:plate.get_readout(tag) for index, plate in self.plates.items()}
                else:
                    return {index:plate.get_readout(tag) for index, plate in self.plates.items() if index in subset}
            else:
                result = {}
                for tag in list(self.plates.values)[0].read_outs.keys():
                    if not subset:
                        result[tag] =  {index:plate.get_readout(tag) for index, plate in self.plates.items()}
                    else:
                        result[tag] = {index:plate.get_readout(tag) for index, plate in self.plates.items() if index in subset}
                return result
        elif type == 'plate_wise':
            # Return plates across a plate.
            if tag != '':
                if not subset:
                    return self.plates[tag].read_outs
                else:
                    return {i:readout for i,readout in self.plates[tag].read_outs.items() if i in subset}
            else:
                result = {}
                for tag in self.plates.keys():
                    if not subset:
                        result[tag] =  self.plates[tag].read_outs
                    else:
                        result[tag] =  {i:readout for i,readout in self.plates[tag].read_outs.items() if i in subset}
                return result
        else:
            raise Exception("The type: {} is not implemented in "
                            "Run.filter()".format(type))


    def preprocess(self):
        """ Perform data preprocessing.

        Perform data preprocessing.

        """
        if hasattr(self.protocol(), 'preprocessing'):
            for i_method_name, kwargs in self.protocol().preprocessing.items():
                for i_plate in self.plates.values():
                    i_plate.preprocess(i_method_name, **kwargs)
        else:
            LOG.info("preprocessing is not defined in protocol: {}".format(self.protocol().name))


    def get_qc_config(self):
        """
            Extract qc info from protocol and run.
        """

        if hasattr(self.protocol(), "qc"):
            protocol_qc = self.protocol().qc
        else:
            protocol_qc = {}
        if "qc" in self.meta_data:
            run_qc = self.meta_data["qc"]
        else:
            run_qc = {}

        if len(set(protocol_qc.keys()).intersection(run_qc.keys())) != 0:
            LOG.warning("Some QC keys were defined both in the protocol config"
                "[{}] and the run config [{}]".format(str(protocol_qc.keys()),
                                                      str(run_qc.keys())))

        # This will work Python 3.5 onwards: return {**protocol_qc, **run_qc}
        return dict(protocol_qc, **run_qc) # This only works if keys are strings.


    def get_run_meta_data(self):
        """
            Extract relevant meta data for qc and analysis reports.
            Returns list of tuples: [(key_str, value_str)]
        """


        # You could try to flatten the dict automagically to increase elegance:
        # http://stackoverflow.com/questions/6027558/flatten-nested-python-dictionaries-compressing-keys
        meta_data_order = ["protocol_name", "protocol_config", "experimenter", "experimenter_mail", "run_config"]
        meta_data = {}
        for i, j in self.meta_data.items():
            if i in ["qc"]:
                continue
            elif type(j) == configobj.Section:
                for k, l in j.items():
                    meta_data["_".join([i,k])] = l
            else:
                meta_data[i] = j
        meta_data["protocol_name"] = self.protocol().name
        meta_data["protocol_config"] = self.protocol().path
        meta_data["run_config"] = self.path
        meta_data = {i: str(j) if type(j) != list else ", ".join([str(k) for k in j]) for i,j in meta_data.items()}

        meta_data_ordered = [(i_o,meta_data[i_o]) for i_o in meta_data_order]
        meta_data_ordered += [(i_m, str(i_v)) for i_m, i_v in meta_data.items() if i_m not in meta_data_order]

        return meta_data_ordered


    def qc(self):
        """ Perform quality control and save the results

        Perform quality control and save the results

        Args:

        .. todo:: Create QC for different plate subsets (e.g. raw/net).
        .. todo:: Use function to get to plate data instead of attributes?
        """

        if hasattr(self, '_qc'):
            return self._qc
        else:
            type = self.protocol().qc.pop("type", None)
            if type == 'knitr':
                qc_method = qc_knitr
            elif type == "matplotlib":
                qc_method = qc_matplotlib
            else:
                raise ValueError("The qc_type {} is currently not implemented.".format(type))

            # For all analysis needing data, add data... e.g.: the qc should write down the needed data for R automagically...
            qc_results = qc_method.report_qc(run=self, meta_data=self.get_run_meta_data(), **self.get_qc_config())
            self._qc = qc_results

        if "send_mail_upon_qc" in self.meta_data and self.meta_data["send_mail_upon_qc"].lower() == "true":
            send_mail(email_to = [self.meta_data['experimenter_mail']], body = "QC report for Run config '{}' is prepared.".format(self.path))
        return self._qc


    def analysis(self):
        """ Perform analysis and save the results

        Perform analysis and save the results

        Args:

        """

        if hasattr(self, '_analysis'):
            return self._analysis
        else:
            self._analysis = {}
            for i_ana, protocol_analysis_param in self.protocol().analysis.items():
                LOG.info(i_ana)
                LOG.info(protocol_analysis_param)
                subset = self.filter(**protocol_analysis_param['filter'])
                #import pdb; pdb.set_trace()
                if protocol_analysis_param['filter']['tag'] == '':
                    analysis_results = {i: analysis.perform_analysis(methods=protocol_analysis_param['methods'], data=j, plate_layout=self.plate_layout(), **self.meta_data['meta']) for i,j in subset.items()}
                else:
                    analysis_results = analysis.perform_analysis(methods=protocol_analysis_param['methods'], data=subset, plate_layout=self.plate_layout(), **self.meta_data['meta'])
                self._analysis[i_ana] = analysis_results

        return self._analysis


    def plate_layout(self):
        """ Return a plate_layout instance.

        Return a plate_layout instance.

        """

        plate_layouts = [plate.plate_layout for plate in self.plates.values()]
        if len(set(plate_layouts)) != 1:
            LOG.warning("The plates may have different plate layouts")
        return plate_layouts[0]


    def protocol(self, path = None, format = None):
        """ Read protocol and attach to `Run` instance.

        Read protocol and attach to `Run` instance.

        Args:
            path (str): Path to input file
            format (str):  At current only "csv"

        .. todo:: Write checks if path and format exists when necessary.
        """

        if not hasattr(self, '_protocol'):
            if path and format:
                self._protocol = protocol.Protocol.create(path, format)
            else:
                return None
        return self._protocol


    def write(self, format, path=None, return_string=None, *args):
        """ Serialize and write ``Run`` instances.

        Serialize ``Run`` instance using the stated ``format``.

        Args:
            format (str):  The output format: Currently only "pickle".
            path (str): Path to output file

        .. todo:: Write checks for ``format`` and ``path``.
        """

        if format == 'pickle':
            with open(path, 'wb') as fh:
                pickle.dump(self, fh)
        elif format == 'csv':
            output = run_io.serialize_run_for_r(self)
        else:
            raise Exception('Format is unknown: {}'.format(format))

        if path:
            with open(path, 'w') as fh:
                fh.write(output)
        if return_string:
            return output

def send_mail(body,
                email_to,
                email_from = "adriano_conrad_aguzzi@gmail.com",
                smtp_server = "smtp.gmail.com",
                smtp_port = 587,
                smtp_username = "elkewschaper@gmail.com",
                email_subject = "QC_report finished"):

    LOG.info("Sending email to {}".format(email_to))

    from email.mime.text import MIMEText
    from datetime import date
    import smtplib

    smtp_password = input('Enter password for {}:  '.format(smtp_username))
    #email_from = smtp_username

    DATE_FORMAT = "%d/%m/%Y"
    EMAIL_SPACE = ", "

    msg = MIMEText(body)
    msg['Content-Type'] = 'text/html; charset=UTF8'
    msg['Subject'] = email_subject + " %s" % (date.today().strftime(DATE_FORMAT))
    msg['From'] = email_from
    msg['To'] = EMAIL_SPACE.join(email_to)
    mail = smtplib.SMTP(smtp_server, smtp_port)
    mail.starttls()
    mail.login(smtp_username, smtp_password)
    mail.sendmail(email_from, email_to, msg.as_string())
    mail.quit()

