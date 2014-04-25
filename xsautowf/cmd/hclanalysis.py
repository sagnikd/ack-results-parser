"""Python script to analyze HCL related telemetry"""

from xsautowf.cmd.processsubmission import JIRA, ArgumentParser
import datetime


def time_track(inputdate):
    """Prints Weekly Tickets Created and Resolved from the input day
       till Today"""
    resolve_str = ("type ='HCL Submission' and resolutiondate >=" +
                   " '%d/%d/%d' and resolutiondate<= '%d/%d/%d'")
    created_str = ("type ='HCL Submission' and createdDate >= '%d/%d/%d'" +
                   " and createdDate<= '%d/%d/%d'")
    inputdate = datetime.datetime(int(inputdate.split('-')[0]),
                                  int(inputdate.split('-')[1]),
                                  int(inputdate.split('-')[2]))
    today = datetime.datetime.today()

    date = inputdate
    while True:
        week_firstday = date - datetime.timedelta(date.weekday())
        week_endday = week_firstday + datetime.timedelta(7)

        nextweek_firstday = week_endday + datetime.timedelta(1)
        reslvd_tkts = JIRA.search_issues(resolve_str % (week_firstday.year,
                                                        week_firstday.month,
                                                        week_firstday.day,
                                                        week_endday.year,
                                                        week_endday.month,
                                                        week_endday.day))
        print "Resolved Tickets between %s to %s = %d" % (week_firstday,
                                                          week_endday,
                                                          len(reslvd_tkts))
        crtd_tkts = JIRA.search_issues(created_str % (week_firstday.year,
                                                      week_firstday.month,
                                                      week_firstday.day,
                                                      week_endday.year,
                                                      week_endday.month,
                                                      week_endday.day))
        print "Tickets raised between %s to %s = %d\n" % (week_firstday,
                                                          week_endday,
                                                          len(crtd_tkts))
        if (nextweek_firstday - today).days < 0:
            date = nextweek_firstday
        else:
            break


def main():
    """Entry Point"""
    dataParser = ArgumentParser()  # pylint: TODO
    dataParser.add_argument("-d", "--date", dest="date", required=False,
                            help="Enter Date format: YYYY-MM-DD")
    cmdargs = dataParser.parse_args()  # pylint: disable TODO
    time_track(cmdargs.date)
