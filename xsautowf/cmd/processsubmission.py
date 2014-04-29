"""Python script for processing a submission"""

from jira.client import JIRA
import re
from xsjira.models import Task, HCLSubmission, GenericSubmission
from sfftp.client import SFFTPClient
from argparse import ArgumentParser

SERVER_URL = 'https://tracker.vmd.citrix.com'

JIRA = JIRA(options={'server': SERVER_URL},
            )


class RemoteCopyToCRD(object):  # pylint: disable=R0903
    """Create remote copy in Project CRD of given ticket for
       update marketplace.
    """
    #  TODO
    crd_user = 'sagnikd'
    crd_pjt_key = 'HCL'

    def __init__(self):
        self.crd_ticket = None

    def do_remote_copy(self, master_ticket):
        """Perform the remote copy"""
        (filepath, filename) = get_doc_attachment(master_ticket)
        reporter = master_ticket.get_reporter()
        master_ticket.create_issue({'project': {'key': self.crd_pjt_key},
                                    'summary': 'CLONE Of %s' %
                                    master_ticket.get_summary(),
                                    'issuetype': {'name': 'Task'},
                                    'description': 'Please add' +
                                    ' the device to marketplace', })

        self.crd_ticket = Task(JIRA, self.crd_pjt_key)
        self.crd_ticket.create_issue_link(master_ticket.key)
        self.crd_ticket.change_reporter(reporter)

        add_hcl_link_comment(master_ticket, self.crd_ticket)

        if filepath:
            self.crd_ticket.add_attachment(filepath, filename)
        self.crd_ticket.add_watcher(reporter)
        self.crd_ticket.add_comment(
            "Hi Gaurav,\nCould you please update this to market " +
            "place and attach the link.\nThanks,\nSagnik"
            )
        self.crd_ticket.assign_issue(self.crd_user)
        print "%s Created" % self.crd_ticket.key
        print self.crd_ticket.get_summary()
        return self.crd_ticket


def process_submission(options):
    """process submission function"""
    #  Dictionary which maps the Folder directory with the type
    tag_dict = {'server': 'Servers',
                'stor': 'Storage Arrays',
                'nic': 'NICs',
                'hba': 'HBAs and CNAs',
                'cna': 'HBAs and CNAs',
                'gpu': 'GPUs',
                'dd': 'Driver Disks',
                'test': 'Test'}
    version_list = [
        'Other',
        'XenServer 5.0',
        'XenServer 5.5',
        'XenServer 5.6',
        'XenServer 5.6.x',
        'XenServer 6.0.x',
        'XenServer 6.1.0',
        'XenServer 6.2.0'
        ]

    key = options.subtype
    if key is not 'dd':
        ticket = HCLSubmission(JIRA, options.ticket)
    else:
        ticket = GenericSubmission(JIRA, options.ticket)

    print ticket.get_summary()

    # If copy flag is set, move a copy to the project CRD
    if options.crddup:
        instance = RemoteCopyToCRD()
        ticket2 = instance.do_remote_copy(ticket)
        print "## Remote Copy to CRD Done ##\n"

    #  For non HCL Submission, we need additional parameters as below
    self.version = options.version

    if not options.name and ticket.get_device_tested():
        product_name = ticket.get_device_tested()
    else:
        product_name = options.name
    #  To display the ack-submission if there is one:
    if ticket.get_type() == 'HCL Submission' and key in ['server', 'nic']:
        (ack_path, ack_filename) = ticket.get_ack_attachment()
        print "%s found.\nExtracting Product Info.." % ack_filename
        adict = ticket.get_ack_attachment_dict(ack_path)

        if not self.version:
            self.version = adict['xs_version']

        # if Device Tested is empty, take product name wfrom result dict
        if product_name is None:
            product_name = "%s %s" %
            (dict['system-manufacturer'].strip(), adict['product'].strip())

    print "\nDevice Tested: %s" % product_name

    # derive upload_path for FTP upload
    upload_path = "/XenServer HCL/Hardware Certification Logs"
    for ver in version_list:
        if re.search(self.version, ver):
            upload_path += "/%s" % ver
            break
    upload_path += "/%s" % tag_dict[key]
    upload_path += "/%s" % product_name
    zipfile = ticket.issue.key + ".zip"
    upload_path += "/%s" % zipfile

    # Path of zipfile that will be stored
    zippath = ticket.get_attachmentzip_path(ticket.issue.id)
    SFFTPClient().upload(zippath, upload_path)


def add_hcl_link_comment(master_ticket, crd_ticket):
    """Add a HCL link to the specified ticket"""
    for comment in master_ticket.list_comments():
        if re.search("http://", comment.body):
            crd_ticket.add_comment(comment.body)


def get_doc_attachment(master_ticket):
    """Get a doc from a ticket"""
    for afile in master_ticket.issue.fields.attachment:
        if re.search('doc', afile.filename):
            return (master_ticket.get_attachment_path(afile.id),
                    afile.filename)
    print("Error: Missing the Verification Form (doc) which is " +
          "needed to update Citrix Ready for market place.")
    return (None, None)


def main():
    """Entry point"""
    argParser = ArgumentParser()  # pylint: disable=C0103
    argParser.add_argument("-t", "--ticket", dest="ticket", required=True,
                           help="HCL-435,(server|stor|nic|hba|cna|gpu|dd)," +
                           " 6.2.0[Optional], Product_Name [Optional]")
    argParser.add_argument("-s", "--subtype", dest="subtype", required=True)
    argParser.add_argument("-v", "--version", dest="version", required=False)
    argParser.add_argument("-n", "--name", dest="name", required=False)
    argParser.add_argument("-c", "--crddup", dest="crddup", nargs='?',
                           type=str, const='True', required=False)
    cmdargs = argParser.parse_args()  # pylint: disable=C0103
    process_submission(cmdargs)
