#!python
'''nclint: A simple script which checks NetCDF files for problems

Outputs the name of any file that fails any check.
'''

import sys
import argparse

import numpy

import nchelpers

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
    '''Returns a list of all global attributes in array `attrs` that are missing from NetCDF file `nc`'''
    return [attr for attr in attrs if not hasattr(nc, attr)]


@is_a_check
def missing_cmip5_global_attrs(nc):
    """Checks if any required CMIP5 output global attribute is missing.
    Reference: http://cmip-pcmdi.llnl.gov/cmip5/docs/CMIP5_output_metadata_requirements_22May14.pdf
    """
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
    """Checks if any CF Metadata Convention global attribute is missing.
    Reference: http://cfconventions.org/cf-conventions/v1.6.0/cf-conventions.html#description-of-file-contents
    """
    return missing_global_attrs(nc, '''
        title
        institution
        source
        history
        references
        comment
    '''.split())


# Mandatory and optional summary global attributes describing GCM output that the PCIC metdata standard uses when
# referencing such data in an downstream output file (e.g., as input to downscaling or forcing to a model).
# In use, these attributes always bear a prefix that indicates what they are describing (e.g., 'driving_' for
# input to downscaling).

summary_gcm_mandatory_global_attrs = '''
    experiment
    experiment_id
    initialization_method
    institute_id
    institution
    model_id
    physics_version
    realization
'''.split()

summary_gcm_optional_global_attrs = '''
    forcing
    frequency
    tracking_id
'''.split()


# Mandatory and optional attributes describing a gridded observational dataset that the PCIC metdata standard uses when
# referencing such data in a downstream output file (e.g., used for calibration of downscaling or forcing to a model).
# In use, these attributes always bear a prefix that indicates what they are describing (e.g., 'target_' for
# calibration of downscaling).

gridded_dataset_mandatory_global_attrs = '''
    contact
    dataset
    dataset_id
    institute_id
    institution
    references
    version
'''.split()

gridded_dataset_optional_global_attrs = '''
    frequency
'''.split()


# Downscaling-specific mandatory and optional global attributes.
# Note: additional attributes are required to fully describe a downscaling output file.

downscaling_specific_mandatory_global_attrs = \
    ['driving_' + attr for attr in summary_gcm_mandatory_global_attrs] + \
    ['target_' + attr for attr in gridded_dataset_mandatory_global_attrs] + \
    '''
        downscaling_method
        downscaling_method_id
        downscaling_package_id
    '''.split()

downscaling_specific_optional_global_attrs = \
    ['driving_' + attr for attr in summary_gcm_optional_global_attrs] + \
    ['target_' + attr for attr in gridded_dataset_optional_global_attrs]



# Model forcing by observational data mandatory and optional attributes

model_forcing_observational_mandatory_global_attrs = \
    ['forcing_obs_' + attr for attr in gridded_dataset_mandatory_global_attrs]
model_forcing_observational_optional_global_attrs = \
    ['forcing_obs_' + attr for attr in gridded_dataset_optional_global_attrs]


# Model forcing by downscaled GCM data mandatory and optional attributes

model_forcing_downscaled_gcm_mandatory_global_attrs = \
    ['forcing_' + attr for attr in downscaling_specific_mandatory_global_attrs]
model_forcing_downscaled_gcm_optional_global_attrs = \
    ['forcing_' + attr for attr in downscaling_specific_optional_global_attrs]


# Model calibration (by gridded dataset) mandatory and optional attributes

model_calibration_mandatory_global_attrs = ['calibration_' + attr for attr in gridded_dataset_mandatory_global_attrs]
model_calibration_optional_global_attrs = ['calibration_' + attr for attr in gridded_dataset_optional_global_attrs]


# Hydromodel-specific mandatory and optional attributes
# Note: additional attributes are required to fully describe a hydromodel output file.

hydromodel_specific_mandatory_global_attrs = '''
    domain
    hydromodel_method
    hydromodel_method_id
    hydromodel_version
    hydromodel_resolution
    hydromodel_type
'''.split()

hydromodel_specific_optional_global_attrs = '''
    hydromodel_settings
'''.split()


@is_a_check
def missing_pcic_common_mandatory_global_attrs(nc):
    """Checks if any mandatory global attribute common to all PCIC data files is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table A.
    """
    return missing_global_attrs(nc, '''
        contact
        Conventions
        creation_date
        frequency
        institute_id
        institution
        modeling_realm
        product
        project_id
        table_id
        title
    '''.split())


@is_a_check
def missing_downscaling_specific_mandatory_global_attrs(nc):
    """Checks if any mandatory global metadata attribute describing downscaling is missing.
    This check only checks for downscaling-specific attributes; additional attributes are required to fully describe
    a downscaling output file.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table B
    """
    return missing_global_attrs(nc, downscaling_specific_mandatory_global_attrs)


@is_a_check
def missing_downscaling_mandatory_global_attrs(nc):
    """Checks if any mandatory global metadata attribute for downscaled model products is missing.
    This checks the complete set of mandatory global attributes for a downscaled output file.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Tables A & B
    """
    return missing_pcic_common_mandatory_global_attrs(nc) + missing_downscaling_specific_mandatory_global_attrs(nc)


@is_a_check
def missing_downscaling_optional_global_attrs(nc):
    """Checks if any optional global metadata attribute for a downscaled output file is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Tables A & B
    """
    return missing_global_attrs(
        nc, 
        downscaling_specific_optional_global_attrs +
        '''
            domain
            tracking_id
        '''.split()
    )


@is_a_check
def missing_downscaling_any_global_attrs(nc):
    """Checks if any mandatory OR optional global metadata attribute for downscaled model products is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Tables A & B
    """
    return missing_downscaling_mandatory_global_attrs(nc) + missing_downscaling_optional_global_attrs(nc)


@is_a_check
def missing_model_forcing_general_mandatory_attrs(nc):
    """Checks if any mandatory global metadata attribute describing general model forcing is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table C1
    """
    return missing_global_attrs(nc, '''
        forcing_type
    '''.split())


@is_a_check
def missing_model_forcing_general_optional_attrs(nc):
    """Checks if any optional global metadata attribute describing general model forcing is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table C1
    """
    return missing_global_attrs(nc, '''
        forcing_domain
    '''.split())


@is_a_check
def missing_model_forcing_observational_mandatory_attrs(nc):
    """Checks if any mandatory global metadata attribute describing model forcing by observational data is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table C2
    """
    return missing_global_attrs(nc, model_forcing_observational_mandatory_global_attrs)



@is_a_check
def missing_model_forcing_observational_optional_attrs(nc):
    """Checks if any optional global metadata attribute describing model forcing by observational data is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table C2
    """
    return missing_global_attrs(nc, model_forcing_observational_optional_global_attrs)



@is_a_check
def missing_model_forcing_downscaled_gcm_mandatory_attrs(nc):
    """Checks if any mandatory global metadata attribute describing model forcing by downscaled gcm data is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table C3
    """
    return missing_global_attrs(nc, model_forcing_downscaled_gcm_mandatory_global_attrs)



@is_a_check
def missing_model_forcing_downscaled_gcm_optional_attrs(nc):
    """Checks if any optional global metadata attribute describing model forcing by downscaled gcm data is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table C3
    """
    return missing_global_attrs(nc, model_forcing_downscaled_gcm_optional_global_attrs)



@is_a_check
def missing_calibration_mandatory_attrs(nc):
    """Checks if any mandatory global metadata attribute describing model calibration dataset is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table D
    """
    return missing_global_attrs(nc, model_calibration_mandatory_global_attrs)



@is_a_check
def missing_model_calibration_optional_attrs(nc):
    """Checks if any optional global metadata attribute describing model calibration dataset is missing.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table D
    """
    return missing_global_attrs(nc, model_calibration_optional_global_attrs)


@is_a_check
def missing_hydromodel_specific_mandatory_global_attrs(nc):
    """Checks if any mandatory global metadata attribute specific to hydrological models is missing.
    This check only checks for hydromodel-specific attributes; additional attributes are required to fully describe
    a hydromodel output file.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table E
    """
    return missing_global_attrs(nc, hydromodel_specific_mandatory_global_attrs)


@is_a_check
def missing_hydromodel_specific_optional_global_attrs(nc):
    """Checks if any optional global metadata attribute specific to hydrological models is missing.
    This check only checks for hydromodel-specific attributes; additional attributes are required to fully describe
    a hydromodel output file.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Table E
    """
    return missing_global_attrs(nc, hydromodel_specific_optional_global_attrs)


@is_a_check
def missing_hydromodel_obs_mandatory_global_attrs(nc):
    """Checks if any mandatory global metadata attribute for hydrological modelling output products is missing.
    This check is the full deal -- all attributes needed for an output file from a hydromodel forced by observations.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Tables A, C1, C2, D, E
    """
    return missing_pcic_common_mandatory_global_attrs(nc) + \
           missing_model_forcing_general_mandatory_attrs(nc) + \
           missing_model_forcing_observational_mandatory_attrs(nc) + \
           missing_calibration_mandatory_attrs(nc) + \
           missing_hydromodel_specific_mandatory_global_attrs(nc)


@is_a_check
def missing_hydromodel_gcm_mandatory_global_attrs(nc):
    """Checks if any mandatory global metadata attribute for hydrological modelling output products is missing.
    This check is the full deal -- all attributes needed for an output file from a hydromodel forced by observations.
    Reference: https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data
    Tables A, C1, C3, D, E
    """
    return missing_pcic_common_mandatory_global_attrs(nc) + \
           missing_model_forcing_general_mandatory_attrs(nc) + \
           missing_model_forcing_downscaled_gcm_mandatory_attrs(nc) + \
           missing_calibration_mandatory_attrs(nc) + \
           missing_hydromodel_specific_mandatory_global_attrs(nc)


@is_a_check
def cant_generate_climos(nc):
    """Checks to see if the generate_climos script will fail (raise an
    exception) due to metadata when run.

    Tests whether the nchelpers properties that generate_climos
    needs are undefined or raise an exception.
    """
    for name in '''
        time_var
        cmor_filename
    '''.split():
        try:
            test = getattr(nc, name)
            if not test:
                return name, 'Falsy value: {}'.format(test)
        except Exception as e:
            return name, str(e)
    return False


@is_a_check
def has_masked_dimensions(nc):
    """Checks for any dimension variables that have masked values.

    Returns a list containing the names of each such dimension variable.

    A masked dimension is not logically natural, and it can cause trouble
    when processing the file. Specifically, a masked time variable causes
    ``generate_climos`` (entirely reasonably) to omit any masked time period
    and/or to not be able to determine the time resolution of the file.
    """
    return [
        dim for dim in nc.dimensions
        if isinstance(nc.variables[dim][:], numpy.ma.core.MaskedArray)
    ]



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', metavar='FILE', type=str, nargs='*',
            help='File to check for missing layer')
    parser.add_argument('-c', '--checks', default='layer_one_missing',
            help='Comma separated list of check names to be performed')
    parser.add_argument('-l', '--list_checks', action='store_true',
            help='List the names of all available checks and exit',
            default=False)
    parser.add_argument('-v', '--verbose', action='store_true',
            help='Provide more detail about available checks and check failures',
            default=False)

    args = parser.parse_args()

    if args.list_checks:
        if args.verbose:
            for check_name in check_list:
                check = globals()[check_name]
                print('{}:\n{}\n'.format(check_name, check.__doc__))
        else:
            print("Available checks:", ','.join(check_list))
        sys.exit(0)

    checks = []
    for check in args.checks.split(','):
        if check not in check_list:
            print("NetCDF check '{}' does not exist".format(check), file=sys.stderr)
            sys.exit(1)
        checks.append(globals()[check])

    exit_status = 0
    for file_ in args.files:
        nc = nchelpers.CFDataset(file_, 'r')
        for check in checks:
            result = check(nc)
            if result:
                exit_status = 1
                if args.verbose:
                    print('{} FAILED {}: {}'.format(file_, check.__name__, result))
                else:
                    print(file_)
                    # In non-verbose mode, we only care whether a file is
                    # good/bad. If it fails, skip the rest of the checks
                    break

    sys.exit(exit_status)