'''nclint: A simple script which checks NetCDF files for problems

Outputs the name of any file that fails any check.
'''

import sys
import argparse

import numpy
import netCDF4

check_list = []
def is_a_check(fun):
    check_list.append(fun.__name__)
    return fun


@is_a_check
def layer_one_missing(nc):
    '''Checks an open NetCDF file for a missing layer at t=1

    Last year we did a round of processing large climate rasters and
    computing multidecadal means (e.g. a temporal mean across a 30
    year period). Unfortunately, we did this for a large number of
    climate data sets where a multidecadal mean makes no
    sense. Examples include CLIMDEX timeseries where the files are
    already some temporal summary.

    The manifestation of this was that the error files have 13 time
    steps where the 1st appears to contain data, but all subsequent
    time steps do not. They can be easily identified by opening the
    file and testing whether the layer at t=1 is all NA/missing.
    '''

    for varname, var_ in nc.variables.items():
        # Only check grid variables
        if len(var_.dimensions) < 3:
            continue
        one_layer = var_[1,:,:]
        if isinstance(one_layer, numpy.ma.MaskedArray) and one_layer.mask.all():
            return True
    return False


@is_a_check
def vars_missing_units(nc):
    '''Returns True if any variable is not attributed with units'''
    for var_ in nc.variables.values():
        if not hasattr(var_, 'units'):
            return True
    return False


@is_a_check
def missing_time_units(nc):
    '''Returns True if the time variable is missing units attribute'''
    if 'time' in nc.variables:
        return not hasattr(nc.variables['time'], 'units')
    else:
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', metavar='FILE', type=str, nargs='*',
            help='File to check for missing layer')
    parser.add_argument('-c', '--checks', default='layer_one_missing',
            help='Comma separated list of check names to be performed')
    parser.add_argument('-l', '--list_checks', action='store_true',
            help='List the names of all available checks and exit',
            default=False)

    args = parser.parse_args()

    if args.list_checks:
        print("Available checks:", ','.join(check_list))

    checks = []
    for check in args.checks.split(','):
        if check not in check_list:
            print("NetCDF check '{}' does not exist".format(check), file=sys.stderr)
            sys.exit(1)
        checks.append(globals()[check])

    for file_ in args.files:
        nc = netCDF4.Dataset(file_, 'r')
        for check in checks:
            if check(nc):
                print(file_)
                break
