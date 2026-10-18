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


def test_analysis_environment_has_one_cv2_provider() -> None:
    from importlib.metadata import distributions

    providers = sorted(
        distribution.metadata["Name"].lower().replace("_", "-")
        for distribution in distributions()
        if any(str(path).startswith("cv2/") for path in distribution.files or ())
    )

    assert providers == ["opencv-python-headless"]
