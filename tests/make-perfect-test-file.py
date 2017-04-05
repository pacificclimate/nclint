import argparse

import netCDF4


# Define these the hard way to avoid just duplicating the computations in nclint.

pcic_common_mandatory_global_attrs = '''
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
'''.split()

downscaling_specific_mandatory_global_attrs = '''
    downscaling_method
    downscaling_method_id
    downscaling_package_id
    driving_experiment
    driving_experiment_id
    driving_initialization_method
    driving_institute_id
    driving_institution
    driving_model_id
    driving_physics_version
    driving_realization
    driving_tracking_id
    target_contact
    target_dataset
    target_dataset_id
    target_institute_id
    target_institution
    target_references
    target_version
'''.split()

model_forcing_general_mandatory_attrs = '''
    forcing_type
'''.split()

model_forcing_observational_mandatory_global_attrs = '''
    forcing_obs_contact
    forcing_obs_dataset
    forcing_obs_dataset_id
    forcing_obs_institute_id
    forcing_obs_institution
    forcing_obs_references
    forcing_obs_version
'''.split()

model_forcing_downscaled_gcm_mandatory_global_attrs = '''
    forcing_downscaling_method
    forcing_downscaling_method_id
    forcing_downscaling_package_id
    forcing_driving_experiment
    forcing_driving_experiment_id
    forcing_driving_initialization_method
    forcing_driving_institute_id
    forcing_driving_institution
    forcing_driving_model_id
    forcing_driving_physics_version
    forcing_driving_realization
    forcing_driving_tracking_id
    forcing_target_contact
    forcing_target_dataset
    forcing_target_dataset_id
    forcing_target_institute_id
    forcing_target_institution
    forcing_target_references
    forcing_target_version
'''.split()

calibration_mandatory_global_attrs = '''
    calibration_contact
    calibration_dataset
    calibration_dataset_id
    calibration_institute_id
    calibration_institution
    calibration_references
    calibration_version
'''.split()

hydromodel_specific_mandatory_global_attrs = '''
    domain
    hydromodel_method
    hydromodel_method_id
    hydromodel_version
    hydromodel_resolution
    hydromodel_type
'''.split()


attrs_by_filetype = {
    'downscaled': pcic_common_mandatory_global_attrs +
                  downscaling_specific_mandatory_global_attrs,
    'hydromodel_gcm': pcic_common_mandatory_global_attrs +
                       model_forcing_general_mandatory_attrs +
                       model_forcing_downscaled_gcm_mandatory_global_attrs +
                       calibration_mandatory_global_attrs +
                       hydromodel_specific_mandatory_global_attrs,
    'hydromodel_obs': pcic_common_mandatory_global_attrs +
                       model_forcing_general_mandatory_attrs +
                       model_forcing_observational_mandatory_global_attrs +
                       calibration_mandatory_global_attrs +
                       hydromodel_specific_mandatory_global_attrs,
}


def assign_attrs(nc, attrs, value='value'):
    for attr in attrs:
        setattr(nc, attr, value)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str, help='Output file name')
    parser.add_argument('-t', '--type', required=True, help='Output file type',
                        choices=attrs_by_filetype.keys())
    args = parser.parse_args()

    with netCDF4.Dataset(args.file, mode='w') as nc:
        attrs =  attrs_by_filetype[args.type]
        assign_attrs(nc, attrs)

