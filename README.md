This tool allow you to use a custom skeletal mesh with wind data setup for unreal 5.7's nanite skeletal foliage. No need to use the build-in PCG Vegetation.

The Nanite Skeletal Foliage need an asset user data called Dynamic Wind Skeletal Data for setting up the bones for wind.
This tool can use the xml exported from Speed Tree, auto phrasing the bone hireachy and import to unreal as Dynamic Wind Skeletal Data.

Asset preparation in Speed Tree.
You should name your node with the wind level like Branch_Large_L1_Wind, Branch_Small_V1_L2_Wind, Branch_Small_V2_L2_Wind before you export.
Export the speed tree as .xml format. In Grouping, it should be Hierarchy, and set hierarchy level to the highest level that need have wind.

Run the script set_up_wind_hierarchy.py and you will get a json file to import into unreal as Dynamic Wind Skeletal Data.

Run the import_wind_data.py in unreal and choose the json file to import to the skeletal mesh.


You can create your own tool to generate the json file. Just follow this format

{
  "Joints": [
    { "JointName": "Root",        "SimulationGroupIndex": 0 },
    { "JointName": "Bone_1_Start",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_1_End",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_2_Start",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_2_End",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_3_Start",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_3_End",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_4_Start",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_4_End",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_5_Start",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_5_End",   "SimulationGroupIndex": 0 },
    { "JointName": "Bone_7_Start",   "SimulationGroupIndex": 1 },
    { "JointName": "Bone_7_End",   "SimulationGroupIndex": 1 },
    { "JointName": "Bone_8_Start",   "SimulationGroupIndex": 2 },
    { "JointName": "Bone_8_End",   "SimulationGroupIndex": 2 },
    { "JointName": "Bone_9_Start",     "SimulationGroupIndex":1 },
    { "JointName": "Bone_9_End",     "SimulationGroupIndex": 1 },
    { "JointName": "Bone_10_Start",     "SimulationGroupIndex": 2 },
    { "JointName": "Bone_10_End",     "SimulationGroupIndex": 2 }
  ],
  "SimulationGroups": [
    {
      "bUseDualInfluence": false,
      "Influence": 1.0,
      "bIsTrunkGroup": true
    },
    {
      "bUseDualInfluence": true,
      "MinInfluence": 0.25,
      "MaxInfluence": 0.6,
      "ShiftTop": 0.2,
      "bIsTrunkGroup": false
    },
    {
      "bUseDualInfluence": true,
      "MinInfluence": 0.6,
      "MaxInfluence": 1.0,
      "ShiftTop": 0.0,
      "bIsTrunkGroup": false
    }
  ],
  "bIsGroundCover": false,
  "GustAttenuation": 0.25
}

