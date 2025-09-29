import unreal

selected_asset_data = unreal.EditorUtilityLibrary.get_selected_asset_data()[0]
skeletal_mesh_obj = unreal.EditorAssetLibrary.load_asset(selected_asset_data.package_name)


unreal.DynamicWindBlueprintLibrary.import_dynamic_wind_skeletal_data_from_file(
    skeletal_mesh_obj
)