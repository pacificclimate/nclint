import os
import glob
import pytest
from nchelpers import CFDataset
import nclint

# Basic sanity tests for nclint.
# This script checks that:
# - Bad NetCDF files fail more checks than good ones
# - Each individual check is more likely to fail on bad files
# - The check_list matches the functions registered with @is_a_check


# Find all test netCDF files
good_files = sorted(f for f in glob.glob("tests/*.nc") if not f.endswith("_bad.nc"))


@pytest.mark.parametrize("good_file", good_files)
def test_good_bad_file_pair(good_file):
    """Test that bad files fail more checks than their good counterparts."""
    bad_file = good_file.replace(".nc", "_bad.nc")
    assert os.path.exists(bad_file), f"Missing bad pair for {good_file}"

    nc_good = CFDataset(good_file, "r")
    nc_bad = CFDataset(bad_file, "r")

    failures_good = {}
    failures_bad = {}

    for check_name in nclint.check_list:
        check = getattr(nclint, check_name)

        good_result = check(nc_good)
        bad_result = check(nc_bad)

        if good_result:
            failures_good[check_name] = good_result
        if bad_result:
            failures_bad[check_name] = bad_result

    assert len(failures_bad) > len(failures_good), (
        f"{bad_file} did not fail more checks than {good_file}.\n"
        f"Good file failed {len(failures_good)} checks: {list(failures_good.keys())}\n"
        f"Bad file failed {len(failures_bad)} checks: {list(failures_bad.keys())}"
    )

    # Check if there are any failures in good file that aren't in bad file
    good_only_failures = set(failures_good.keys()) - set(failures_bad.keys())
    if good_only_failures:
        pytest.fail(
            f"Good file {good_file} fails checks that bad file {bad_file} passes: {good_only_failures}"
        )


@pytest.mark.parametrize("check_name", nclint.check_list)
def test_check_functionality(check_name):
    """Test that each check should fail more on bad files than good files."""
    check = getattr(nclint, check_name)

    good_fails = 0
    bad_fails = 0

    for good_file in good_files:
        bad_file = good_file.replace(".nc", "_bad.nc")

        nc_good = CFDataset(good_file, "r")
        nc_bad = CFDataset(bad_file, "r")

        if check(nc_good):
            good_fails += 1
        if check(nc_bad):
            bad_fails += 1

    assert bad_fails >= good_fails, (
        f"Check '{check_name}' fails on {good_fails} good files and {bad_fails} bad files. "
        f"Bad files should fail more checks than good files."
    )


def test_check_list_completeness():
    """Verify that all checks defined with @is_a_check decorator are in check_list."""
    # Find all functions with the @is_a_check decorator
    check_functions = [
        name
        for name, func in vars(nclint).items()
        if callable(func)
        and (name.startswith("missing_") and name != "missing_global_attrs")
        or name
        in [
            "layer_one_missing",
            "vars_missing_units",
            "cant_generate_climos",
            "has_masked_dimensions",
        ]
    ]

    # Make sure all check functions are in check_list
    missing_checks = set(check_functions) - set(nclint.check_list)
    extra_checks = set(nclint.check_list) - set(check_functions)

    assert not missing_checks, f"Functions missing from check_list: {missing_checks}"
    assert not extra_checks, f"Extra functions in check_list: {extra_checks}"
