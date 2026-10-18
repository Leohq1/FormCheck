def test_person3_packages_are_importable() -> None:
    import formcheck_analysis
    import formcheck_biomechanics
    import formcheck_pose
    import formcheck_rules
    import formcheck_video

    assert all(
        package.__version__ == "0.1.0"
        for package in (
            formcheck_analysis,
            formcheck_biomechanics,
            formcheck_pose,
            formcheck_rules,
            formcheck_video,
        )
    )
