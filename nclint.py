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


def missing_global_attrs(nc, attrs):
    '''Returns True if any global attribute named in array attrs is missing from NetCDF file nc'''
    return not all(hasattr(nc, attr) for attr in attrs)


@is_a_check
def missing_cmip5_global_attrs(nc):
    '''Returns True if any required CMIP5 output global attribute is missing.
    Reference: http://cmip-pcmdi.llnl.gov/cmip5/docs/CMIP5_output_metadata_requirements_22May14.pdf
    '''
    return missing_global_attrs(nc, '''
        branch_time
        contact
        Conventions
        creation_date
        experiment
        experiment_id
        forcing
        frequency
        initialization_method
        institute_id
        institution
        model_id
        modeling_realm
        parent_experiment_id
        parent_experiment_rip
        physics_version
        product
        project_id
        realization
        source
        table_id
        tracking_id
    '''.split())


@is_a_check
def missing_cf_global_attrs(nc):
    '''Returns True if any CF Metadata Convention global attribute is missing.
    Reference: http://cfconventions.org/cf-conventions/v1.6.0/cf-conventions.html#description-of-file-contents
    '''
    return missing_global_attrs(nc, '''
        title
        institution
        source
        history
        references
        comment
    '''.split())


@is_a_check
def missing_downscaling_global_attrs(nc):
    '''Returns True if any required global metadata attribute for downscaled model products is missing.
    Reference: https://redmine.pacificclimate.org/projects/downscaling/wiki

    '''
    return missing_global_attrs(nc, '''
        Conventions
        comment
        contact
        creation_date
        driving_experiment
        driving_experiment_name
        driving_institute_id
        driving_institution
        driving_model_ensemble_member
        driving_model_id
        frequency
        institute_id
        institution
        modeling_realm
        product
        realization
        references
        source
        target_contact
        target_dataset
        target_history
        target_id
        target_institute_id
        target_institution
        target_references
        target_version
        title
        version
    '''.split())


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
